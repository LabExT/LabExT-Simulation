#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from termcolor import cprint
from inquirer import Text, List, Confirm, prompt
from os import path, listdir

ERROR_COLOR = 'red'
SUCCESS_COLOR = 'green'

YES_ANSWERS = ['y', 'yes']
NO_ANSWERS = ['n', 'no']


def out(message: str, color: str = None, highlight: str = None, bold: bool = False, underline: bool = False, overwritable: bool=False) -> None:
    attrs = []
    if bold:
        attrs.append('bold')

    if underline:
        attrs.append("underline")

    cprint(
        message,
        color,
        highlight,
        attrs=attrs,
        end="\r" if overwritable else None)

def ask_for_input(message: str, type = str, default = None):
    answer_string = input("{} ({}): ".format(message, default) if default is not None else "{}: ".format(message))
    try:
        if answer_string == '' and default is not None:
            return default

        return type(answer_string)
    except Exception:
        out("Invalid type of {}, required type {}".format(answer_string, type), color=ERROR_COLOR)
        return ask_for_input(message, type, default)


def success(message: str):
    out(message, color=SUCCESS_COLOR, bold=True)

def error(message: str):
    out(message, color=ERROR_COLOR, bold=True)

def confirm(message: str, default: bool = False) -> bool:
    return prompt([Confirm('x', message=message, default=default)]).get('x', default)

def setup_new_stage(available_stages, orientations, ports):
    return prompt([
        List('stage',
            message="Which stage should be configured?",
            choices=available_stages
        ),
        List('orientation',
            message="What orientation should the stage have?",
            choices=orientations
        ),
        List('port',
            message="What port should the stage have?",
            choices=ports
        ),
    ])

def setup_new_chip():
    chips_folder = path.join(path.abspath(path.dirname(__file__)), "chips")
    
    file = prompt([
        List("path",
            message="Which chip should be loaded?",
            choices=[f for f in listdir(chips_folder) if path.isfile(path.join(chips_folder, f))]
        ),
    ]).get("path")

    return path.join(chips_folder, file)


def setup_mover():
    return {k: float(v) for k, v in prompt([
        Text('speed_xy', "Speed XY in um/s", default="200.0"),
        Text('speed_z', "Speed Z in um/s", default="20.0"),
        Text('acceleration_xy', "Acceleration XY in um^2/s", default="50.0"),
        Text('z_lift', "Z channel up-movement in um", default="20.0"),
    ]).items()}


def ask_for_action(message: str, actions: list):
    return prompt([
        List('action',
            message=message,
            choices=actions
        )
    ]).get('action')