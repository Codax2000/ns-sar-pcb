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

Run these commands from the repository root. Python dependencies are installed with `uv` (`.python-version` is 3.12; `uv.lock` pins Sphinx, the Read the Docs theme, sphinx-peakrdl, and schemdraw).

Diagram PNGs are generated into `docs/_static/img/` and are not committed. `make doc` regenerates them before the Sphinx build.

| Action | Terminal Command | Behavior |
| :--- | :--- | :--- |
| Generate diagrams | `uv run python ./scripts/diagrams.py` | Write schemdraw PNGs under `docs/_static/img/`. |
| Build website | `make doc` | Generate diagrams, then build Sphinx HTML into `docs/_build/html`. |
| Preview website | `make serve` | Serve the built HTML locally. |
| Deploy website | `make deploy` | Push `docs/_build/html` to the `gh-pages` branch with `ghp-import`. |
| Generate register RTL/UVM | `make gen` | Run PeakRDL register generation and redraw diagrams. |
| Model unit tests | `PYTHONPATH=scripts uv run python -m unittest models.fp_array models.cordic models.sinegen_dac models.nssar` | Run the unittest cases in the modeling package. |
| One HDL block test | `make hdltest.<name>` | Run `scripts/hdl_sim/test_<name>.py` with cocotb and Verilator. |
| All HDL block tests | `make hdltest` | Run every `test_*.py` under `scripts/hdl_sim/`. With none present, exit 0. |

Python layout under `scripts/`:

- `models/` — fixed-point, CORDIC, sine-generator DAC, and noise-shaping SAR models (`from models.fp_array import ...` with `scripts` on `PYTHONPATH`)
- `hdl_sim/` — cocotb + Verilator block tests. `make hdltest.dac_datapath` checks that the idle DAC datapath wrapper stays at midscale, not SNR.
- `diagrams.py`, `registers.py`, `peakrdl_templates/` — documentation and register tooling

Pushes to `main` that change the docs, Python scripts under `scripts/`, register specifications, or the Python lockfile run [`.github/workflows/docs.yml`](.github/workflows/docs.yml). That workflow regenerates the diagrams, builds the Sphinx site, and publishes `docs/_build/html` to `gh-pages`, which is the branch GitHub Pages already serves. After the workflow is on `main`, the same job can be started by hand with **Actions → Docs → Run workflow**.

# AI Tools for this Project

I used Cursor IDE, Gemini, and Aider for this project. To start Aider, run the following command:

```
aider --model gemini/gemini-2.5-flash
```