# Installation

## From PyPI

```bash
pip install oehrpy
```

## From Source

```bash
git clone https://github.com/platzhersh/oehrpy.git
cd oehrpy
pip install -e .
```

## Development Setup

Install with development and generator extras:

```bash
pip install -e ".[dev,generator]"
```

This installs:

- **Runtime**: `pydantic>=2.0`, `httpx>=0.25`, `defusedxml>=0.7`
- **Dev**: `pytest`, `pytest-asyncio`, `mypy`, `ruff`
- **Generator**: `jinja2>=3.0`, `lxml>=4.9` (for code generation from OPT/BMM files)

## Verify Installation

```python
import openehr_sdk
from openehr_sdk.rm import DV_TEXT

text = DV_TEXT(value="Hello, openEHR!")
print(text.value)  # Hello, openEHR!
```
