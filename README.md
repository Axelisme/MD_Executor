# MD Executor

## Run
run the script like:
```bash=
./md_executor.py -f $path_to_install_guide [-d $dict_path] [--dry-run]
```

## Grammar
```bash=
#%%Q: {requirements dict}     <-- begin of block
...command to run...
#%%                         <-- end of block
```
* there are Add block and Quiry block.
* script will remember your system condition once it know it.
* script will excute the command in block if and only if your system condition reach its requirements.
* the requitement's value can be a regular expression or a list of accept regular expressions.
* script will auto store your system condition into file and ask you to load it at begining.
* substring like {key} in the command will be auto substituded to its value.

Example:
```bash=
#%%Q:c {"kernel":["linux","linux-lts"], "UserName":".+"}
pacman -S {kernel}
useradd {UserName}
#%%
```
