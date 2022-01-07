# gen-cmd-group



- [Features](#features)
- [How to start](#how-to-start)
- [Usage](#usage)
  - [Command structure](#command-structure)
  - [Example of input json file](#example-of-input-json-file)
  - [Handle commnad group](#handle-commnad-group)
  - [Uninstall command group](#uninstall-command-group)

# Features

- Provides git-like alias command group and their help by simple json file input.
- Provides zsh completer function simulteniously.

# How to start

1. Run `command-zoo.py` to generate initial input json file: `commands.json`.
2. Edit `commands.json`. Details are shown in below.
3. Run `command-zoo.py` to generate execution files.
4. Export path of command group directory to `PATH` (optional, but highly recommended)
5. Export path of zsh functions directory to `fpath` (optional, if you use *zsh*)

*`command-zoo.py` requires *python3.9*.

# Usage

## Command structure

Command group has tree category items of `group`, `command`, and `argument` as:

<pre>
group
 ├── command
 │   ├── argument
 │   ├── argument
 │   └── ..
 ├── command
 ├──   ..
</pre>


## Example of input json file

For example, `mycmd` command includes the following commands and arguments.

| command | alias |
| ------------- | ------------- |
| `mycmd command_1`  | [command_1 alias line]  |
| `mycmd command_2 argument_2a`  | [argument_2a alias line]  |
| `mycmd command_2 argument_2b`  | [argument_2b alias line]  |
| `mycmd command_3`  | [argument_3 alias line]  |
| `mycmd command_3 argument_3a`  | [argument_3a alias line]  |

A json file `commands.json` for example command `mycmd` is written as:

```json
[
  {
    "group": "mycmd",
    "description": "[mycmd help description]",
      "commands": [
      {
        "cmd": "command_1",
        "desc": "[command_1 help desc.]",
        "line": "[command_1 alias line]"
      },
      {
        "cmd": "command_2",
        "desc": "[command_2 help desc.]",
        "line": "",
        "args": [
          {
            "arg": "argument_2a",
            "desc": "[argument_2a help]",
            "line": "[argument_2a alias line]"
          },
          {
            "arg": "argument_2b",
            "desc": "[argument_2b help]",
            "line": "[argument_2b alias line]"
          }
        ]
      },
      {
        "cmd": "command_3",
        "desc": "[command_3 help desc.]",
        "line": "[command_3 alias line]",
        "args": [
          {
            "arg": "argument_3a",
            "desc": "[argument_3a help]",
            "line": "[argument_3a alias line]"
          }
        ]
      }
    ]
  },
  {
     .... second command group ....
  }
  ....
]

```

The example command of `mycmd` give help description with `-h` option as:


```
usage: mycmd [-h] [-s] [command] [argument [argument ...]]

[mycmd help description]
Load from commands/user/json/mycmd.json.

positional arguments:
  command     a mycmd command
  argument    an argument for each mycmd command

optional arguments:
  -h, --help  show this help message and exit
  -s, --show  only show command line

command list with argument:
1) command_1 ([command_1 help desc.])    --> [command_1 alias line]

2) command_2 ([command_2 help desc.])
   ├── argument_2a  [argument_2a help]   --> [argument_2a alias line]
   └── argument_2b  [argument_2b help]   --> [argument_2b alias line]

3) command_3 ([command_3 help desc.])    --> [command_3 alias line]
   └── argument_3a  [argument_3a help]   --> [argument_3a alias line]
```

The example command of `mycmd` also give zsh completer as:

```
$mycmd [tab]
command_1  --> [command_1 help desc.]
command_2  --> [command_2 help desc.]
command_3  --> [command_3 help desc.]
```

```
mycmd command_2 [tab]
argument_2a  argument_2b
```

## Handle commnad group

1. Generate and Update commnads
   ```sh
   ./command-zoo.py
   ```

2. Remove commands

    After editing to remove unnecessary from `commands.json`, and then run,
    ```sh
    ./command-zoo.py -r
    ```

3. Check command lists and status
   ```sh
   ./command-zoo.py -c
   ```
   It gives summary of status as:

       (avalable)  (config)    (state)
       mycmd           OK          OK          no change   

       export PATH      : OK
       export zsh fpath : OK


Please run `./command-zoo.py -h` for more details.

## Uninstall command group
1. Run `./command-zoo.py --uninstall` to remove user directory.
2. Unexport `Path` and `fpath`.
