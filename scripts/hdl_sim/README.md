# Block-level HDL tests

Cocotb and Verilator block tests live in this directory. UVM system tests are a different target and are not run from here.

From the repository root, after `uv sync`:

| Command | Makefile arguments | Runs |
| --- | --- | --- |
| `make hdltest.<name>` | `MODULE=test_<name>` `SIM=verilator` | `test_<name>.py` |
| `make hdltest` | `SIM=verilator` | Every `test_*.py`, or nothing if there are none |

`make hdltest.dac_snr` maps to cocotb module `test_dac_snr`. This makefile copies `MODULE` to cocotb 2's `COCOTB_TEST_MODULES` and includes cocotb's `Makefile.sim`.

`make hdltest.dac_top` runs `test_dac_top.py` against Verilog module `dac_top`. `dac_top.mk` sets `VERILOG_SOURCES` and `COCOTB_TOPLEVEL`. The test checks reset and the one-word CPUIF loopback. It does not score a sine or an SNR. `test_dac_top.sv` instantiates `dac_top` for the chip, but that wrapper also instantiates generated `dac_regs_mod`, so the block test does not elaborate it.

Adding another block test takes two pieces:

1. `test_<name>.py` — cocotb tests.
2. Verilog sources — `<name>.mk` setting `VERILOG_SOURCES` (and `COCOTB_TOPLEVEL` if the Verilog module is not `<name>`), or the same variables on the `make` command line.

`make hdltest.<name>` stops before the simulator if either piece is missing. `make hdltest` exits 0 without calling Verilator while no `test_*.py` files exist.

Verilator is not installed by `uv`. Cocotb supports Verilator 5.036 and newer; install that binary locally. `cocotb` and `cocotb-bus` are Python dependencies in `pyproject.toml`. The makefile prepends the repository `.venv/bin` directory so `cocotb-config` is found without activating the virtualenv.
