# About oehrpy

## Name & Pronunciation

**oehrpy** — /oʊ.ɛər.paɪ/ ("o-air-pie")

Short for "openehrpy", where "ehr" is pronounced like "air" (as in openEHR). The name follows the Python convention of short, pronounceable package names.

## Motivation

The openEHR ecosystem has a mature Java SDK ([openEHR Java SDK](https://github.com/ehrbase/openEHR_SDK)) and various tools in other languages, but Python — one of the most widely used languages in healthcare data science and backend development — had no comprehensive, actively maintained SDK.

Developers working with openEHR in Python were forced to:

1. **Manually construct JSON** — Complex nested structures with precise paths, easy to get wrong
2. **No IDE support** — No autocomplete, no type checking, no documentation hints
3. **Memorize template paths** — Every FLAT format path had to be known by heart
4. **No validation** — Errors only caught at submission time to the CDR

oehrpy was built to close this gap as part of the [Open CIS](https://medium.com/@platzh1rsch/building-open-cis-part-4-the-openehr-sdk-landscape-1b93411ec279) project.

## Project History

oehrpy started in January 2026 as part of the Open CIS project — an initiative to build open-source clinical information systems using openEHR standards. The SDK was designed from the ground up to be:

- **Generated, not hand-written** — RM classes are generated from official openEHR specifications
- **Type-safe** — Pydantic v2 validation catches errors at construction time
- **Template-aware** — OPT files are parsed to generate template-specific builders
- **Modern Python** — Targets Python 3.10+ with modern type hints and async support

## License

oehrpy is released under the [MIT License](https://github.com/platzhersh/oehrpy/blob/main/LICENSE).

Copyright 2026 Open CIS Project.
