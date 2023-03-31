#! /usr/bin/python3
'''A python script for runnig command from markdown file'''

# import modules
import re
import json
import os
from sys import argv
from typing import Optional
from CommandBlock import *

# load file and execute it
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
        for line in exec_fh.readlines():
            #print(line,end='')
            if match_condition_start := condition_block_start_pattern.fullmatch(line):
                handle_condition_block_start(match_condition_start)
            elif condition_block_end_pattern.fullmatch(line):
                handle_condition_block_end()
            elif condition_block_stack and not all(condition_block_stack):
                continue
            elif match_command_start := command_block_start_pattern.fullmatch(line):
                if command_block:
                    raise ValueError("Reach start of command block but previous one not terminate")
                command_block = CommandBlock(data_dict, match_command_start)
                if command_block.not_store:
                    not_store_set.update(command_block.condition_dict.keys())
                if match_command_start.group(3):
                    command_block = None
            elif command_block_end_pattern.fullmatch(line):
                if command_block:
                    command_block.run(data_dict)
                    command_block = None
                else:
                    raise ValueError("Reach end of command block, but no block exist")
            elif command_block:
                command_block.add(line)
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
    if not os.path.exists("./data"):
        os.makedirs("./data")
    try:
        with open(dict_path,"r",encoding="utf-8") as load_fh:
            store_dict = json.load(load_fh)
    except (FileNotFoundError, json.decoder.JSONDecodeError):
        return {}
    #user checking
    if store_dict:
        print(f"Load store dictionary:\n{store_dict}")
        input("I have checked (enter to continue) ")

    return store_dict

def dump_file(store_path:str,store_dict:dict) -> None:
    """dump data into file"""
    with open(store_path,"w",encoding="utf-8") as dump_fh:
        json.dump(store_dict,dump_fh,indent=2)

# main function
def main(file_path:str,dict_path:str = "data/data_dict.json") -> None:
    '''main function'''
    #Load dictionary
    init_dict:dict = load_file(dict_path)

    #Execute file
    store_dict = exec_file(file_path,init_dict)

    #Write dictionary into file
    dump_file(dict_path,store_dict)

# run code
if __name__ == '__main__':
    exec_path:str = ""
    if len(argv) > 1:
        exec_path:str = argv[1]
    else:
        print("No file provide, use default file path")
        exec_path:str = "data/testfile"
    #run main function
    main(exec_path)
