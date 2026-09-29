"""End-to-end FLAT example: RM values -> FLAT -> POST to a CDR -> read back.

Prerequisites: a running CDR (``docker-compose up -d`` starts EHRBase on
http://localhost:8080/ehrbase). Run with::

    python examples/flat_end_to_end.py

The flow, and where each FLAT path comes from (ADR-0005):

1. Upload the OPT so the CDR knows the template.
2. Fetch the Web Template JSON -- the *only* authoritative source of FLAT paths.
3. Build the FLAT dict with ``FlatBuilder`` (no hand-written serializer or
   RM subclasses needed; RM values map onto ``|attribute`` suffixes).
4. POST it with ``format="FLAT"``.
"""

from __future__ import annotations

import asyncio
import os
from pathlib import Path

from oehrpy.client import EHRBaseClient
from oehrpy.rm import DV_QUANTITY
from oehrpy.serialization import FlatBuilder

OPT_PATH = Path(__file__).parent.parent / "tests" / "fixtures" / "vital_signs.opt"
TEMPLATE_ID = "IDCR - Vital Signs Encounter.v1"
PREFIX = "vital_signs_observations"  # root Web Template node id
BP = f"{PREFIX}/vital_signs/blood_pressure"


def build_flat() -> dict:
    # An RM value you already hold ...
    systolic = DV_QUANTITY(magnitude=120.0, units="mm[Hg]")
    diastolic = DV_QUANTITY(magnitude=80.0, units="mm[Hg]")

    # ... maps 1:1 onto FLAT: DV_QUANTITY -> <path>|magnitude + <path>|unit.
    builder = FlatBuilder(composition_prefix=PREFIX)
    builder.context(language="en", territory="US", composer_name="Dr. Smith")
    # Single-event history: the event collapses into the observation, so use
    # history_origin for the time (works on EHRBase and FerroEHR).
    builder.set(f"{BP}/history_origin", "2024-01-15T10:30:00Z")
    builder.set_quantity(f"{BP}/systolic", systolic.magnitude, systolic.units)
    builder.set_quantity(f"{BP}/diastolic", diastolic.magnitude, diastolic.units)
    # Required by EHRBase 2.26+ on each entry.
    builder.set(f"{BP}/language|terminology", "ISO_639-1")
    builder.set(f"{BP}/language|code", "en")
    builder.set(f"{BP}/encoding|terminology", "IANA_character-sets")
    builder.set(f"{BP}/encoding|code", "UTF-8")
    return builder.build()


async def main() -> None:
    async with EHRBaseClient(
        base_url=os.environ.get("EHRBASE_URL", "http://localhost:8080/ehrbase"),
        username=os.environ.get("EHRBASE_USER", "ehrbase-user"),
        password=os.environ.get("EHRBASE_PASSWORD", "SuperSecretPassword"),
    ) as client:
        try:
            await client.upload_template(OPT_PATH.read_text())
        except Exception as exc:  # already uploaded
            print(f"template upload skipped: {exc}")

        # Look up valid FLAT paths instead of guessing them.
        web_template = await client.get_web_template(TEMPLATE_ID)
        print("Web Template root id:", web_template["tree"]["id"])

        ehr = await client.create_ehr()
        flat = build_flat()
        result = await client.create_composition(
            ehr_id=ehr.ehr_id,
            composition=flat,
            template_id=TEMPLATE_ID,
            format="FLAT",
        )
        print("Created composition:", result.uid)

        stored = await client.get_composition(ehr.ehr_id, result.uid, format="FLAT")
        print("Read back:", stored.composition)


if __name__ == "__main__":
    asyncio.run(main())
