import re
import subprocess as sp
from typing import Optional, List, Dict, Union, Any

class BaseCommandBlock:
    start_pat = "#%*"
    oper_pat = "[_A-Z]"
    flag_pat = "[a-z]+(?:,[a-z]+)*"
    cond_pat = "{.*}"
    end_pat = "#@*|```"
    head_pat = re.compile(
        f"^(?:```bash=?\s*)?(?P<start>{start_pat})(?P<oper>{oper_pat}):\s*(?P<flag>{flag_pat})?\s+(?P<cond>{cond_pat})\s*(?P<end>{end_pat})?\s*$"
    )
    tail_pat = re.compile(f"^(?P<end>{end_pat})\s*$")

    _register_block:Dict[str,"BaseCommandBlock"] = {"_":"BaseCommandBlock"}

    @classmethod
    def register_block(cls, oper:str, block:"BaseCommandBlock") -> None:
        cls._register_block[oper] = block

    def __init__(self, head:Dict[str,str], line_iter:iter) -> None:
        self.level = len(head["start"]) - 1

        self.operation = head["oper"]

        self.oper_flag = head["flag"]
        self.oper_flag = self.oper_flag.split(",") if self.oper_flag else []
        assert self.check_flag(), f"Invalid flag: {self.oper_flag}"

        self.condition = eval(head["cond"])
        assert isinstance(self.condition, dict), f"expect condition be a dict but get {self.condition}"

        if end := head.get("end"):
            assert end != "```", "Invalid Syntax: Cannot use ``` in one line mode."

            end_level = len(end) - 1
            assert self.level == end_level, \
                f"start level is mismatched with end level, {self.level} != {end_level}"
            self.content = []
        else:
            self.content = self._parse_content(line_iter)

    @classmethod
    def _parse_head(cls, line:str) -> Optional[Dict[str,Any]]:
        match = cls.head_pat.fullmatch(line)
        return match.groupdict() if match else None

    @classmethod
    def _parse_tail(cls, line:str) -> Optional[Dict[str,Any]]:
        match = cls.tail_pat.fullmatch(line)
        return match.groupdict() if match else None

    def _parse_content(self, line_iter:iter) -> List[Union[str,"BaseCommandBlock"]]:
        command_buffer = ""
        content = []

        def pack_command() -> None:
            nonlocal command_buffer
            if command_buffer:
                content.append(command_buffer)
                command_buffer = ""

        for line in line_iter:
            if (match := self._parse_head(line)) is not None:
                pack_command()
                sub_level = len(match["start"]) - 1
                assert self.level + 1 == sub_level, \
                    f"current level: {self.level}, sub level: {sub_level}"
                BlockClass = self._register_block.get(match["oper"])
                if BlockClass is None:
                    raise ValueError(f"Unknown operation: {match['oper']}")
                content.append(eval(BlockClass)(match, line_iter))

            elif (match := self._parse_tail(line)) is not None:
                pack_command()
                if match["end"] != "```":
                    end_level = len(match["end"]) - 1
                    assert self.level == end_level, \
                        f"start level is mismatched with end level, {self.level} != {end_level}"
                break

            else:
                command_buffer += line

        pack_command()

        return content

    def _operate(self, data_dict:dict) -> bool:
        return True

    def check_flag(self) -> bool:
        valid = ["n", "c"]
        return all(flag in valid for flag in self.oper_flag)

    def _exec_command(self, commands:str, data_dict:dict) -> None:
        if "n" in self.oper_flag:
            return
        formatted_command:str = commands.format(**data_dict)
        if "c" in self.oper_flag:
            print("\n\n"+">"*50+"\nCommand to run:")
            print(formatted_command,end='')
            print("<"*50)
            input("(Enter to run) ")
        sp.run(formatted_command,shell=True,check=True).check_returncode()

    def run(self, data_dict:dict) -> None:
        if self._operate(data_dict):
            for content in self.content:
                if isinstance(content, BaseCommandBlock):
                    content.run(data_dict)
                else:
                    self._exec_command(content, data_dict)


class AddBlock(BaseCommandBlock):
    BaseCommandBlock.register_block("A", "AddBlock")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.operation = "A"

    def _operate(self, data_dict:dict) -> bool:
        if "s" in self.oper_flag:
            data_dict.update(self.condition)
            return True

        for key, value in self.condition.items():
            if key in data_dict:
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

    def check_flag(self) -> bool:
        valid = ["s","m","n"]
        return all(flag in valid for flag in self.oper_flag)

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

        respond = input(f"From 0 to {choose_num-1}, default is all: ")
        if not respond:
            respond = ' '.join(map(str,range(0,choose_num)))
        while not all(map(lambda x: x.isdigit() and int(x) in range(0,choose_num), respond.split())):
            respond = input("Invalid input, please enter again: ")
            if not respond:
                respond = ' '.join(map(str,range(0,choose_num)))

        return [value[int(i)] for i in respond.split()]

    def user_input(self, key:str, value:str, data_dict:dict) -> str:
        print(f"Valid form: {value}")
        respond = input(f"What is your {key}: ")
        while not re.fullmatch(value, respond):
            respond = input("Invalid input, please enter again: ")

        return respond


class QueryBlock(BaseCommandBlock):
    BaseCommandBlock.register_block("Q", "QueryBlock")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.operation = "Q"

    def _operate(self, data_dict:dict) -> bool:
        for key, cond_value in self.condition.items():
            data_value = data_dict.get(key)
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

    def check_flag(self) -> bool:
        valid = ["n", "c", "vor", "kor"]
        return all(flag in valid for flag in self.oper_flag)


class CommandTree:
    def __init__(self, filepath:str):
        self.filepath = filepath

        base_head = BaseCommandBlock._parse_head("#_:n {}")

        with open(filepath,'r',encoding="utf-8") as exec_fh:
            lines = exec_fh.readlines()
            lines = [line for line in lines if line != "\n"] + ["#\n"]

        self._root = BaseCommandBlock(base_head, iter(lines))

    def run(self, data_dict:dict) -> None:
        self._root.run(data_dict)
