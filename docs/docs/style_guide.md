# Codax2000 Engineering Style Guide
**Revision:** 1.0  

**Core Philosophy:** Documentation is a contract. If code and comments diverge, the code is the truth,
but the comments are a liability. Prefer automated documentation (NaturalDocs) and readable logic over "clouds of text."
In short, comments are no substitute for illegible code.

---

## 1. SystemVerilog Style Guide
All SystemVerilog files must utilize **NaturalDocs** headers. Comments should explain the *why* (architectural intent), while the code should be readable enough to explain the *what* at a glance.

### 1.1 RTL (Synthesizable)
* **Assignments:** Sequential logic **must** use non-blocking assignments (`<=`).
* **Resets:** Use active-low synchronous resets with the name `rst_n`. They will be synchronized on-chip if they are asynchronous coming in.
* **Automation:** Never manually code register banks. Use **PeakRDL** to generate RTL from the `.rdl` specification to ensure a single source of truth.

### 1.2 Behavioral Modeling (Analog/Mixed-Signal)
* **Signal Types:** Use `real` for continuous signals (voltages, currents) in behavioral models.
* **Precision:** Every behavioral file must include a local `` `timescale ``.
* **Partitioning:** Models should mimic the physical PCB floorplan. If an integrator is discrete on the board, it should be a standalone module in the simulation. This also helps with block-level validation in SPICE, since we can't do co-simulation without some kind of sim engine.

### 1.3 Design Verification (DV)
* **File Names** * Package files should end with `_pkg.sv`. All other UVM class files should be defined as header files, using `.svh`. Modules should always end in `.sv`.
* **Naming:** * Classes: `snake_case` (e.g., `adc_scoreboard`, `spi_monitor`).
    * Member Variables: `m_` prefix if an instance of an object that extends a UVM type (e.g., `m_env_cfg`) Exceptions for an agent, in which case the driver, monitor, sequencer should be called `driver`, `monitor`, `sequencer`.
* **Virtual Interfaces:** No direct RTL hierarchy references. Use `uvm_config_db` to pass virtual interfaces (`vif`).
* **Reporting:** Use `uvm_ms_info`, `uvm_ms_warning`, and `uvm_ms_error` macros to ensure analog-bridge signals are logged correctly within the UVM environment.
* **Variables:** * If something is Vivado-incompliant (e.g. real-type coverpoints), use a workaround and add `ifdef`s using the `VIVADO` define.
---

## 2. Python Style Guide
Python is the "automation glue" of the project. It must be as reliable as the hardware it generates.

### 2.1 Linting & Standards
* **Linter:** **flake8** is mandatory. Code must pass with zero warnings.
* **Docstrings:** Use NaturalDocs for documentation. Python `help` still works, but docstrings have
to be above the function. This sucks, but we want our documentation in one place.

### 2.2 Project-Specific Rules
* **No Hard-Coding:** Scripts must pull parameters (bit-widths, memory depths) from the design source where possible.
* **Diagrammatic Integrity:** Technical diagrams must be generated via `schemdraw` in `scripts/diagrams.py`. Manual edits to images are a pain,
just update the script so Git can see the changes.

---

## 3. General "Clean Code" Principles
* **Meaningful Names:** If you need a comment to explain a variable name, the name is probably wrong. We comment variables in NaturalDocs so a user
knows how to use them from the documentation, not to explain poor naming.
* **Small Functions:** Functions should do one thing. 
* **Stale Comments are Bugs:** Delete self-evident comments. Document the *decisions*, not the *syntax*.