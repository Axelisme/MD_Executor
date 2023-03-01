#! /usr/bin/python3

#%%
import sys
import subprocess
import re
import json

#%%
def user_input(cond_key,cond_value):
    if type(cond_value) is list:
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
        user_respond:str = input(f"What is your {cond_key}: ")
        while not user_respond:
            user_respond = input(f"Empty input, type again: ")
        return user_respond
    else:
        raise ValueError("Unsupported type of condition value")

#%%
def check_and_load_condition(condition_dict,data_dict):
    for cond_key,cond_value in condition_dict.items():
        if type(cond_key) is not str:
            raise ValueError("Unsopported type of condition key")
        if cond_key not in data_dict:
            data_dict[cond_key] = user_input(cond_key,cond_value)
        if type(cond_value) is list:
            if not any(re.fullmatch(cond_value_i,data_dict[cond_key]) for cond_value_i in cond_value):
                return False
        elif not re.fullmatch(cond_value,data_dict[cond_key]):
            return False
    return True

#%%
condition_block_start_pattern = re.compile(r'^#>>> ({.*})\s*')
condition_block_end_pattern = re.compile(r'^#<<<\s*')
command_block_start_pattern = re.compile(r'^#%%(.*) ({.*})\s*(#%%)?\s*')
command_block_end_pattern = re.compile(r'^#%%\s*')

#%%
def exec_file(filepath:str,data_dict=dict()):
    with open(filepath,'r') as fh:
        print("Start setup...")
        not_store_list = []
        in_condition_block:bool = False
        run_condition_block:bool = True
        in_command_block:bool = False
        run_command_block:bool = True
        command_to_run:str = ""
        for i,line in enumerate(fh.readlines()):
            #print(line,end='')
            if match_condition_start := condition_block_start_pattern.fullmatch(line):
                assert in_condition_block == False
                in_condition_block = True
                condition_dict:dict = json.loads(match_condition_start.group(1).encode('utf-8'))
                run_condition_block = check_and_load_condition(condition_dict,data_dict)
            elif condition_block_end_pattern.fullmatch(line):
                assert in_condition_block == True
                in_condition_block = False
            elif not in_condition_block or run_condition_block:
                if match_command_start := command_block_start_pattern.fullmatch(line):
                    assert in_command_block == False
                    in_command_block = True
                    condition_dict:dict = json.loads(match_command_start.group(2).encode('utf-8'))
                    run_command_block = check_and_load_condition(condition_dict,data_dict)
                    if post_flag := match_command_start.group(1):
                        if '*' in post_flag and not run_command_block:
                            raise ValueError(f"Unsupported condition:\n{data_dict}")
                        if '%' in post_flag:
                            not_store_list.extend(condition_dict.keys())
                    elif not run_command_block:
                        print(f"Don't match the block condition:\n{condition_dict}\nIgnore this block.")
                    if match_command_start.group(3) == "#%%":
                        in_command_block = False
                elif command_block_end_pattern.fullmatch(line):
                    assert in_command_block == True
                    in_command_block = False
                    if run_command_block:
                        #print(command_to_run)
                        subprocess.run(command_to_run,shell=True)
                    else:
                        assert command_to_run == ""
                    command_to_run = ""
                elif in_command_block and run_command_block:
                    command_to_run += line.format(**data_dict)
        assert not in_condition_block and not in_condition_block
        print("Reach end of file, setup completely")
    store_dict = data_dict.copy()
    for key in not_store_list:
        del store_dict[key]
    return store_dict

#%%
if __name__ == '__main__':
    file_path:str = ""
    argv_num:int = len(sys.argv)
    if argv_num <= 1:
        print("No file provide, use default file path")
        file_path = "data/testfile"
    elif argv_num > 2:
        print("Too many file provide")
        exit(0)
    else :
        file_path = sys.argv[1]
    
    #Load dictionary
    dict_path:str = "data/data_dict.json"
    store_dict:dict = dict()
    try:
        with open(dict_path,"r") as fh:
            store_dict = json.load(fh)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        pass
    
    #Execute file
    store_dict = exec_file(file_path,store_dict)

    #Write dictionary into file
    with open(dict_path,"w") as fh:
        json.dump(store_dict,fh,indent=2)

