#!/usr/bin/env python3

import logging

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity
)

from homeassistant.const import (
    UnitOfEnergy,
    UnitOfVolume
)

from . import DOMAIN
from .eonnext import METER_TYPE_GAS, METER_TYPE_ELECTRIC

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Setup sensors from a config entry created in the integrations UI."""

    api = hass.data[DOMAIN][config_entry.entry_id]

    entities = []
    for account in api.accounts:
        for meter in account.meters:
            if await meter.has_reading() == True:

                entities.append(LatestReadingDateSensor(meter))

                if meter.get_type() == METER_TYPE_ELECTRIC:
                    entities.append(LatestElectricKwhSensor(meter))
                
                if meter.get_type() == METER_TYPE_GAS:
                    entities.append(LatestGasCubicMetersSensor(meter))
                    entities.append(LatestGasKwhSensor(meter))

    async_add_entities(entities, update_before_add=True)



class LatestReadingDateSensor(SensorEntity):
    """Date of latest meter reading"""

    def __init__(self, meter):
        self.meter = meter

        self._attr_name = self.meter.get_serial() + " Reading Date"
        self._attr_device_class = SensorDeviceClass.DATE
        self._attr_icon = "mdi:calendar"
        self._attr_unique_id = self.meter.get_serial() + "__" + "reading_date"
    

    async def async_update(self) -> None:
        self._attr_native_value = await self.meter.get_latest_reading_date()



class LatestElectricKwhSensor(SensorEntity):
    """Latest electricity meter reading"""

    def __init__(self, meter):
        self.meter = meter

        self._attr_name = self.meter.get_serial() + " Electricity"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_state_class = "total"
        self._attr_icon = "mdi:meter-electric-outline"
        self._attr_unique_id = self.meter.get_serial() + "__" + "electricity_kwh"
    

    async def async_update(self) -> None:
        self._attr_native_value = await self.meter.get_latest_reading()



class LatestGasKwhSensor(SensorEntity):
    """Latest gas meter reading in kWh"""

    def __init__(self, meter):
        self.meter = meter

        self._attr_name = self.meter.get_serial() + " Gas kWh"
        self._attr_device_class = SensorDeviceClass.ENERGY
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_state_class = "total"
        self._attr_icon = "mdi:meter-gas-outline"
        self._attr_unique_id = self.meter.get_serial() + "__" + "gas_kwh"
    

    async def async_update(self) -> None:
        self._attr_native_value = await self.meter.get_latest_reading_kwh()



class LatestGasCubicMetersSensor(SensorEntity):
    """Latest gas meter reading in kWh"""

    def __init__(self, meter):
        self.meter = meter

        self._attr_name = self.meter.get_serial() + " Gas"
        self._attr_device_class = SensorDeviceClass.GAS
        self._attr_native_unit_of_measurement = UnitOfVolume.CUBIC_METERS
        self._attr_state_class = "total"
        self._attr_icon = "mdi:meter-gas-outline"
        self._attr_unique_id = self.meter.get_serial() + "__" + "gas_m3"
    

    async def async_update(self) -> None:
        self._attr_native_value = await self.meter.get_latest_reading()

