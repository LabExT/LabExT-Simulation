#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from termcolor import cprint


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
    

def ask_yes_or_no(message: str = "Do you want to proceed?", default: bool = False) -> bool:
    answer = str(input("{} ([y]/n) ".format(message)))
    if answer == '':
        return default

    if answer in YES_ANSWERS:
        return True
    
    if answer in NO_ANSWERS:
        return False

    out("Invalid answer {}".format(answer), color=ERROR_COLOR)
    return ask_yes_or_no(message, default)

def ask_for_input(message: str, type = str, default = None):
    answer_string = input("{} ({}): ".format(message, default) if default is not None else "{}: ".format(message))
    try:
        if answer_string == '' and default is not None:
            return default

        return type(answer_string)
    except Exception:
        out("Invalid type of {}, required type {}".format(answer_string, type), color=ERROR_COLOR)
        return ask_for_input(message, type, default)
