#!/usr/bin/env python3.8

import argparse
import json
import os
import pathlib
import subprocess
import sys
from enum import Enum, auto
from jinja2 import Environment, FileSystemLoader
from pathlib import Path
from subprocess import PIPE


def ParseArgs():
    argparser = argparse.ArgumentParser(
        prog="generate_commands",
        description="",
        add_help=True,
        epilog="",
    )
    argparser.add_argument(
        "-v",
        "--version",
        action="store_true",
        required=False,
        help="show version",
    )
    argparser.add_argument(
        "-j",
        "--json",
        type=str,
        required=False,
        help="specify input json file",
    )
    argparser.add_argument(
        "-c",
        "--check_only",
        action="store_true",
        required=False,
        help="only check command status",
    )
    argparser.add_argument(
        "-r",
        "--remove",
        action="store_true",
        required=False,
        help="remove command without config.",
    )
    argparser.add_argument(
        "-i",
        "--interactive",
        action="store_true",
        required=False,
        help="update by interactive",
    )
    argparser.add_argument(
        "-s",
        "--show_commands",
        action="store_true",
        required=False,
        help="show command usages.",
    )
    argparser.add_argument(
        "--verbose",
        action="store_true",
        required=False,
        help="print verbose",
    )
    return argparser.parse_args()


class CommandAvailability(Enum):
    Empty = auto()
    Available = auto()
    Broken = auto()


class CommandUpdateState(Enum):
    NoChange = auto()
    Updated = auto()
    New = auto()
    Removed = auto()


class CommandFileStatus:
    availability = CommandAvailability.Empty
    update_state = CommandUpdateState.NoChange
    has_config = False


def IsJson(json_str):
    file_open = open(json_str, "r")
    try:
        json_obj = json.loads(file_open.read())
    except ValueError as e:
        return False
    return True


def LoadJsonFile(command_list_json):
    if not IsJson(command_list_json):
        error_message = f"\033[31m{command_list_json} is not json format.\033[0m \n"
        error_message += f"Please fix \033[34m{command_list_json}\033[34m."
        sys.exit(error_message)
    json_open = open(command_list_json, "r")
    json_load_list = json.load(json_open)
    return json_load_list


def yes_or_no(ask_str):
    while True:
        choice = input(f"{ask_str} [y/N]: ").lower()
        if choice in ["y", "ye", "yes"]:
            return True
        elif choice in ["n", "no"]:
            return False
        elif not choice:
            return False


def CheckUserDirectory(user_dir, verbose):
    if not os.path.isdir(user_dir):
        print(f"[INFO] mkdir \033[34m{os.path.abspath(user_dir)}\033[0m")
        os.makedirs(user_dir)
    elif verbose:
        print(f"[INFO] \033[34m{os.path.abspath(user_dir)}\033[0m already exsits.")

    user_json_dir = f"{user_dir}/json"
    if not os.path.isdir(user_json_dir):
        print(f"[INFO] mkdir \033[34m{os.path.abspath(user_json_dir)}\033[0m")
        os.makedirs(user_json_dir)
    elif verbose:
        print(f"[INFO] \033[34m{os.path.abspath(user_json_dir)}\033[0m already exsits.")

    user_zsh_func_dir = f"{user_dir}/zsh_func"
    if not os.path.isdir(user_zsh_func_dir):
        print(f"[INFO] mkdir \033[34m{os.path.abspath(user_zsh_func_dir)}\033[0m")
        os.makedirs(user_zsh_func_dir)
    elif verbose:
        print(f"[INFO] \033[34m{os.path.abspath(user_zsh_func_dir)}\033[0m already exsits.")
    return


def CheckAvailability(user_dir, group):
    if os.path.exists(f"{user_dir}/{group}"):
        if os.path.exists(f"{user_dir}/json/{group}.json"):
            if os.path.exists(f"{user_dir}/zsh_func/_{group}"):
                return True
    return False


