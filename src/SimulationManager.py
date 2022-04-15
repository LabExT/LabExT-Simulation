#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import src.CLI as cli
from src.WizardCli import ChipWizard, MoverWizard

class SimulationManager:
    def __init__(self) -> None:
        cli.out("--- WELCOME TO THE LABEXT MOVEMENT SIMULATION ---", bold=True)

        cli.out("Mover Setup:", bold=True)
        self.mover = MoverWizard()._mover

        cli.out("Chip Setup:", bold=True)
        self.chip = ChipWizard()._chip
    
        
      