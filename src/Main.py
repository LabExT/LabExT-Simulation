#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import src.CLI as cli
from src.SimulationManager import SimulationManager

def main():
    cli.out("--- WELCOME TO THE LABEXT MOVEMENT SIMULATION ---", bold=True)
    SimulationManager()


if __name__ == '__main__':
    main()