def FetchCommandFileStatusMap(user_dir):
    cmd_status_list = {}
    for file_path in list(Path(user_dir).glob("*")):
        if os.path.isdir(file_path):
            continue
        stem = str(Path(file_path).stem).lstrip("_")
        if not stem in cmd_status_list.keys():
            cmd_status_list[stem] = CommandFileStatus()
    return cmd_status_list


def LinkExecuteFile(src_dir, user_exec_link_file):
    if os.path.exists(user_exec_link_file):
        link_path_old = os.readlink(user_exec_link_file)
        if link_path_old == f"{src_dir}/commands.py":
            return False
    print(f"[INFO]     ==>  exec link  : \033[34m{user_exec_link_file}\033[0m")
    subprocess.run(
        [f"ln -snf {src_dir}/commands.py {user_exec_link_file}"], shell=True
    )
    return True


def DumpCommandJson(json_load, user_json_file):
    if os.path.exists(user_json_file):
        json_load_old = LoadJsonFile(user_json_file)
        if json_load_old == json_load:
            return False
    print(f"[INFO]     ==>  conf. json : \033[34m{user_json_file}\033[0m")
    with open(user_json_file, mode="wt", encoding="utf-8") as file:
        json.dump(json_load, file, ensure_ascii=False, indent=2)
    return True


def GenerateZshFunction(src_dir, group, json_load, user_zsh_func_file):
    env = Environment(loader=FileSystemLoader(str(src_dir)))
    template = env.get_template(f"zsh_func.tpl")
    zsh_func = template.render({"group": group, "commands": json_load["commands"]})

    if os.path.exists(user_zsh_func_file):
        f = open(user_zsh_func_file, 'r', encoding='UTF-8')
        zsh_func_old = f.read()
        if zsh_func_old == zsh_func:
            return False

    print(f"[INFO]     ==>  zsh func   : \033[34m{user_zsh_func_file}\033[0m")
    with open(user_zsh_func_file, mode="wt", encoding="utf-8") as file:
        file.write(zsh_func)
    return True

def GenerateTargetCommand(group, src_dir, user_dir, json_load):
    group_bold = f"\033[1m{group}\033[0m"
    print(f"[INFO] Generate command group: {group_bold}")
    is_generated = False
    is_generated |= LinkExecuteFile(src_dir, f"{user_dir}/{group}")
    is_generated |= DumpCommandJson(json_load, f"{user_dir}/json/{group}.json")
    is_generated |= GenerateZshFunction(src_dir, group, json_load, f"{user_dir}/zsh_func/_{group}")

    if not is_generated:
        if CheckAvailability(user_dir, group):
            print(f"[INFO] \033[33mNo change.\033[0m\n")
        else:
            print(f"[WARNING] \033[33mExistent command is invalid\033[0m: {group_bold}.\n")
    else:
        if CheckAvailability(user_dir, group):
            print(f"[INFO] \033[36mComplete.\033[0m\n")
        else:
            print(f"[WARNING] \033[33mFailed to generate command\033[0m: {group_bold}.\n")
    return is_generated

def EraceTargetCommand(group, user_dir):
    print(f"[INFO] Remove {group}")
    if os.path.exists(f"{user_dir}/{group}"):
        os.remove(f"{user_dir}/{group}")
    if os.path.exists(f"{user_dir}/json/{group}.json"):
        os.remove(f"{user_dir}/json/{group}.json")
    if os.path.exists(f"{user_dir}/zsh_func/_{group}"):
        os.remove(f"{user_dir}/zsh_func/_{group}")
    return

def ShowCommandGenerationResult(cmd_status_list, verbose):
    generated_cmd_list = []
    for group, cmd_status in cmd_status_list.items():
        if cmd_status.availability == CommandAvailability.Available:
            if cmd_status.update_state != CommandUpdateState.NoChange:
                generated_cmd_list.append(group)

    if generated_cmd_list:
        party_popper = chr(int(0x2728))
        cake = chr(int(0x1F389))
        print(
            f"[INFO] Success generation of commands. {party_popper} {cake} {party_popper}"
        )
        cmds_str = ""
        for cmd in generated_cmd_list:
            cmds_str += f"{str(cmd)} "
        print(f"       ==> \033[1m{cmds_str}\033[0m\n")
    elif verbose:
        print("[INFO] Nothing to generate.\n")



