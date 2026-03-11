# oehrpy

**Python SDK for openEHR** — /oʊ.ɛər.paɪ/ ("o-air-pie")

[![CI](https://github.com/platzhersh/oehrpy/actions/workflows/ci.yml/badge.svg)](https://github.com/platzhersh/oehrpy/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/oehrpy)](https://pypi.org/project/oehrpy/)
[![Python](https://img.shields.io/pypi/pyversions/oehrpy)](https://pypi.org/project/oehrpy/)
[![License](https://img.shields.io/github/license/platzhersh/oehrpy)](https://github.com/platzhersh/oehrpy/blob/main/LICENSE)

A comprehensive Python SDK for openEHR that provides type-safe Reference Model classes, template-specific composition builders, an EHRBase client, and an AQL query builder.

## Why oehrpy?

The openEHR ecosystem has lacked a comprehensive, actively maintained Python SDK. Developers working with openEHR in Python have been forced to manually construct complex nested JSON structures — error-prone, with no IDE support and no type safety.

oehrpy solves this with:

- **134 type-safe RM classes** — Pydantic v2 models for the full openEHR Reference Model 1.1.0
- **Template builders** — Generate type-safe composition builders from OPT files
- **FLAT format support** — Full EHRBase 2.26.0+ FLAT format serialization
- **Canonical JSON** — Round-trip openEHR canonical JSON with `_type` fields
- **EHRBase client** — Async REST client for EHR, composition, and query operations
- **AQL query builder** — Fluent API to build type-safe AQL queries

## Quick Install

```bash
pip install oehrpy
```

## Quick Example

```python
from openehr_sdk.templates import VitalSignsBuilder

builder = VitalSignsBuilder(composer_name="Dr. Smith")
builder.add_blood_pressure(systolic=120, diastolic=80)
builder.add_pulse(rate=72)
builder.add_temperature(37.2)

flat_data = builder.build()
```

## Background

oehrpy is part of the **Open CIS** project. Read about the journey:

- [Building Open CIS Part 4: The openEHR SDK Landscape](https://medium.com/@platzh1rsch/building-open-cis-part-4-the-openehr-sdk-landscape-1b93411ec279) — Survey of existing SDKs and the gap that motivated oehrpy
- [Building Open CIS Part 5: oehrpy — A Python SDK for openEHR](https://medium.com/@platzh1rsch/building-open-cis-part-5-oehrpy-a-python-sdk-for-openehr-c9c90f46d075) — Announcement and walkthrough

## Getting Started

Ready to dive in? Head to [Installation](getting-started/installation.md) or jump straight to the [Quick Start](getting-started/quick-start.md).
