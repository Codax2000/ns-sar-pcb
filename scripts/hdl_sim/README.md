# Block-level HDL tests

Cocotb and Verilator block tests live in this directory. UVM system tests are a different target and are not run from here.

From the repository root, after `uv sync`:

| Command | Makefile arguments | Runs |
| --- | --- | --- |
| `make hdltest.<name>` | `MODULE=test_<name>` `SIM=verilator` | `test_<name>.py` |
| `make hdltest` | `SIM=verilator` | Every `test_*.py`, or nothing if there are none |

`make hdltest.dac_snr` maps to cocotb module `test_dac_snr`. This makefile copies `MODULE` to cocotb 2's `COCOTB_TEST_MODULES` and includes cocotb's `Makefile.sim`.

`make hdltest.dac_datapath` runs `test_dac_datapath.py` against Verilog module `tb_dac_datapath` (`dac_datapath.mk` sets `COCOTB_TOPLEVEL`). That wrapper lives in `wrappers/` and packs flattened register inputs into `hwif_out`. Two `dac_5311` models (`hdl_design.srcs/dv/models/dac_5311.sv`) turn the serial pins into real voltages. The test checks that an idle serializer leaves both outputs at midscale. It does not score a sine or an SNR. The makefile regenerates the gitignored DAC register package from `dac_registers.rdl`.

Adding another block test takes two pieces:

1. `test_<name>.py` — cocotb tests.
2. Verilog sources — `<name>.mk` setting `VERILOG_SOURCES` (and `COCOTB_TOPLEVEL` if the Verilog module is not `<name>`), or the same variables on the `make` command line.

`make hdltest.<name>` stops before the simulator if either piece is missing. `make hdltest` exits 0 without calling Verilator while no `test_*.py` files exist.

Verilator is not installed by `uv`. Cocotb supports Verilator 5.036 and newer; install that binary locally. `cocotb` and `cocotb-bus` are Python dependencies in `pyproject.toml`. The makefile prepends the repository `.venv/bin` directory so `cocotb-config` is found without activating the virtualenv.
