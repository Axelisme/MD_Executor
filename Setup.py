#! /usr/bin/python3

#%%
import sys
import os
import re
import json

#%%
def user_input(cond_key,cond_value):
    if type(cond_value) is list:
        type_num = len(cond_value)
        print(f"\n\nSelect what {cond_key} you used, supported type are: ")
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
    try:
        with open(filepath,'r') as fh:
            print("Start setup...")
            global data_dict
            data_dict = dict()
            command_to_run = ""
            in_block = False
            for line in fh.readlines():
                #print(line,end='')
                if match_header := re.fullmatch(r'^(#%%\*?) ({.*}).*',line,re.DOTALL):
                    json_str = match_header.group(2)
                    condition_dict = json.loads(json_str.encode('utf-8'))
                    if check_and_load_condition(condition_dict):
                        in_block = True
                    elif match_header.group(1)[-1] == '*':
                        raise ValueError("Unsupport setup condition")
                    else:
                        print(f"Unknown system condition {condition_dict}, ignore this block")
                        in_block = False
                elif re.fullmatch(r'^```[^b].*',line,re.DOTALL):
                    in_block = False
                    os.system(command_to_run.format(**data_dict) .encode())
                    command_to_run = ""
                elif in_block:
                    command_to_run += line
            print("Reach end of file, setup completely")
    except Exception as e:
        print(f"Error: {str(e)}")
        exit(0)

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