def ShowCommandFileStatusListSummary(cmd_status_list):
    cmd_status_label_str = "               " + "(avalable)  " + "(config)    " + "(state)"
    print(cmd_status_label_str)
    cmd_status_list_sorted = sorted(cmd_status_list.items())
    for group, cmd_status in cmd_status_list_sorted:
        availability = ""
        if cmd_status.availability == CommandAvailability.Empty:
            availability = "empty"
            availability = f"\033[31m{availability:<12}\033[0m"
        elif cmd_status.availability == CommandAvailability.Available:
            availability = "OK"
            availability = f"\033[32m{availability:<12}\033[0m"
        elif cmd_status.availability == CommandAvailability.Broken:
            availability = "broken"
            availability = f"\033[31m{availability:<12}\033[0m"

        has_config = ""
        if cmd_status.has_config:
            has_config = "OK"
            has_config = f"\033[32m{has_config:<12}\033[0m"
        else:
            has_config = "no config!"
            has_config = f"\033[31m{has_config:<12}\033[0m"

        state = ""
        if cmd_status.update_state == CommandUpdateState.NoChange:
            state = "no change"
            state = f"\033[33m{state:<12}\033[0m"
        elif cmd_status.update_state == CommandUpdateState.Updated:
            state = "updated"
            state = f"\033[36m{state:<12}\033[0m"
        elif cmd_status.update_state == CommandUpdateState.New:
            state = "new"
            state = f"\033[36m{state:<12}\033[0m"
        elif cmd_status.update_state == CommandUpdateState.Removed:
            state = "removed"
            state = f"\033[31m{state:<12}\033[0m"

        cmd_status_str = f"\033[1m{group:16}\033[0m" + availability + has_config + state
        print(cmd_status_str)
    print()
    return

def ShowPathSettingSummary(is_ok_PATH, is_ok_fpath):
    path_str = "\033[32mOK\033[0m" if is_ok_PATH else "\033[31mX\033[0m"
    fpath_str = "\033[32mOK\033[0m" if is_ok_fpath else "\033[31mX\033[0m"
    print(f"export PATH      : {path_str}")
    print(f"export zsh fpath : {fpath_str}\n")
    return

def CheckEnvPath(user_dir):
    is_ok_PATH = (user_dir in str(os.environ.get("PATH")))
    return is_ok_PATH

def CheckZshFPATH(user_dir, src_dir):
    is_ok_fpath = False
    if "zsh" in str(os.environ.get("SHELL")):
        proc = subprocess.run([f"{src_dir}/get_fpath.zsh"], shell=True, stdout=PIPE, stderr=PIPE, text=True)
        is_ok_fpath = (f"{user_dir}/zsh_func" in proc.stdout)
    else:
        is_ok_fpath = True
    return is_ok_fpath

def ShowSettingRecommendation(is_ok_PATH, is_ok_fpath, user_dir):
    if not is_ok_PATH or not is_ok_fpath:
        print("[INFO] One more step!!!")

    if not is_ok_PATH:
        print(
            "[INFO] Please add below lines to ~/.bashrc or ~/.zshrc or  ~/.zshenv .."
        )
        print("#Setting commands")
        print(f'export PATH="{user_dir}:$PATH"')

    if not is_ok_fpath:
        print("[INFO] Please add below lines to ~/.zshrc or  ~/.zshenv.")
        print(f"fpath=({user_dir}/zsh_func $fpath)")
        print("autoload -Uz compinit && compinit")
    return

