# HDL simulation

Cocotb 2 tests in this directory run on Verilator. From the repository root, `uv sync` installs `cocotb` (it is a `pyproject.toml` dependency). Verilator 5.036 or newer is a separate install; `uv` does not provide it.

`make`, `make help`, and `make clean` do not start the simulator.

From the repository root:

```text
make hdltest TOPLEVEL=<hdl module> TEST=<python module> SOURCES=<file.f>
```

| Variable | Role |
| --- | --- |
| `TOPLEVEL` | HDL toplevel module. Passed to cocotb as `COCOTB_TOPLEVEL`. |
| `TEST` | Python module in this directory, without `.py`. Passed as `COCOTB_TEST_MODULES`. |
| `SOURCES` | Path of a plain Verilator filelist (one RTL or SV path per line). Passed as `verilator -f`. |
| `VERILOG_SOURCES` | Space-separated sources. Use instead of `SOURCES`, or as well as it. |
| `SIM` | Simulator. Default `verilator`. |

`make -C` runs the simulator in this directory, so paths inside the filelist and in `VERILOG_SOURCES` are relative to `scripts/hdl_sim`. `SOURCES` itself may be relative to the repository root or to this directory.

`make hdltest.spi SOURCES=<file.f>` sets `TOPLEVEL=test_dac_top` and `TEST=test_spi`.

Register RTL comes from `make gen` (`scripts/registers.py`), not from this directory. That writes the gitignored DAC block under `hdl_design/hdl_design.srcs/rtl/registers/dac/`. A filelist for the SPI test:

```text
../../hdl_design/hdl_design.srcs/rtl/registers/sync_nstage.sv
../../hdl_design/hdl_design.srcs/rtl/posedge_detector.sv
../../hdl_design/hdl_design.srcs/rtl/registers/spi.sv
../../hdl_design/hdl_design.srcs/rtl/registers/dac/dac_regs_mod_pkg.sv
../../hdl_design/hdl_design.srcs/rtl/registers/dac/dac_regs_mod.sv
../../hdl_design/hdl_design.srcs/rtl/dac_datapath/phase_accumulator.sv
../../hdl_design/hdl_design.srcs/rtl/dac_datapath/cordic.sv
../../hdl_design/hdl_design.srcs/rtl/dac_datapath/dsm_error_feedback.sv
../../hdl_design/hdl_design.srcs/rtl/dac_datapath/dsm_bypass_mux.sv
../../hdl_design/hdl_design.srcs/rtl/dac_datapath/dac5311_ctrl.sv
../../hdl_design/hdl_design.srcs/rtl/dac_datapath.sv
../../hdl_design/hdl_design.srcs/rtl/test_dac_top.sv
```

`tb_test_dac_top.py` defines `send_spi`. It drives `test_dac_top` pins `csb`, `scl`, and `mosi`, and samples `miso`, SPI mode 0 (CPOL=0, CPHA=0, MSB first). `test_spi.py` writes the FREQUENCY register and reads it back. The SPI clock-domain crossing is still wrong, so that readback can fail. Nothing here changes the RTL.

On Windows, use GNU make. If `cocotb-config` is not picked up, put `.venv/Scripts` on `PATH`.
