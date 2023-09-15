#! /usr/bin/python3
'''A python script for runnig command from markdown file'''

# import modules
from argparse import ArgumentParser

from CommandTree import CommandTree
from StatusDict import load_dict, dump_dict

def main(args):
    # create command tree
    command_tree = CommandTree(args.filepath)

    # load from dict file
    store_dict = load_dict(args.dict)

    # run command tree
    command_tree.run(store_dict)

    # dump to dict file
    dump_dict(args.dict,store_dict)


if __name__ == '__main__':
    parser = ArgumentParser(description="A python script for runnig command from markdown file")
    parser.add_argument("-f","--filepath",help="the path of markdown file")
    parser.add_argument("-d","--dict",help="the path of dict file", default="data/dict.json")

    args = parser.parse_args()

    main(args)

