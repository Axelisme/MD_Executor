
import json

def load_dict(dictpath:str) -> dict:
    '''load dict from dict file'''
    try:
        with open(dictpath,'r',encoding="utf-8") as dict_fh:
            store_dict = json.load(dict_fh)
    except FileNotFoundError:
        store_dict = None
        print("dictionary not found! ignore")

    if isinstance(store_dict, dict):
        print(f"Load store dictionary:\n{store_dict}")
        respond = input("Accept: (Y/n) ")
        while respond.lower() not in ["y","n",""]:
            respond = input("Unrecognized input, accept: (Y/n) ")
        if respond.lower() == "n":
            print("Ignore store dictionary")
            store_dict = {}
        else:
            print("Accept store dictionary")
    else:
        store_dict = {}

    return store_dict

def dump_dict(dictpath:str, store_dict:dict) -> None:
    '''dump dict into dict file'''
    if store_dict == {}:
        return

    with open(dictpath,'w',encoding="utf-8") as dict_fh:
        json.dump(store_dict,dict_fh,indent=2)