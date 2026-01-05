# oehrpy - Python openEHR SDK

A Python SDK for openEHR that provides type-safe Reference Model (RM) classes and template-specific composition builders.

## Overview

This project aims to address the current gap in the openEHR ecosystem where no comprehensive, actively maintained Python SDK exists. It eliminates the need for developers to manually construct complex nested JSON structures when working with openEHR compositions.

## Features (Planned)

- **Type-safe RM Classes**: ~200 Pydantic models for all openEHR Reference Model 1.0.4 types
- **Template Builders**: Template-specific composition builders with IDE autocomplete support
- **Serialization**: Support for both canonical JSON and FLAT format (EHRBase)
- **REST Client**: Type-safe client for EHRBase operations

## Project Status

This project is currently in the planning phase. See [PRD-0000](docs/prd/PRD-0000-python-openehr-sdk.md) for the full product requirements document.

## Documentation

- [Product Requirements Documents](docs/prd/)
- [Architecture Decision Records](docs/adr/)

## License

TBD

## Contributing

Contributions are welcome! Please see the documentation for guidelines.
