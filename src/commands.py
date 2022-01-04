#!/usr/bin/env python3.8

import argparse
import difflib
import json
import os
import pathlib
import subprocess
import sys
from subprocess import PIPE


def AplyArgParser(group, desc, help_epilog_str, json_file_path):
    desc_str = "The command {group} provides git-command-like alias.\n"
    if desc:
        desc_str = f"{desc}\n"
    argparser = argparse.ArgumentParser(
        prog=group,
        description=f"{desc_str}Load from {json_file_path}.",
        add_help=True,
        epilog=help_epilog_str,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    argparser.add_argument("command", type=str, nargs="?", help=f"a {group} command")
    argparser.add_argument(
        "argument", type=str, nargs="*", help=f"an argument for each {group} command"
    )
    argparser.add_argument(
        "-s",
        "--show",
        action="store_true",
        required=False,
        help="only show command line",
    )
    return argparser


def IsJson(json_str):
    file_open = open(json_str, "r")
    try:
        json_obj = json.loads(file_open.read())
    except ValueError as e:
        return False
    return True


def GetSimilarOne(target, lists):
    candidates_with_score = {}
    for cmd in lists:
        is_similar = False
        score = difflib.SequenceMatcher(None, target, cmd).ratio()
        # print(target, cmd, score)
        if score > 0.2:
            candidates_with_score[score] = cmd

    candidates = []
    for key, cmd in sorted(candidates_with_score.items(), reverse=True):
        candidates.append(cmd)

    max_to_show_similar_args = 5
    return candidates[:max_to_show_similar_args]


def ReadCommandSetting(command_list_json):
    if not IsJson(command_list_json):
        error_message = f"'{command_list_json}' is not json format. \nPlease fix {command_list_json}."
        sys.exit(error_message)

    json_open = open(command_list_json, "r")
    json_load = json.load(json_open)

    if not "group" in json_load.keys():
        error_message = f"'group' key is required. \nPlease fix {command_list_json}."
        sys.exit(error_message)
    group = json_load["group"]

    discription = (
        json_load["description"] if ("description" in json_load.keys()) else ""
    )

    if not "commands" in json_load.keys():
        error_message = f"'commands' key is required. \nPlease fix {command_list_json}."
        sys.exit(error_message)

    commands = {}
    for command_elem in json_load["commands"]:
        args = {}
        if "args" in command_elem.keys():
            for arg_elem in command_elem["args"]:
                if "arg" in arg_elem:
                    key = arg_elem["arg"]
                    arg_elem_desc = (
                        arg_elem["desc"] if ("desc" in arg_elem.keys()) else ""
                    )
                    arg_elem_line = (
                        arg_elem["line"] if ("line" in arg_elem.keys()) else ""
                    )
                    args[key] = arg_elem_desc, arg_elem_line

        if "cmd" in command_elem.keys():
            cmd = command_elem["cmd"]
            command_elem_desc = (
                command_elem["desc"] if ("desc" in command_elem.keys()) else ""
            )
            command_elem_line = (
                command_elem["line"] if ("line" in command_elem.keys()) else ""
            )

            if not args and not command_elem_line:
                continue
            commands[cmd] = command_elem_desc, command_elem_line, args

    help_epilog_str = "command list with argument:\n"

    max_arg = 0
    max_desc = 0
    for cmd_k, cmd_v in commands.items():
        cmd_args = cmd_v[2]
        for arg_k in cmd_args:
            max_arg = max([max_arg, len(arg_k)])
        for arg_v in cmd_args.values():
            max_desc = max([max_desc, len(arg_v[0])])

    for cmd_k, cmd_v in commands.items():
        cmd_desc = cmd_v[0]
        cmd_line = cmd_v[1]
        cmd_args = cmd_v[2]
        temp_str = f"{cmd_k}"
        if cmd_desc:
            temp_str += f" ({cmd_desc})"
        help_epilog_str += f"{list(commands.keys()).index(cmd_k) + 1}) {temp_str:{max_arg + max_desc + 9}}"
        if cmd_line:
            help_epilog_str += f"--> {cmd_line}\n"
        else:
            help_epilog_str += "\n"

        for arg_k, arg_v in cmd_args.items():
            if list(cmd_args.keys()).index(arg_k) + 1 != len(cmd_args.items()):
                tree_str = "├──"
            else:
                tree_str = "└──"
            help_epilog_str += f"   {tree_str} {arg_k:{max_arg + 2}}{arg_v[0]:{max_desc + 2}} --> {arg_v[1]}\n"
        help_epilog_str += "\n"
    return commands, group, discription, help_epilog_str


def main():
    # home_dir = os.path.expanduser("~")
    json_parent = pathlib.Path(f"{__file__}").parent
    json_stem = pathlib.Path(f"{__file__}").stem
    command_list_json = f"{json_parent}/json/{json_stem}.json"
    if not os.path.exists(command_list_json):
        error_message = f"conf json {command_list_json} does not exists"
        sys.exit(error_message)

    commands, group, discription, help_epilog_str = ReadCommandSetting(
        command_list_json
    )
    argparser = AplyArgParser(group, discription, help_epilog_str, command_list_json)
    params = argparser.parse_args()

    if not params.command:
        error_message = argparser.format_help()
        sys.exit(error_message)
    elif params.command not in commands.keys():
        error_message = f"{group}: '{params.command}' is not a {group} command. See '{group} --help'.\n\n"
        error_message += "The most similar commands are\n"
        candidates = GetSimilarOne(params.command, commands.keys())
        for cmd in candidates:
            error_message += f"\t{cmd}\n"
        sys.exit(error_message)

    cmd_line = commands[params.command][1]
    is_only_cmd = cmd_line and (
        not params.argument or not params.argument[0] in commands[params.command][2]
    )

    if is_only_cmd:
        cmd_line_with_arg = cmd_line
        for arg in params.argument:
            cmd_line_with_arg += " " + arg
        if params.show:
            print(cmd_line_with_arg)
        else:
            sh_cmd = [cmd_line_with_arg]
            subprocess.run(sh_cmd, shell=True)
        return 0

    args = commands[params.command][2]

    if not params.argument:
        error_message = argparser.format_usage()
        error_message += f"\n{group}: Not found argument for {params.command}. See '{group} --help'.\n\n"
        error_message += "The available arguments are\n"
        for arg in args.keys():
            error_message += f"\t{arg}\n"
        sys.exit(error_message)

    sub_cmd = params.argument[0]
    if not args.keys():
        error_message = argparser.format_usage()
        error_message += f"\n{group}: Any argument is not acceptable for {params.command}. See '{group} --help'.\n\n"
        sys.exit(error_message)
    elif sub_cmd not in args.keys():
        error_message = f"{group}: '{sub_cmd}' is not a '{group} {params.command}' argument. See '{group} --help'.\n\n"
        error_message += "The most similar arguments are\n"
        candidates = GetSimilarOne(sub_cmd, args.keys())
        for arg in candidates:
            error_message += f"\t{arg}\n"
        sys.exit(error_message)

    cmd_line = args[sub_cmd][1]
    cmd_line_with_arg = cmd_line
    for arg in params.argument[1:]:
        cmd_line_with_arg += " " + arg

    if params.show:
        print(cmd_line_with_arg)
    else:
        sh_cmd = [cmd_line_with_arg]
        subprocess.run(sh_cmd, shell=True)

    return 0


if __name__ == "__main__":
    main()
