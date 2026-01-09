"""
Template-specific composition builders.

This module provides type-safe builder classes for common openEHR templates,
eliminating the need for manual FLAT format path construction.

Example:
    >>> builder = VitalSignsBuilder(composer_name="Dr. Smith")
    >>> builder.add_blood_pressure(systolic=120, diastolic=80)
    >>> builder.add_pulse(rate=72)
    >>> flat_data = builder.build()
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from ..serialization.flat import FlatBuilder


@dataclass
class QuantityValue:
    """Represents a DV_QUANTITY value with magnitude and unit."""

    magnitude: float
    unit: str
    precision: int | None = None

    def to_flat(self, base_path: str) -> dict[str, Any]:
        """Convert to FLAT format entries."""
        result = {
            f"{base_path}|magnitude": self.magnitude,
            f"{base_path}|unit": self.unit,
        }
        if self.precision is not None:
            result[f"{base_path}|precision"] = self.precision
        return result


@dataclass
class CodedValue:
    """Represents a DV_CODED_TEXT value."""

    value: str
    code: str
    terminology: str = "local"

    def to_flat(self, base_path: str) -> dict[str, Any]:
        """Convert to FLAT format entries."""
        return {
            f"{base_path}|value": self.value,
            f"{base_path}|code": self.code,
            f"{base_path}|terminology": self.terminology,
        }


class TemplateBuilder:
    """Base class for template-specific builders.

    Subclasses should define the template_id and provide
    domain-specific methods for adding content.
    """

    template_id: str = ""

    def __init__(
        self,
        composer_name: str | None = None,
        language: str = "en",
        territory: str = "US",
    ):
        """Initialize the builder.

        Args:
            composer_name: Name of the composition author.
            language: Language code (default: "en").
            territory: Territory code (default: "US").
        """
        self._flat = FlatBuilder()
        self._flat.context(
            language=language,
            territory=territory,
            composer_name=composer_name,
        )
        self._event_counters: dict[str, int] = {}

    def _next_event_index(self, observation: str) -> int:
        """Get the next event index for an observation."""
        current = self._event_counters.get(observation, 0)
        self._event_counters[observation] = current + 1
        return current

    def set(self, path: str, value: Any) -> TemplateBuilder:
        """Set a raw value at the given path."""
        self._flat.set(path, value)
        return self

    def build(self) -> dict[str, Any]:
        """Build the FLAT format composition."""
        return self._flat.build()


@dataclass
class BloodPressureReading:
    """Blood pressure measurement data."""

    systolic: float
    diastolic: float
    time: datetime | str | None = None
    position: str | None = None  # e.g., "sitting", "standing", "lying"
    cuff_size: str | None = None
    location: str | None = None  # e.g., "left arm", "right arm"


@dataclass
class PulseReading:
    """Pulse/heart rate measurement data."""

    rate: float
    time: datetime | str | None = None
    regularity: str | None = None
    position: str | None = None


@dataclass
class BodyTemperatureReading:
    """Body temperature measurement data."""

    temperature: float
    unit: str = "Cel"  # Celsius
    time: datetime | str | None = None
    site: str | None = None  # e.g., "oral", "axillary", "ear"


@dataclass
class RespirationReading:
    """Respiration measurement data."""

    rate: float
    time: datetime | str | None = None
    regularity: str | None = None


@dataclass
class OxygenSaturationReading:
    """Oxygen saturation (SpO2) measurement data."""

    spo2: float
    time: datetime | str | None = None
    supplemental_oxygen: bool = False


class VitalSignsBuilder(TemplateBuilder):
    """Builder for IDCR Vital Signs Encounter template.

    This builder provides a type-safe interface for creating vital signs
    compositions without needing to know the FLAT path structure.

    Example:
        >>> builder = VitalSignsBuilder(composer_name="Dr. Smith")
        >>> builder.add_blood_pressure(systolic=120, diastolic=80)
        >>> builder.add_pulse(rate=72)
        >>> builder.add_temperature(37.0)
        >>> builder.add_respiration(rate=16)
        >>> builder.add_oxygen_saturation(spo2=98)
        >>> flat_data = builder.build()
    """

    template_id = "IDCR - Vital Signs Encounter.v1"

    # FLAT path prefixes for each observation type
    # Based on the Web Template from EHRBase 2.26.0
    # The template structure is: COMPOSITION > content[SECTION.vital_signs] > items[OBSERVATION.*]
    # In FLAT format: vital_signs/observation_id:0/event:0/element
    # Note: observation IDs come from the web template 'id' fields
    _BP_PREFIX = "vital_signs/blood_pressure"
    _PULSE_PREFIX = "vital_signs/pulse_heart_beat"
    _TEMP_PREFIX = "vital_signs/body_temperature"
    _RESP_PREFIX = "vital_signs/respirations"
    _SPO2_PREFIX = "vital_signs/indirect_oximetry"

    def add_blood_pressure(
        self,
        systolic: float,
        diastolic: float,
        time: datetime | str | None = None,
        position: str | None = None,
        cuff_size: str | None = None,
        location: str | None = None,
        event_index: int | None = None,
    ) -> VitalSignsBuilder:
        """Add a blood pressure reading.

        Args:
            systolic: Systolic pressure in mmHg.
            diastolic: Diastolic pressure in mmHg.
            time: Measurement time (defaults to now).
            position: Patient position (sitting, standing, lying).
            cuff_size: Cuff size used.
            location: Measurement location (left arm, right arm).
            event_index: Optional specific event index.

        Returns:
            Self for method chaining.
        """
        if event_index is None:
            event_index = self._next_event_index("blood_pressure")

        prefix = f"{self._BP_PREFIX}:{event_index}/any_event:{event_index}"

        # Set time
        time_str = self._format_time(time)
        self._flat.set(f"{prefix}/time", time_str)

        # Set measurements
        self._flat.set_quantity(f"{prefix}/systolic", systolic, "mm[Hg]")
        self._flat.set_quantity(f"{prefix}/diastolic", diastolic, "mm[Hg]")

        # Optional fields
        if position:
            self._flat.set(f"{prefix}/position|value", position)
        if cuff_size:
            self._flat.set(f"{prefix}/cuff_size|value", cuff_size)
        if location:
            self._flat.set(f"{prefix}/location_of_measurement|value", location)

        return self

    def add_pulse(
        self,
        rate: float,
        time: datetime | str | None = None,
        regularity: str | None = None,
        position: str | None = None,
        event_index: int | None = None,
    ) -> VitalSignsBuilder:
        """Add a pulse/heart rate reading.

        Args:
            rate: Heart rate in beats per minute.
            time: Measurement time (defaults to now).
            regularity: Pulse regularity (regular, irregular).
            position: Patient position.
            event_index: Optional specific event index.

        Returns:
            Self for method chaining.
        """
        if event_index is None:
            event_index = self._next_event_index("pulse")

        prefix = f"{self._PULSE_PREFIX}:{event_index}/any_event:{event_index}"

        time_str = self._format_time(time)
        self._flat.set(f"{prefix}/time", time_str)
        self._flat.set_quantity(f"{prefix}/heart_rate", rate, "/min")

        if regularity:
            self._flat.set(f"{prefix}/regularity|value", regularity)
        if position:
            self._flat.set(f"{prefix}/position|value", position)

        return self

    def add_temperature(
        self,
        temperature: float,
        unit: str = "Cel",
        time: datetime | str | None = None,
        site: str | None = None,
        event_index: int | None = None,
    ) -> VitalSignsBuilder:
        """Add a body temperature reading.

        Args:
            temperature: Temperature value.
            unit: Temperature unit (Cel or [degF]).
            time: Measurement time.
            site: Measurement site (oral, axillary, ear, rectal).
            event_index: Optional specific event index.

        Returns:
            Self for method chaining.
        """
        if event_index is None:
            event_index = self._next_event_index("temperature")

        prefix = f"{self._TEMP_PREFIX}:{event_index}/any_event:{event_index}"

        time_str = self._format_time(time)
        self._flat.set(f"{prefix}/time", time_str)
        self._flat.set_quantity(f"{prefix}/temperature", temperature, unit)

        if site:
            self._flat.set(f"{prefix}/site_of_measurement|value", site)

        return self

    def add_respiration(
        self,
        rate: float,
        time: datetime | str | None = None,
        regularity: str | None = None,
        event_index: int | None = None,
    ) -> VitalSignsBuilder:
        """Add a respiration rate reading.

        Args:
            rate: Respiratory rate in breaths per minute.
            time: Measurement time.
            regularity: Breathing regularity.
            event_index: Optional specific event index.

        Returns:
            Self for method chaining.
        """
        if event_index is None:
            event_index = self._next_event_index("respiration")

        prefix = f"{self._RESP_PREFIX}:{event_index}/any_event:{event_index}"

        time_str = self._format_time(time)
        self._flat.set(f"{prefix}/time", time_str)
        self._flat.set_quantity(f"{prefix}/rate", rate, "/min")

        if regularity:
            self._flat.set(f"{prefix}/regularity|value", regularity)

        return self

    def add_oxygen_saturation(
        self,
        spo2: float,
        time: datetime | str | None = None,
        supplemental_oxygen: bool = False,
        event_index: int | None = None,
    ) -> VitalSignsBuilder:
        """Add an oxygen saturation (SpO2) reading.

        Args:
            spo2: Oxygen saturation percentage.
            time: Measurement time.
            supplemental_oxygen: Whether patient is on supplemental O2.
            event_index: Optional specific event index.

        Returns:
            Self for method chaining.
        """
        if event_index is None:
            event_index = self._next_event_index("spo2")

        prefix = f"{self._SPO2_PREFIX}:{event_index}/any_event:{event_index}"

        time_str = self._format_time(time)
        self._flat.set(f"{prefix}/time", time_str)
        self._flat.set_quantity(f"{prefix}/spo2", spo2, "%")

        if supplemental_oxygen:
            self._flat.set_coded_text(
                f"{prefix}/inspired_oxygen/on_air",
                value="Supplemental oxygen",
                code="at0054",
                terminology="local",
            )

        return self

    def add_all_vitals(
        self,
        systolic: float | None = None,
        diastolic: float | None = None,
        pulse: float | None = None,
        temperature: float | None = None,
        respiration: float | None = None,
        spo2: float | None = None,
        time: datetime | str | None = None,
    ) -> VitalSignsBuilder:
        """Add all vital signs at once.

        Args:
            systolic: Systolic blood pressure in mmHg.
            diastolic: Diastolic blood pressure in mmHg.
            pulse: Heart rate in bpm.
            temperature: Body temperature in Celsius.
            respiration: Respiratory rate in breaths/min.
            spo2: Oxygen saturation percentage.
            time: Common measurement time for all readings.

        Returns:
            Self for method chaining.
        """
        if systolic is not None and diastolic is not None:
            self.add_blood_pressure(systolic, diastolic, time=time)
        if pulse is not None:
            self.add_pulse(pulse, time=time)
        if temperature is not None:
            self.add_temperature(temperature, time=time)
        if respiration is not None:
            self.add_respiration(respiration, time=time)
        if spo2 is not None:
            self.add_oxygen_saturation(spo2, time=time)

        return self

    def _format_time(self, time: datetime | str | None) -> str:
        """Format time for FLAT format.

        Returns an ISO 8601 formatted string with timezone info.
        If no time is provided, uses the current UTC time.
        Naive datetimes are assumed to be UTC.
        """
        if time is None:
            return datetime.now(timezone.utc).isoformat()
        if isinstance(time, datetime):
            if time.tzinfo is None:
                # Assume naive datetime is UTC
                time = time.replace(tzinfo=timezone.utc)
            return time.isoformat()
        return time
