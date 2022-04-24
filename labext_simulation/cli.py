#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from termcolor import cprint, colored
from inquirer import Text, List, Confirm, prompt
from os import path, listdir

import click

ERROR_COLOR = 'red'
SUCCESS_COLOR = 'green'
ASK_COLOR = 'yellow'

ARROW_RIGHT = "\U000027A1"
GLOBE = "\U0001F30D"
ROBOT = "\U0001F916"
ATOM = "\U0000269B"
HAT = "\U0001F3A9"
TOOLS = "\U0001F6E0"


def out(message: str, color: str = None, highlight: str = None, bold: bool = False, underline: bool = False, overwritable: bool=False) -> None:
    """
    Prints a message to terminal with given color, bold and underline properties.
    """
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


def success(message: str):
    """
    Prints a green bold message to terminal.
    """
    out(message, color=SUCCESS_COLOR, bold=True)

def error(message: str):
    """
    Prints a red bold message to terminal.
    """
    out(message, color=ERROR_COLOR, bold=True)


def input(message: str, type = str, default = None):
    """
    Asks for input.
    """
    try:
        return click.prompt("[{}] {}".format(colored("?", color=ASK_COLOR), message), type=type, default=default)
    except click.Abort:
        raise KeyboardInterrupt


def choice(message: str, choices: list, default = None):
    """
    Asks for a choice.
    """
    return prompt(
        [List("choice", message=message, choices=choices, default=default)],
        raise_keyboard_interrupt=True).get("choice", default)

def confirm(message: str, default: bool = False) -> bool:
    """
    Asks for confirmation.
    """
    return prompt([Confirm('confirm', message=message, default=default)], raise_keyboard_interrupt=True).get('confirm', default)