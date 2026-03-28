# Noise-Shaping SAR PCB
The goal of this project is to create a 2nd-order, noise shaping SAR on a printed circuit board (PCB).

The full documentation can be found on this project's website, on (GitHub Pages)[https://codax2000.github.io/ns-sar-pcb/].

## Required Tools

## Cloning the Repo

## Running a Vivado Simulation in GUI Mode

## Running a Simulation in Batch Mode

## Building Documentation

Eventually, the goal should be to have a script that does everything from generate registers and other stuff to regenerating the website (kind of like a Makefile).

In lieu of that:

| Action | Terminal Command | Behavior |
| :--- | :--- | :--- |
| Generate register RTL/UVM, etc | `python ./scripts/registers.py` | Runs the registers script, which generates RTL, website information, and UVM stuff. |
| Build website | `cd docs; mkdocs build` | Build website, which can then be opened using `index.html` in browser. |
| Deploy website | `cd docs; mkdocs gh-pages` | Deploy website to GitHub Pages |