#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from os import path, listdir

VIEWS_FOLDER = path.join(path.abspath(path.dirname(__file__)), "views")

CALIBRATIONS_FILE = path.join(path.abspath(path.dirname(__file__)), "calibrations.json")

def get_all_view_files():
    if not path.exists(VIEWS_FOLDER):
        return []

    return [path.join(VIEWS_FOLDER, f) for f in listdir(VIEWS_FOLDER) if path.isfile(path.join(VIEWS_FOLDER, f))]

def get_all_transformations():
    if not path.exists(CALIBRATIONS_FILE):
        return []

    with open(CALIBRATIONS_FILE) as f:
        return json.load(f)