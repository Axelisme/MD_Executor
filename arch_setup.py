#! /usr/bin/python3
'''A python script for runnig command from markdown file'''

#%% import modules
import re
import json
from sys import argv
from subprocess import run
from typing import Optional
from io import StringIO

#%% define the regular expression pattern
condition_block_start_pattern:re.Pattern = re.compile(r'^#>>> ({.*})\s*(#<<<)?\s*')
condition_block_end_pattern:re.Pattern = re.compile(r'^#<<<\s*')
command_block_start_pattern:re.Pattern = re.compile(r'^#%%(.*) ({.*})\s*(#%%)?\s*')
command_block_end_pattern:re.Pattern = re.compile(r'^#%%\s*')

#%% define command block
class CommandBlock():
    '''add and run commands in shell'''

    wait_all_flag:bool = False

    __slots__ = ('command_to_run', 'wait_flag', 'run_flag')

    def __init__(self,wait_flag=False,run_flag=True) -> None:
        self.command_to_run:StringIO= StringIO()
        self.wait_flag:bool = wait_flag
        self.run_flag:bool = run_flag

    def __repr__(self) -> str:
        return self.command_to_run.getvalue()

    def add(self,new_command:str) -> None:
        "Add a command to command block"
        self.command_to_run.write(new_command)

    def run(self,data_dict:dict) -> None:
        "Run the command in command block"
        if self.run_flag:
            formatted_command:str = self.command_to_run.getvalue().format(**data_dict)
            if self.wait_all_flag or self.wait_flag:
                print("\n\n"+">"*50+"\nCommand to run:")
                print(formatted_command,end='')
                print("<"*50)
                input("(Enter to run) ")
            run(formatted_command,shell=True,check=True).check_returncode()

#%% handle how to interact with user
def user_input(cond_key,cond_value) -> str:
    '''ask user system condition'''
    if isinstance(cond_value,list):
        type_num:int = len(cond_value)
        if type_num == 1:
            return cond_value[0]
        print(f"\n\nSelect what {cond_key} you want, supported type are: ")
        print('-'*30)
        for i,name in enumerate(cond_value):
            print(f"{i}) {name}")
        print('-'*30)
        user_respond:str = input(f"From 0 to {type_num-1}, default is 0: ")
        if not user_respond:
            user_respond = '0'
        while not user_respond.isdigit() or int(user_respond) not in range(0,type_num):
            user_respond = input("Unknown input, please enter again: ")
            if not user_respond:
                user_respond = '0'
        return cond_value[int(user_respond)]
    if isinstance(cond_value,str):
        return input(f"What is your {cond_key}: ")
    raise ValueError("Unsupported type of condition value")

#%% handle how to check an load condition
def check_and_load_condition(condition_dict,data_dict) -> bool:
    '''check and load system condition with given condition'''
    for cond_key,cond_value in condition_dict.items():
        if not isinstance(cond_key,str):
            raise ValueError("Unsopported type of condition key")
        if cond_key not in data_dict:
            data_dict[cond_key] = user_input(cond_key,cond_value)
        if isinstance(cond_value,list):

            if not any(re.fullmatch(cond_value_i,data_dict[cond_key]) \
                       for cond_value_i in cond_value):
                return False
        elif not re.fullmatch(cond_value,data_dict[cond_key]):
            return False
    return True

#%% load file and execute it
def exec_file(filepath:str,data_dict:dict) -> dict:
    '''execute file from filepath'''
    not_store_set = set()
    with open(filepath,'r',encoding="utf-8") as exec_fh:
        print("Start setup...")
        condition_block_stack = []
        command_block:Optional[CommandBlock] = None
        def handle_condition_block_start(match_condition_start:re.Match) -> None:
            nonlocal condition_block_stack
            if not condition_block_stack or all(condition_block_stack):
                condition_dict:dict = json.loads(match_condition_start.group(1).encode('utf-8'))
                condition_block_stack.append(check_and_load_condition(condition_dict,data_dict))
            else:
                condition_block_stack.append(False)
            if match_condition_start.group(2):
                condition_block_stack.pop()
        def handle_condition_block_end() -> None:
            nonlocal condition_block_stack
            condition_block_stack.pop()
        def handle_command_block_start(match_command_start:re.Match) -> None:
            nonlocal command_block
            nonlocal not_store_set
            _match = match_command_start.groups()
            post_parameters:str = _match[0]
            condition_dict:dict = json.loads(_match[1].encode('utf-8'))
            is_one_line_block:bool = bool(_match[2])

            command_block = CommandBlock()
            command_block.run_flag = check_and_load_condition(condition_dict,data_dict)
            if not command_block.run_flag:
                if '*' in post_parameters:
                    raise ValueError(f"Unsupported given condition:\n{data_dict}")
                print(f"""\
                    Doesn't match the block condition:
                    {condition_dict}
                    Ignore this block.""")
            if '%' in post_parameters:
                not_store_set.update(condition_dict.keys())
            if '@' in post_parameters:
                command_block.wait_flag = True
            if is_one_line_block:
                command_block.run(data_dict)
                command_block = None
        def handle_command_block_end() -> None:
            nonlocal command_block
            if command_block:
                command_block.run(data_dict)
                command_block = None
            else:
                raise ValueError("Reach end of command block, but no block exist")
        def handle_line(line:str) -> None:
            nonlocal command_block
            if command_block:
                command_block.add(line)
        for line in exec_fh.readlines():
            #print(line,end='')
            if match_condition_start := condition_block_start_pattern.fullmatch(line):
                handle_condition_block_start(match_condition_start)
            elif condition_block_end_pattern.fullmatch(line):
                handle_condition_block_end()
            elif condition_block_stack and not all(condition_block_stack):
                continue
            elif match_command_start := command_block_start_pattern.fullmatch(line):
                handle_command_block_start(match_command_start)
            elif command_block_end_pattern.fullmatch(line):
                handle_command_block_end()
            else:
                handle_line(line)
        assert not condition_block_stack and not command_block
        print("Reach end of file, setup completely")
    def make_store_dict(data_dict:dict,not_store_set:set) -> dict:
        store_dict = data_dict.copy()
        for key in not_store_set:
            del store_dict[key]
        return store_dict
    return make_store_dict(data_dict,not_store_set)

def load_file(dict_path:str) -> dict:
    """Load dictionary from file"""
    #load dictionary
    store_dict:dict = {}
    try:
        with open(dict_path,"r",encoding="utf-8") as exec_fh:
            store_dict = json.load(exec_fh)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}
    #user checking
    if store_dict:
        print(f"Load store dictionary:\n{store_dict}")
        input("I have checked (enter to continue) ")

    return store_dict

def dump_file(store_path:str,store_dict:dict) -> None:
    """dump data into file"""
    with open(store_path,"w",encoding="utf-8") as exec_fh:
        json.dump(store_dict,exec_fh,indent=2)

#%% main function
def main(file_path:str,dict_path:str = "data/data_dict.json") -> None:
    '''main function'''
    #Load dictionary
    init_dict:dict = load_file(dict_path)

    #Execute file
    store_dict = exec_file(file_path,init_dict)

    #Write dictionary into file
    dump_file(dict_path,store_dict)

#%% run code
if __name__ == '__main__':
    exec_path:str = ""
    if len(argv) > 1:
        exec_path:str = argv[1]
    else:
        print("No file provide, use default file path")
        exec_path:str = "data/testfile"
    #run main function
    main(exec_path)
