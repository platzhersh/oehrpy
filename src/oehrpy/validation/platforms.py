"""Platform dialect configuration for EHRBase and Better."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

PlatformType = Literal["ehrbase", "better"]


@dataclass(frozen=True)
class PlatformDialect:
    """Configuration for a specific CDR platform's FLAT format dialect."""

    name: PlatformType
    uses_index_notation: bool
    includes_any_event: bool
    index_single_occurrence: bool

    @property
    def description(self) -> str:
        parts: list[str] = []
        if self.uses_index_notation:
            parts.append(":0 indexing on all nodes")
        else:
            parts.append("no :0 indexing on single-occurrence")
        if self.includes_any_event:
            parts.append("/any_event/ nodes included")
        else:
            parts.append("no /any_event/ intermediate nodes")
        return "; ".join(parts)


EHRBASE_DIALECT = PlatformDialect(
    name="ehrbase",
    uses_index_notation=False,
    includes_any_event=False,
    index_single_occurrence=False,
)

BETTER_DIALECT = PlatformDialect(
    name="better",
    uses_index_notation=True,
    includes_any_event=True,
    index_single_occurrence=True,
)

DIALECTS: dict[PlatformType, PlatformDialect] = {
    "ehrbase": EHRBASE_DIALECT,
    "better": BETTER_DIALECT,
}


def get_dialect(platform: PlatformType) -> PlatformDialect:
    """Get the dialect configuration for a platform."""
    return DIALECTS[platform]
