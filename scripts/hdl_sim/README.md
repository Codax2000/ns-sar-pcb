# HDL simulation

Cocotb 2 tests in this directory run on Verilator. From the repository root, `uv sync` installs `cocotb` (it is a `pyproject.toml` dependency). Verilator 5.036 or newer is a separate install; `uv` does not provide it.

`make`, `make help`, and `make clean` do not start the simulator.

From `scripts/hdl_sim` (sources are listed in the `Makefile`):

```text
make spi.sim            # bare spi, tb_spi.py
make test_dac_top.sim   # test_dac_top, tb_test_dac_top.py
```

`%.sim` sets `TOPLEVEL=$*` and `COCOTB_TEST_MODULES=tb_$*`. All RTL in the Makefile is compiled for every target. `tb_spi.py` drives `spi` (`rst_n`, `cs_b`) with hand-set `if_rd_data`. `tb_test_dac_top.py` writes and reads FREQUENCY on `test_dac_top` (`arst_n`, `csb`).

On Windows, use GNU make. If `cocotb-config` is not picked up, put `.venv/Scripts` on `PATH`.
