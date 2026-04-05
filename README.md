# Noise-Shaping SAR PCB
The goal of this project is to create a 2nd-order, noise shaping SAR on a printed circuit board (PCB).

The full documentation can be found on this project's website, on [GitHub Pages](https://codax2000.github.io/ns-sar-pcb/).

## Required Tools

| Tool | Purpose |
| :--- | :--- |
| Git | Version Control |
| Git Bash | Terminal Command Automation |
| Python | Technical documentation, high-level simulation |
| Xilinx Vivado | Digital logic design + simulation |
| KiCAD | PCB design and analog simulation w/NgSpice |

## Running a Vivado Simulation in GUI Mode

Running Vivado should be very simple. All you should have to do is open the `hdl_design.xpr` project and then click "Run Behavioral Simulation". Whatever the default UVM test is should run.

## Running a Simulation in Batch Mode

There will soon be a bash script that will run the digital regression and show pass rate, coverage, etc. Bonus points for adding it as a bash hook.

## Building Documentation

Given that this project is being written in Windows with no native Makefile support, everything is done via bash script. The plus side of this is that scripts could be added into commits

| Action | Terminal Command | Behavior |
| :--- | :--- | :--- |
| Generate all documentation and publish | `source gen_all.sh ` | Regenerate the website, documentation, RTL, register map, and push to GitHub Pages. |
| Generate register RTL/UVM, etc | `python ./scripts/registers.py` | Runs the registers script, which generates RTL, website information, and UVM stuff. |
| Build website | `cd docs; mkdocs build` | Build website, which can then be opened using `index.html` in browser. |
| Deploy website | `cd docs; mkdocs gh-deploy` | Deploy website to GitHub Pages |