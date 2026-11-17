"""Regenerate dac_regs_mod_pkg for the dac_datapath block test.

The package is produced by peakrdl-regblock and gitignored under
hdl_design/hdl_design.srcs/rtl/registers/dac. Pass that directory.
"""

import sys
from pathlib import Path

from systemrdl import RDLCompiler
from peakrdl_regblock import RegblockExporter
from peakrdl_regblock.cpuif.passthrough import PassthroughCpuif
from peakrdl_regblock.udps import ALL_UDPS


def main():
    """Write dac_regs_mod_pkg.sv into the directory given on argv."""
    if len(sys.argv) != 2:
        sys.exit("usage: gen_dac_hwif.py OUTPUT_DIR")
    repo = Path(__file__).resolve().parents[2]
    out = Path(sys.argv[1])
    out.mkdir(parents=True, exist_ok=True)

    rdlc = RDLCompiler()
    for udp in ALL_UDPS:
        rdlc.register_udp(udp)
    rdlc.compile_file(
        repo / "hdl_design/hdl_design.srcs/registers/regblock_udps.rdl"
    )
    rdlc.compile_file(
        repo / "hdl_design/hdl_design.srcs/registers/dac_registers.rdl"
    )
    RegblockExporter().export(
        rdlc.elaborate(),
        str(out),
        cpuif_cls=PassthroughCpuif,
        module_name="dac_regs_mod",
    )


if __name__ == "__main__":
    main()