def ShowCommandHelp(cmd_status_list, user_dir):
    for group in sorted(cmd_status_list.keys()):
        if cmd_status_list[group].availability == CommandAvailability.Available:
            group_bold = f"\033[1m{group}\033[0m"
            print(f"------------------ {group_bold} ------------------\n")
            subprocess.run(
                [f"{user_dir}/{group} -h"], shell=True
            )
            print()
    return


def main():
    args = ParseArgs()
    if args.show_commands:
        args.check_only = True

    if args.version:
        prog = str(Path(sys.argv[0]).stem)
        print(f"{prog}: version 0.0")
        return 0

    parent_dir = pathlib.Path(os.path.abspath(__file__)).parent
    src_dir = f"{parent_dir}/src"
    user_dir = f"{parent_dir}/user"
    if not args.check_only:
        CheckUserDirectory(user_dir, args.verbose)
    cmd_status_list = FetchCommandFileStatusMap(user_dir)
    for group in cmd_status_list:
        if not CheckAvailability(user_dir, group):
            cmd_status_list[group].availability = CommandAvailability.Broken

    json_file_path = f"{parent_dir}/commands.json"
    if args.json:
        json_file_path = args.json

    if not os.path.exists(json_file_path):
        error_message = f"[ERROR] \033[31mNo input json.\033[0m\nPlease create \033[34m{json_file_path}\033[0m."
        sys.exit(error_message)

    json_load_list = LoadJsonFile(json_file_path)
    for json_load in json_load_list:
        if not "group" in json_load:
            error_message = f"[ERROR] \033[31mAn item with no group exists in json input.\033[0m \nPlease fix \033[34m{json_file_path}\033[0m."
            sys.exit(error_message)

        group = json_load["group"]

        if not "commands" in json_load or not json_load["commands"]:
            error_message = f"[ERROR] \033[31mNo commands in {group}.\033[0m \nPlease fix \033[34m{json_file_path}\033[0m."
            sys.exit(error_message)

        is_existing = group in cmd_status_list
        if not is_existing:
            cmd_status_list[group] = CommandFileStatus()
        cmd_status_list[group].has_config = True

        if args.check_only:
            continue

        is_generated = False
        if is_existing:
            group_bold = f"\033[1m{group}\033[0m"
            ask_str = f"[INFO] {group_bold} already exists. Do you want to update?"
            if not args.interactive or yes_or_no(ask_str):
                cmd_status_list[group].update_state = CommandUpdateState.Updated
                is_generated = GenerateTargetCommand(group, src_dir, user_dir, json_load)
        else:
            cmd_status_list[group].update_state = CommandUpdateState.New
            is_generated = GenerateTargetCommand(group, src_dir, user_dir, json_load)

        if not is_generated:
            cmd_status_list[group].update_state = CommandUpdateState.NoChange

    if args.remove:
        for group in cmd_status_list.keys():
            if not cmd_status_list[group].has_config:
                group_bold = f"\033[1m{group}\033[0m"
                ask_str = f"[INFO] {group_bold} has no config. Do you remove {group_bold}?"
                if not args.interactive or yes_or_no(ask_str):
                    cmd_status_list[group].update_state = CommandUpdateState.Removed
                    EraceTargetCommand(group, user_dir)
                print()

    for group in cmd_status_list.keys():
        if CheckAvailability(user_dir, group):
            cmd_status_list[group].availability = CommandAvailability.Available

    ShowCommandGenerationResult(cmd_status_list, args.verbose)

    is_ok_PATH = CheckEnvPath(user_dir)
    is_ok_fpath = CheckZshFPATH(user_dir, src_dir)
    ShowCommandFileStatusListSummary(cmd_status_list)
    ShowPathSettingSummary(is_ok_PATH, is_ok_fpath)

    if not args.check_only:
        ShowSettingRecommendation(is_ok_PATH, is_ok_fpath, user_dir)

    if args.show_commands:
        ShowCommandHelp(cmd_status_list, user_dir)

    return 0


if __name__ == "__main__":
    main()
