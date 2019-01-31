# XBOS Building Analysis

<p align="center">
    <img src="./building.png" height="180">
</p>

This repo is for analysis of energy consumption of buildings using the eXtensible Building Operating System (XBOS). To learn more about XBOS, see the documentation [here](https://docs.xbos.io/).

## Status

### Baseline Calculations
- 3/10 baseline calculation in `src/baseline.py`

### Plots
- Comparing event day with baseline energy consumption & weather in `src/plot_event.py`

## Getting Started

### Requirements
- Anaconda (Python 3)
- Python 3.6
- Jupyter Notebook

### Setup
1. Install the requirements
2. Clone the repository
3. Run `conda env create -f environment.yml`. This creates a new python environment called "mortar"
4. Run `conda activate mortar` (windows) or `source activate mortar` (macOS/Linux) to start the environment shell.

### Test Functionality in Jupyter Notebook
1. Inside the "mortar" environment, run `jupyter notebook`
2. Go to the `src` directory and open `plot_example.ipynb`, ensuring that you are running in the "mortar" kernel.
3. Fill in the arguments in the second cell. `site` is the site name. `start` and `end` are the timestamp bounds for the baseline calculation. `event_day` is the day we would like to observe. `event_start_hour` and `event_end_hour` are integers in [0,23] that represent the start and end hour of the DR event. 
4. Run `plot_event`.