# Arch_Setup

## Run
run the script like:
```bash=
./arch_setup.py $path_to_install_guide
```
or use binary file
```bash=
./arch_setup $path_to_install_guide
```

## Grammar
```bash=
#%% {requirements dict}     <-- begin of block
...command to run...
#%%                         <-- end of block
```
* script will remember your system condition once it know it.
* script will excute the command in block if and only if your system condition reach its requirements.
* the requitement's value can be a regular expression or a list of accept regular expressions.
* script will auto store your system condition into file and ask you to load it at begining.
* if script doesn't know the system condition, it will ask you to input.
* you can add flag after #%% at begin of block, '*' for necessary condition, '%' for not store this conditon to file, '@' for asking you before run this block
* substring like {key} in the command will be auto substituded to its value.

Example:
```bash=
#%%@* {"kernel":["linux","linux-lts"], "UserName":".+"}
pacman -S {kernel}
useradd {UserName}
#%%
```
