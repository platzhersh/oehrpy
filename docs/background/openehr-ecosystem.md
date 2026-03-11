# The openEHR Ecosystem

A brief introduction for developers new to openEHR.

## What is openEHR?

[openEHR](https://www.openehr.org/) is an open standard for electronic health records (EHR). It provides a vendor-neutral, interoperable framework for storing and querying clinical data.

The key innovation of openEHR is the **two-level modelling** approach:

1. **Reference Model (RM)** — A stable, generic information model that defines the building blocks (compositions, observations, data types, etc.)
2. **Archetypes & Templates** — Domain-specific constraints defined by clinicians, independent of software

This separation means the software layer (the RM) remains stable while clinical definitions can evolve without code changes.

## Key Concepts

### Reference Model (RM)

The RM defines ~134 types that form the structure of all clinical data:

- **Compositions** — The top-level container (like a clinical document)
- **Sections** — Organize content within a composition
- **Entries** — Clinical statements: Observations, Evaluations, Instructions, Actions
- **Data types** — DV_QUANTITY, DV_TEXT, DV_CODED_TEXT, DV_DATE_TIME, etc.

oehrpy provides Pydantic models for all of these.

### Archetypes

Archetypes are reusable, computable definitions of clinical concepts (e.g., "blood pressure", "medication order"). They are authored by domain experts and shared via the [Clinical Knowledge Manager (CKM)](https://ckm.openehr.org/).

### Templates

Templates combine and constrain archetypes for a specific use case (e.g., "Vital Signs Encounter" combines blood pressure, pulse, temperature, etc.). Templates are distributed as **OPT** (Operational Template) files.

oehrpy can parse OPT files and generate type-safe builder classes from them.

### Clinical Data Repositories (CDR)

A CDR is the database that stores openEHR data. [EHRBase](https://ehrbase.org/) is the leading open-source CDR, and oehrpy includes a client for it.

### AQL (Archetype Query Language)

AQL is the query language for openEHR. It's similar to SQL but navigates archetype paths instead of table columns:

```sql
SELECT c/uid/value, o/data[at0001]/events[at0006]/data[at0003]/items[at0004]/value/magnitude
FROM EHR e
CONTAINS COMPOSITION c
CONTAINS OBSERVATION o[openEHR-EHR-OBSERVATION.blood_pressure.v1]
WHERE e/ehr_id/value = :ehr_id
```

oehrpy's AQL builder helps construct these queries programmatically.

## Where oehrpy Fits

```
Clinical Knowledge Manager (CKM)
        │
        ▼ Archetypes + Templates (OPT)
┌───────────────────┐
│     oehrpy        │ ◄── Parse OPT, generate builders,
│  Python SDK       │     serialize to FLAT/canonical JSON,
│                   │     query via AQL
└───────┬───────────┘
        │ REST API
        ▼
┌───────────────────┐
│    EHRBase CDR    │ ◄── Stores & queries clinical data
└───────────────────┘
```

## Learn More

- [openEHR Specifications](https://specifications.openehr.org/)
- [EHRBase Documentation](https://docs.ehrbase.org/)
- [Clinical Knowledge Manager](https://ckm.openehr.org/)
- [Building Open CIS Part 4: The openEHR SDK Landscape](https://medium.com/@platzh1rsch/building-open-cis-part-4-the-openehr-sdk-landscape-1b93411ec279)
