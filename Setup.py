#! /usr/bin/python3

#%%
import sys
import subprocess
import re
import json

#%%
def user_input(cond_key,cond_value):
    if type(cond_value) is list:
        type_num = len(cond_value)
        print(f"\n\nSelect what {cond_key} you want, supported type are: ")
        print('-'*30)
        for i,name in enumerate(cond_value):
            print(f"{i}) {name}")
        print('-'*30)
        user_respond = input(f"From 0 to {type_num-1}, default is 0: ")
        user_respond = user_respond if user_respond else '0'
        while not user_respond.isdigit() or int(user_respond) not in range(0,type_num):
            user_respond = input(f"Unknown input, please enter again: ")
            user_respond = user_respond if user_respond else '0'
        else:
            return cond_value[int(user_respond)]
    else:
        user_respond = input(f"What is your {cond_key}: ")
        while not user_respond:
            user_respond = input(f"Empty input, type again: ")
        return user_respond

#%%
def check_and_load_condition(condition_dict):
    global data_dict
    for cond_key,cond_value in condition_dict.items():
        if cond_key not in data_dict:
            if cond_value == []:
                return False
            data_dict[cond_key] = user_input(cond_key,cond_value)
        if type(cond_value) is list:
            if not any(re.fullmatch(cond_value_i,data_dict[cond_key]) for cond_value_i in cond_value):
                return False
        elif not re.fullmatch(cond_value,data_dict[cond_key]):
            return False
    return True

#%%
def exec_file(filepath:str):
    with open(filepath,'r') as fh:
        print("Start setup...")
        global data_dict
        data_dict = dict()
        condition_block_start_pattern = re.compile(r'^#>>> ({.*})\s*')
        condition_block_end_pattern = re.compile(r'^#<<<\s*')
        in_condition_block = False
        run_condition_block = True
        command_block_start_pattern = re.compile(r'^#%%(\*)? ({.*})\s*')
        command_block_end_pattern = re.compile(r'^#%%\s*')
        in_command_block = False
        run_command_block = True
        command_to_run = []
        for line in fh.readlines():
            #print(line,end='')
            if match_condition_start := condition_block_start_pattern.fullmatch(line):
                assert in_condition_block == False
                in_condition_block = True
                condition_dict = json.loads(match_condition_start.group(1).encode('utf-8'))
                run_condition_block = check_and_load_condition(condition_dict)
            elif condition_block_end_pattern.fullmatch(line):
                assert in_condition_block == True
                in_condition_block = False
                run_condition_block = True
            elif run_condition_block:
                if match_command_start := command_block_start_pattern.fullmatch(line):
                    assert in_command_block == False
                    in_command_block = True
                    condition_dict = json.loads(match_command_start.group(2).encode('utf-8'))
                    if not (run_command_block := check_and_load_condition(condition_dict)):
                        if match_command_start.group(1) == '*':
                            raise ValueError("Unacceptable setup condition")
                        else:
                            print(f"Unknown system condition {condition_dict}, ignore this block")
                elif command_block_end_pattern.fullmatch(line):
                    assert in_command_block == True
                    in_command_block = False
                    if run_command_block:
                        subprocess.run(command_to_run,shell=True)
                    command_to_run.clear()
                elif in_command_block and run_command_block:
                    command_to_run.append(line.format(**data_dict))
        assert not in_condition_block and not in_condition_block
        print("Reach end of file, setup completely")

#%%
if __name__ == '__main__':
    if len(sys.argv) == 1:
        print("No file provide, use default file path")
        exec_file("data/testfile")
    elif len(sys.argv) > 2:
        print("Too many file provide")
        exit(0)
    else :
        exec_file(sys.argv[1])
