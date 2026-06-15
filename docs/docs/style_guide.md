# Codax2000 Engineering Style Guide
**Revision:** 1.0  

**Core Philosophy:** Documentation is a contract. If code and comments diverge, the code is the truth,
but the comments are a liability. Prefer automated documentation (NaturalDocs) and readable logic over "clouds of text."
In short, comments are no substitute for illegible code.

---

## 1. SystemVerilog Style Guide
All SystemVerilog files must utilize **NaturalDocs** headers. Comments should explain the *why* (architectural intent), while the code should be readable enough to explain the *what* at a glance.

### 1.1. RTL
Prefer to keep things short and clear where possible.

### 1.2. DV
1. Stick to the Doulos Easier UVM Coding Guidelines where possible; i.e. with naming conventions, config conventions, etc.

## 2. Python Style Guide
Python is the "automation glue" of the project. It must be as reliable as the hardware it generates.

### 2.1 Linting & Standards
* **Linter:** Use `flake8` conventions. Code must pass with zero warnings.
* **Docstrings:** Use NaturalDocs for documentation. Python `help` still works, but docstrings have
to be above the function. This sucks, but we want our documentation in one place.

### 2.2 Project-Specific Rules
* **No Hard-Coding:** Scripts must pull parameters (bit-widths, memory depths) from the design source where possible.
* **Diagrammatic Integrity:** Technical diagrams must be generated via `schemdraw` in `scripts/diagrams.py`. Manual edits to images are a pain, just update the script so Git can see the changes.

---

## 3. General "Clean Code" Principles
* **Meaningful Names:** If you need a comment to explain a variable name, the name is probably wrong. We comment variables in NaturalDocs so a user knows how to use them from the documentation, not to explain poor naming.
* **Single Responsibility Princible:** Functions should do one thing. 
* **Follow Conventions Where Possible:** Use the imports that everyone uses, (i.e. no `import numpy as nump`). 