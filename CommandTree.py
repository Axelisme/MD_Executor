import re
import subprocess as sp
from typing import Optional, List, Dict

class BaseCommandBlock:
    level_pat = "(?P<level>#%+)"
    oper_pat = "(?P<oper>[A-Z])"
    flag_pat = "(?P<flag>(?:[a-z]+,?)+)"
    cond_pat = "(?P<cond>{.*})"
    bash_start_pat = "(?P<bash_start>```bash=?)"
    bash_end_pat = "(?P<bash_end>```)"
    end_pat = "(?P<end>#@+)"
    head_pat = re.compile(
        f"^{bash_start_pat}?\s*{level_pat}{oper_pat}:?{flag_pat}?\s+{cond_pat}\s*{end_pat}?\s*$"
    )
    tail_pat = re.compile(f"^(?:{end_pat}|{bash_end_pat})\s*$")

    _register_block:Dict[str,"BaseCommandBlock"] = {}
    _args_flags = {}

    @classmethod
    def register_block(cls, oper:str):
        BaseCommandBlock._register_block[oper] = cls

    @staticmethod
    def register(operation:str):
        def decorator(class_):
            class_.register_block(operation)
            return class_
        return decorator

    @classmethod
    def set_args_flags(cls, flags):
        cls._args_flags.update(flags)

    @classmethod
    def _parse_head(cls, line:str) -> Optional[Dict[str,str|None]]:
        match = cls.head_pat.fullmatch(line)
        return match.groupdict() if match else None

    @classmethod
    def _parse_tail(cls, line:str) -> Optional[Dict[str,str|None]]:
        match = cls.tail_pat.fullmatch(line)
        return match.groupdict() if match else None

    @classmethod
    def get_block(cls, head:Dict[str,str|None], line_iter:iter) -> "BaseCommandBlock":
        BlockClass = cls._register_block.get(head["oper"])
        if BlockClass is None:
            raise ValueError(f"Unknown operation: {head['oper']}")

        block:BaseCommandBlock = BlockClass(head)
        block.parse_content(line_iter)

        return block

    @classmethod
    def as_block(cls, lines:List[str]) -> "BaseCommandBlock":
        presudo_head = {"level":"#","flag":"n","cond":"{}"}

        presudo_block = BaseCommandBlock(presudo_head)
        presudo_block.parse_content(enumerate(lines, start=1))

        return presudo_block

    def __init__(self, head:Dict[str,str|None]):
        self.bash_start = head.get("bash_start")

        self.level = len(head["level"]) - 1

        self.oper_flag = head["flag"]
        self.oper_flag = self.oper_flag.split(",") if self.oper_flag else []
        if not hasattr(self, "valid"):
            self.valid = ["n", "c", "d"]
        assert self.check_flag(), f"Invalid flag: {self.oper_flag}"

        self.condition = eval(head["cond"])
        assert isinstance(self.condition, dict), f"expect condition be a dict but get {self.condition}"

        self.end = head.get("end")
        if self.end:
            end_level = len(self.end) - 1
            if self.level != end_level:
                print(f"current level is mismatched with end level, {self.level} != {end_level}")
                raise ValueError("Invalid end")

        self.content = []

    def parse_content(self, line_iter:iter):
        if self.end:
            return None

        command_buffer = ""
        def pack_command():
            nonlocal command_buffer
            if command_buffer:
                self.content.append(command_buffer)
                command_buffer = ""

        for id, line in line_iter:
            if head := type(self)._parse_head(line):
                pack_command()
                block = type(self).get_block(head, line_iter)
                if self.level + 1 != block.level:
                    print(f"line {id}")
                    print(line)
                    print(
                        f"current level is mismatched with sub level, {self.level} + 1 != {block.level}"
                    )
                    raise ValueError("Invalid start")
                self.content.append(block)
            elif tail := self._parse_tail(line):
                if tail["bash_end"] and self.bash_start is None:
                    continue
                pack_command()
                if tail["end"]:
                    end_level = len(tail["end"]) - 1
                    if self.level != end_level:
                        print(f"line {id}")
                        print(line)
                        print(
                            f"start level is mismatched with end level, {self.level} != {end_level}"
                        )
                        raise ValueError("Invalid end")
                break
            else:
                command_buffer += line
        else:
            if self.level != 0:
                raise ValueError("Cannot find end of block")

    def _operate(self, setup:Dict[str,str|List[str]]) -> bool:
        return True

    def check_flag(self) -> bool:
        return all(flag in self.valid for flag in self.oper_flag)

    def user_confirm(self, question:Optional[str] = None, default:bool = True) -> bool:
        selection = "Y/n" if default else "y/N"

        if question is None:
            question = f"Do you want to run this block? [{selection}] "
        else:
            question += f" [{selection}] "

        while True:
            respond = input(question)
            if respond.lower() == "y":
                return True
            elif respond.lower() == "n":
                return False
            elif respond == "":
                return default
            else:
                question = "Invalid input, enter again [{selection}] "

    def _exec_command(self, commands:str, setup:Dict[str,str|List[str]]) -> None:
        if "n" in self.oper_flag:
            return
        formatted_command:str = commands if "d" in self.oper_flag else commands.format(**setup)
        if "c" in self.oper_flag:
            print("\n\n"+">"*50+"\nCommand to run:")
            print(formatted_command,end='')
            print("<"*50)
            if not self.user_confirm("Do you want to run this command?"):
                return

        if self._args_flags.get("dry_run"):
            print(formatted_command)
        else:
            sp.run(formatted_command,shell=True,check=True).check_returncode()

    def run(self, setup:Dict[str,str|List[str]]) -> None:
        if self._operate(setup):
            for content in self.content:
                if isinstance(content, BaseCommandBlock):
                    content.run(setup)
                else:
                    self._exec_command(content, setup)

