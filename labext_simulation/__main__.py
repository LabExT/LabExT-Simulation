#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from sys import exit
from os import path, listdir

from labext_simulation.management import start_simulation_manager

CHIPS_FOLDER = path.join(path.abspath(path.dirname(__file__)), "chips")
VIEWS_FOLDER = path.join(path.abspath(path.dirname(__file__)), "views")

def main():
    start_simulation_manager(
        chips_folder_path=CHIPS_FOLDER,
        views_folder_path=VIEWS_FOLDER)

if __name__ == "__main__":
    exit(main())