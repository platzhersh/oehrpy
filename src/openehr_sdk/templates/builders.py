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
        composition_prefix: str | None = None,
    ):
        """Initialize the builder.

        Args:
            composer_name: Name of the composition author.
            language: Language code (default: "en").
            territory: Territory code (default: "US").
            composition_prefix: Composition ID for EHRBase 2.26.0+.
                If None, uses "ctx" legacy format.
        """
        self._flat = FlatBuilder(composition_prefix=composition_prefix)
        self._flat.context(
            language=language,
            territory=territory,
            composer_name=composer_name,
        )
        self._event_counters: dict[str, int] = {}
        self._composition_prefix = composition_prefix

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
    unit: str = "°C"  # Celsius
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
    # The template structure is:
    #   COMPOSITION(vital_signs_observations) > SECTION(vital_signs) > OBSERVATION.*
    # In FLAT format (EHRBase 2.26.0+):
    #   composition_id/section_id/observation_id/element
    # NOTE: NO template ID prefix, NO :0 indices, NO /any_event:0/ paths
    # These IDs come from the web template 'id' fields
    _COMPOSITION_PREFIX = "vital_signs_observations"
    _BP_PREFIX = "vital_signs_observations/vital_signs/blood_pressure"
    _PULSE_PREFIX = "vital_signs_observations/vital_signs/pulse_heart_beat"
    _TEMP_PREFIX = "vital_signs_observations/vital_signs/body_temperature"
    _RESP_PREFIX = "vital_signs_observations/vital_signs/respirations"
    _SPO2_PREFIX = "vital_signs_observations/vital_signs/indirect_oximetry"

    def __init__(
        self,
        composer_name: str | None = None,
        language: str = "en",
        territory: str = "US",
    ):
        """Initialize the VitalSignsBuilder.

        Args:
            composer_name: Name of the composition author.
            language: Language code (default: "en").
            territory: Territory code (default: "US").
        """
        # Always use the composition prefix for EHRBase 2.26.0+ format
        super().__init__(
            composer_name=composer_name,
            language=language,
            territory=territory,
            composition_prefix=self._COMPOSITION_PREFIX,
        )

    def add_blood_pressure(
        self,
        systolic: float,
        diastolic: float,
        time: datetime | str | None = None,
        position: str | None = None,
        cuff_size: str | None = None,
        location: str | None = None,
    ) -> VitalSignsBuilder:
        """Add a blood pressure reading.

        Args:
            systolic: Systolic pressure in mmHg.
            diastolic: Diastolic pressure in mmHg.
            time: Measurement time (defaults to now).
            position: Patient position (sitting, standing, lying).
            cuff_size: Cuff size used.
            location: Measurement location (left arm, right arm).

        Returns:
            Self for method chaining.
        """
        prefix = self._BP_PREFIX

        # Set time
        time_str = self._format_time(time)
        self._flat.set(f"{prefix}/time", time_str)

        # Set measurements
        self._flat.set_quantity(f"{prefix}/systolic", systolic, "mm[Hg]")
        self._flat.set_quantity(f"{prefix}/diastolic", diastolic, "mm[Hg]")

        # Set language and encoding (required for EHRBase 2.26.0+)
        self._flat.set(f"{prefix}/language|terminology", "ISO_639-1")
        self._flat.set(f"{prefix}/language|code", "en")
        self._flat.set(f"{prefix}/encoding|terminology", "IANA_character-sets")
        self._flat.set(f"{prefix}/encoding|code", "UTF-8")

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
    ) -> VitalSignsBuilder:
        """Add a pulse/heart rate reading.

        Args:
            rate: Heart rate in beats per minute.
            time: Measurement time (defaults to now).
            regularity: Pulse regularity (regular, irregular).
            position: Patient position.

        Returns:
            Self for method chaining.
        """
        prefix = self._PULSE_PREFIX

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
        unit: str = "°C",
        time: datetime | str | None = None,
        site: str | None = None,
    ) -> VitalSignsBuilder:
        """Add a body temperature reading.

        Args:
            temperature: Temperature value.
            unit: Temperature unit (°C or °F).
            time: Measurement time.
            site: Measurement site (oral, axillary, ear, rectal).

        Returns:
            Self for method chaining.
        """
        prefix = self._TEMP_PREFIX

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
    ) -> VitalSignsBuilder:
        """Add a respiration rate reading.

        Args:
            rate: Respiratory rate in breaths per minute.
            time: Measurement time.
            regularity: Breathing regularity.

        Returns:
            Self for method chaining.
        """
        prefix = self._RESP_PREFIX

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
    ) -> VitalSignsBuilder:
        """Add an oxygen saturation (SpO2) reading.

        Args:
            spo2: Oxygen saturation percentage (0-100).
            time: Measurement time.
            supplemental_oxygen: Whether patient is on supplemental O2.

        Returns:
            Self for method chaining.
        """
        prefix = self._SPO2_PREFIX

        time_str = self._format_time(time)
        self._flat.set(f"{prefix}/time", time_str)
        # SpO2 is a DV_PROPORTION with fixed denominator of 100
        self._flat.set_proportion(f"{prefix}/spo2", numerator=spo2, denominator=100.0)

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