@BaseCommandBlock.register("A")
class AddBlock(BaseCommandBlock):
    def __init__(self, head: Dict[str, str | None]):
        self.valid = ["m", "c", "s", "f", "d"]
        super().__init__(head)

    def _operate(self, data_dict:dict) -> bool:
        if "s" in self.oper_flag:
            data_dict.update(self.condition)
            return True

        for key, value in self.condition.items():
            if key in data_dict and "f" not in self.oper_flag:
                continue
            if isinstance(value, list):
                if "m" in self.oper_flag:
                    data_dict[key] = self.user_choose_many(key, value, data_dict)
                else:
                    data_dict[key] = self.user_choose_one(key, value, data_dict)
            elif isinstance(value, str):
                data_dict[key] = self.user_input(key, value, data_dict)
            else:
                raise ValueError(f"Unsupported type of condition value: {value}")

        return True

    def user_choose_one(self, key:str, value:List[str], data_dict:dict) -> str:
        choose_num = len(value)

        print(f"\n\nSelect one {key} you want, supported type are: ")
        print('-'*30)
        for i,name in enumerate(value):
            print(f"{i}) {name}")
        print('-'*30)

        user_respond:str = input(f"From 0 to {choose_num-1}, default is 0: ")
        if not user_respond:
            user_respond = '0'
        while not user_respond.isdigit() or int(user_respond) not in range(0,choose_num):
            user_respond = input("Invalid input, please enter again: ")
            if not user_respond:
                user_respond = '0'

        return value[int(user_respond)]

    def user_choose_many(self, key:str, value:List[str], data_dict:dict) -> List[str]:
        choose_num = len(value)

        print(f"\n\nSelect what {key} you want, supported type are: ")
        print('-'*30)
        for i,name in enumerate(value):
            print(f"{i}) {name}")
        print('-'*30)

        respond = input(f"From -1 to {choose_num-1}, default is all, -1 is None: ")
        if not respond:
            respond = ' '.join(map(str,range(0,choose_num)))
        elif respond == '-1':
            return []
        while not all(map(lambda x: x.isdigit() and int(x) in range(0,choose_num), respond.split())):
            respond = input("Invalid input, please enter again: ")
            if not respond:
                respond = ' '.join(map(str,range(0,choose_num)))
            elif respond == '-1':
                return []

        return [value[int(i)] for i in respond.split()]

    def user_input(self, key:str, value:str, data_dict:dict) -> str:
        print(f"Valid form: {value}")
        respond = input(f"What is your {key}: ")
        while not re.fullmatch(value, respond):
            respond = input("Invalid input, please enter again: ")

        return respond

@BaseCommandBlock.register("Q")
class QueryBlock(BaseCommandBlock):
    def __init__(self, head: Dict[str, str | None]):
        self.valid = ["n", "c", "kor", "vor", "d"]
        super().__init__(head)

    def _operate(self, setup:Dict[str,str|List[str]]) -> bool:
        for key, cond_value in self.condition.items():
            data_value = setup.get(key)
            if data_value is None:
                raise ValueError(f"Unknown key: {key}")

            if isinstance(cond_value, str):
                if isinstance(data_value, str):
                    matched = self._one_to_one_match(cond_value, data_value)
                elif isinstance(data_value, list):
                    matched = self._one_to_many_match(cond_value, data_value)
                else:
                    raise ValueError(f"Unsupported type of data value: {data_value}")
            elif isinstance(cond_value, list):
                if isinstance(data_value, str):
                    matched = self._many_to_one_match(cond_value, data_value)
                elif isinstance(data_value, list):
                    matched = self._many_to_many_match(cond_value, data_value)
                else:
                    raise ValueError(f"Unsupported type of data value: {data_value}")
            else:
                raise ValueError(f"Unsupported type of condition value: {cond_value}")

            if "kor" in self.oper_flag:
                if matched:
                    return True
            else:
                if not matched:
                    return False

        return "kor" not in self.oper_flag

    def _one_to_one_match(self, cond_value:str, data_value:str) -> bool:
        return re.fullmatch(cond_value, data_value) is not None

    def _one_to_many_match(self, cond_value:str, data_values:List[str]) -> bool:
        for data_value in data_values:
            if self._one_to_one_match(cond_value, data_value):
                return True

        return False

    def _many_to_one_match(self, cond_values:List[str], data_value:str) -> bool:
        if "vor" in self.oper_flag:
            for cond_value in cond_values:
                if self._one_to_one_match(cond_value, data_value):
                    return True
            return False
        else:
            for cond_value in cond_values:
                if not self._one_to_one_match(cond_value, data_value):
                    return False
            return True

    def _many_to_many_match(self, cond_values:List[str], data_values:List[str]) -> bool:
        if "vor" in self.oper_flag:
            for cond_value in cond_values:
                if self._one_to_many_match(cond_value, data_values):
                    return True
            return False
        else:
            for cond_value in cond_values:
                if not self._one_to_many_match(cond_value, data_values):
                    return False
            return True


class CommandTree:
    def __init__(self, filepath:str, **kwargs) -> None:
        self.filepath = filepath

        BaseCommandBlock.set_args_flags(kwargs)

        with open(filepath,'r',encoding="utf-8") as exec_fh:
            lines = exec_fh.readlines()

        self._root = BaseCommandBlock.as_block(lines)

    def run(self, setup:Dict[str,str|List[str]]) -> None:
        self._root.run(setup)
