# HDL simulation

Cocotb 2 tests in this directory run on Verilator. From the repository root, `uv sync` installs `cocotb` (it is a `pyproject.toml` dependency). Verilator 5.036 or newer is a separate install; `uv` does not provide it.

`make`, `make help`, and `make clean` do not start the simulator.

From `scripts/hdl_sim` (sources are listed in the `Makefile`):

```text
make spi.sim            # bare spi, tests/test_spi.py
make test_dac_top.sim   # test_dac_top, tests/test_test_dac_top.py
make chip_top.sim       # chip_top DAC connectivity, tests/test_chip_top.py
```

`%.sim` sets `TOPLEVEL=$*` and `COCOTB_TEST_MODULES=tests.test_$*`. All RTL in the Makefile is compiled for every target. Shared SPI helpers live in `utils/spi_utils.py` (`write_reg` / `read_reg`) and use `csb` when present, else `dac_csb`. `tests/test_spi.py` drives `spi` (`rst`, `csb`) with hand-set `if_rd_data`. `tests/test_test_dac_top.py` exercises `test_dac_top` DAC5311 monitors. `tests/test_chip_top.py` checks DAC SPI readback and dual power-down frames on `chip_top`.

On Windows, use GNU make. If `cocotb-config` is not picked up, put `.venv/Scripts` on `PATH`.
