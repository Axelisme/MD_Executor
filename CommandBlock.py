# import modules
import re
import json
from subprocess import run
from io import StringIO

# define the regular expression pattern
condition_block_start_pattern:re.Pattern = re.compile(r'^#>>> ({.*})\s*(#<<<)?\s*$')
condition_block_end_pattern:re.Pattern = re.compile(r'^#<<<\s*$')
command_block_start_pattern:re.Pattern = re.compile(r'^#%%(.*) ({.*})\s*(#%%)?\s*$')
command_block_end_pattern:re.Pattern = re.compile(r'^#%%\s*$')

# define command block
class CommandBlock():
    '''add and run commands in shell'''

    wait_all_flag:bool = False

    __slots__ = ('condition_dict', 'run_flag', 'not_store', 'wait_flag', 'command_to_run')

    def __init__(self, data_dict:dict, match_command_start:re.Match) -> None:
        _match = match_command_start.groups()
        post_parameters:str = _match[0]
        self.condition_dict:dict = json.loads(_match[1].encode('utf-8'))

        self.run_flag = check_and_load_condition(self.condition_dict,data_dict)
        if not self.run_flag and '*' in post_parameters:
            raise ValueError(f"Unsupported given condition:\n{data_dict}")
        self.not_store = '%' in post_parameters
        self.wait_flag = '@' in post_parameters
        self.command_to_run:StringIO= StringIO()

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
        self.command_to_run.close()

# handle how to interact with user
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

# handle how to check an load condition
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