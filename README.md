# LabExT Movement Simulation

Tool to simulate as well as possible the movements of stages locally without laboratory equipment.

The tool is based on vedo and VTK as CG library and the latest version of LabExT Mover.
- vedo: https://vedo.embl.es
- LabExT Mover: https://github.com/maltewae/LabExT/tree/movement/relative-absolute

## Development Installation
1. Create new conda environment
```
conda create -n LabExT_Simulation_env python=3.8
```
2. Activate environment
```
conda activate LabExT_Simulation_env
```
3. Install packages
```
pip install -r ./requirements.txt
pip install -e .
```
4. Run the tool
```
LabExT-Simulation
```
Note: The tool has no graphical interface, interactions with the tool are done via the console.