#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from termcolor import cprint

class CLI:

    ERROR_COLOR = 'red'
    SUCCESS_COLOR = 'green'

    YES_ANSWERS = ['y', 'yes']
    NO_ANSWERS = ['n', 'no']

    def __init__(self, simulation_manager) -> None:
        self.simulation_manager = simulation_manager


    def out(self, message: str, color: str = None, highlight: str = None, bold: bool = False, underline: bool = False, overwritable: bool=False) -> None:
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
        

    def ask_yes_or_no(self, message: str = "Do you want to proceed?", default: bool = False) -> bool:
        answer = str(input("{} ([y]/n) ".format(message)))
        if answer == '':
            return default

        if answer in self.YES_ANSWERS:
            return True
        
        if answer in self.NO_ANSWERS:
            return False

        self.out("Invalid answer {}".format(answer), color=self.ERROR_COLOR)
        return self.ask_yes_or_no(message, default)

    def ask_for_input(self, message: str, type = str, default = None):
        answer_string = input("{} ({}): ".format(message, default) if default is not None else "{}: ".format(message))
        try:
            if answer_string == '' and default is not None:
                return default

            return type(answer_string)
        except Exception:
            self.out("Invalid type of {}, required type {}".format(answer_string, type), color=self.ERROR_COLOR)
            return self.ask_for_input(message, type, default)


    def welcome_message(self):
        foo = self.ask_for_input("Dein Alter", default=12, type=int)
        print(foo)