#! /usr/bin/python3

#%% import modules
import subprocess
import re
import json
from sys import argv
from typing import Optional

#%% define the regular expression pattern
condition_block_start_pattern:re.Pattern = re.compile(r'^#>>> ({.*})\s*(#<<<)?\s*')
condition_block_end_pattern:re.Pattern = re.compile(r'^#<<<\s*')
command_block_start_pattern:re.Pattern = re.compile(r'^#%%(.*) ({.*})\s*(#%%)?\s*')
command_block_end_pattern:re.Pattern = re.compile(r'^#%%\s*')

#%% define command block
class CommandBlock():
    wait_all_flag:bool = False

    def __init__(self,wait_flag=False,run_flag=True) -> None:
        self.command_to_run:str = ""
        self.wait_flag:bool = wait_flag
        self.run_flag:bool = run_flag

    def __repr__(self) -> str:
        return self.command_to_run

    def add(self,new_command:str) -> None:
        self.command_to_run += new_command

    def run(self,data_dict:dict) -> None:
        if self.run_flag:
            formatted_command:str = self.command_to_run.format(**data_dict)
            if self.wait_all_flag or self.wait_flag:
                print("\n\n"+">"*50+"\nCommand to run:")
                print(formatted_command,end='')
                print("<"*50)
                input("(Enter to run) ")          
            subprocess.run(formatted_command,shell=True,check=True).check_returncode()

#%% handle how to interact with user
def user_input(cond_key,cond_value):
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
            user_respond = input(f"Unknown input, please enter again: ")
            if not user_respond:
                user_respond = '0'
        else:
            return cond_value[int(user_respond)]
    elif type(cond_value) is str:
        return input(f"What is your {cond_key}: ")
    else:
        raise ValueError("Unsupported type of condition value")

#%% handle how to check an load condition 
def check_and_load_condition(condition_dict,data_dict):
    for cond_key,cond_value in condition_dict.items():
        if not isinstance(cond_key,str):
            raise ValueError("Unsopported type of condition key")
        if cond_key not in data_dict:
            data_dict[cond_key] = user_input(cond_key,cond_value)
        if isinstance(cond_value,list):
            if not any(re.fullmatch(cond_value_i,data_dict[cond_key]) for cond_value_i in cond_value):
                return False
        elif not re.fullmatch(cond_value,data_dict[cond_key]):
            return False
    return True

#%% load file and execute it
def exec_file(filepath:str,data_dict=dict()):
    not_store_set = set()
    with open(filepath,'r') as fh:
        print("Start setup...")
        condition_block_stack = []
        command_block:Optional[CommandBlock] = None
        for i,line in enumerate(fh.readlines()):
            #print(line,end='')
            if match_condition_start := condition_block_start_pattern.fullmatch(line):
                if not condition_block_stack or all(condition_block_stack):
                    condition_dict:dict = json.loads(match_condition_start.group(1).encode('utf-8'))
                    condition_block_stack.append(check_and_load_condition(condition_dict,data_dict))
                else:
                    condition_block_stack.append(False)
                if match_condition_start.group(2):
                    condition_block_stack.pop()
            elif condition_block_end_pattern.fullmatch(line):
                condition_block_stack.pop()
            elif not condition_block_stack or all(condition_block_stack):
                if match_command_start := command_block_start_pattern.fullmatch(line):
                    _match = match_command_start.groups()
                    post_parameters:str = _match[0]
                    condition_dict:dict = json.loads(_match[1].encode('utf-8'))
                    is_one_line_block:bool = bool(_match[2])

                    command_block = CommandBlock()
                    command_block.run_flag = check_and_load_condition(condition_dict,data_dict)
                    
                    if not command_block.run_flag:
                        if '*' in post_parameters:
                            raise ValueError(f"Unsupported given condition:\n{data_dict}")
                        else:
                            print(f"Doesn't match the block condition:\n{condition_dict}\nIgnore this block.")
                    if '%' in post_parameters:
                        not_store_set.update(condition_dict.keys())
                    if '@' in post_parameters:
                        command_block.wait_flag = True
                    if is_one_line_block:
                        command_block.run(data_dict)
                        command_block = None
                elif command_block_end_pattern.fullmatch(line):
                    if command_block:
                        command_block.run(data_dict)
                        command_block = None
                    else:
                        raise ValueError(f"Reach end of command block, but no block exist")
                elif command_block:
                    command_block.add(line)
        assert not condition_block_stack and not command_block
        print("Reach end of file, setup completely")
    store_dict = data_dict.copy()
    for key in not_store_set:
        del store_dict[key]
    return store_dict

#%% main function
if __name__ == '__main__':
    if len(argv) > 1:
        file_path:str = argv[1]
    else:
        print("No file provide, use default file path")
        file_path:str = "data/testfile"
    
    #Load dictionary
    dict_path:str = "data/data_dict.json"
    store_dict:dict = dict()
    try:
        with open(dict_path,"r") as fh:
            store_dict = json.load(fh)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        pass
    
    #user checking
    if store_dict:
        print(f"Load store dictionary:\n{store_dict}")
        input("I have checked (enter to continue) ")

    #Execute file
    store_dict = exec_file(file_path,store_dict)

    #Write dictionary into file
    with open(dict_path,"w") as fh:
        json.dump(store_dict,fh,indent=2)
