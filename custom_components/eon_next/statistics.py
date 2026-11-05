"""Import E.ON Next interval consumption into long-term statistics."""

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
import logging
import math
import re

from homeassistant.components.recorder import get_instance
from homeassistant.components.recorder.models import (
    StatisticData,
    StatisticMeanType,
    StatisticMetaData,
)
from homeassistant.components.recorder.statistics import (
    async_add_external_statistics,
    get_last_statistics,
)
from homeassistant.const import UnitOfEnergy
from homeassistant.util.unit_conversion import EnergyConverter

_LOGGER = logging.getLogger(__name__)

DOMAIN = "eon_next"
BACKFILL_START = datetime(2000, 1, 1, tzinfo=timezone.utc)


def _statistic_id(meter) -> str:
    """Build a valid, stable external statistic ID."""
    serial = re.sub(r"[^a-z0-9_]", "_", meter.get_serial().lower())
    meter_type = re.sub(r"[^a-z0-9_]", "_", meter.get_type().lower())
    return f"{DOMAIN}:{serial}_{meter_type}_consumption"


def _hourly_consumption(records: list[dict]) -> dict[datetime, float]:
    """Aggregate half-hour records into UTC hours."""
    hourly = defaultdict(float)

    for record in records:
        start = datetime.fromisoformat(record["startAt"].replace("Z", "+00:00"))
        if start.tzinfo is None:
            raise ValueError("E.ON Next returned a naive consumption timestamp")
        value = float(record["value"])
        if not math.isfinite(value) or value < 0:
            _LOGGER.warning(
                "Ignoring invalid E.ON Next consumption value %s at %s",
                record["value"],
                record["startAt"],
            )
            continue
        hour = start.astimezone(timezone.utc).replace(
            minute=0, second=0, microsecond=0
        )
        hourly[hour] += value

    return dict(hourly)


class HistoricalConsumptionImporter:
    """Incrementally import consumption for every unique meter."""

    def __init__(self, hass, api):
        self.hass = hass
        self.api = api
        self._lock = asyncio.Lock()

    async def async_import(self) -> None:
        """Import any consumption newer than the last stored hour."""
        if self._lock.locked():
            _LOGGER.debug("E.ON Next history import is already running")
            return

        async with self._lock:
            seen_meters = set()
            for account in self.api.accounts:
                for meter in account.meters:
                    meter_key = (meter.get_type(), meter.get_serial())
                    if meter_key in seen_meters:
                        continue
                    seen_meters.add(meter_key)
                    await self._async_import_meter(meter)

    async def _async_import_meter(self, meter) -> None:
        statistic_id = _statistic_id(meter)
        last_start, last_state, running_sum = await self._async_last_statistic(
            statistic_id
        )
        query_start = last_start or BACKFILL_START
        records = await meter.get_consumption_data(
            query_start, datetime.now(timezone.utc)
        )
        hourly = _hourly_consumption(records)

        statistics = []
        for start, state in sorted(hourly.items()):
            if last_start is not None and start < last_start:
                continue
            if start == last_start:
                running_sum -= last_state
            running_sum += state
            statistics.append(
                StatisticData(start=start, state=state, sum=running_sum)
            )

        if not statistics:
            _LOGGER.debug("No new consumption for %s", statistic_id)
            return

        metadata = StatisticMetaData(
            mean_type=StatisticMeanType.NONE,
            has_sum=True,
            name=(
                f"E.ON Next {meter.get_serial()} "
                f"{meter.get_type()} consumption"
            ),
            source=DOMAIN,
            statistic_id=statistic_id,
            unit_class=EnergyConverter.UNIT_CLASS,
            unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        )
        async_add_external_statistics(self.hass, metadata, statistics)
        _LOGGER.info(
            "Imported %s hourly consumption records for %s",
            len(statistics),
            meter.get_serial(),
        )

    async def _async_last_statistic(
        self, statistic_id: str
    ) -> tuple[datetime | None, float, float]:
        last = await get_instance(self.hass).async_add_executor_job(
            get_last_statistics,
            self.hass,
            1,
            statistic_id,
            True,
            {"start", "state", "sum"},
        )
        if not last or not last.get(statistic_id):
            return None, 0.0, 0.0

        row = last[statistic_id][0]
        return (
            datetime.fromtimestamp(row["start"], tz=timezone.utc),
            float(row.get("state") or 0.0),
            float(row.get("sum") or 0.0),
        )