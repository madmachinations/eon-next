#!/usr/bin/env python3

import logging
from homeassistant.util import dt as dt_util

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity
)

from homeassistant.const import (
    UnitOfEnergy,
    UnitOfVolume
)

from . import DOMAIN
from .eonnext import METER_TYPE_GAS, METER_TYPE_ELECTRIC, METER_TYPE_EV
from .tariff_patterns import get_tariff_pattern, get_current_rate_index, get_current_period_name

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
        
        for charger in account.ev_chargers:
            entities.append(SmartChargingScheduleSensor(charger))
            entities.append(NextChargeStartSensor(charger))
            entities.append(NextChargeEndSensor(charger))
            entities.append(NextChargeStartSensor2(charger))
            entities.append(NextChargeEndSensor2(charger))
        
        # Add tariff sensors for the account
        if account.tariff_data:
            entities.append(TariffNameSensor(account))
            entities.append(StandingChargeSensor(account))
            entities.append(UnitRateSensor(account))
        
        # Add saving session sensors
        if account.saving_sessions:
            entities.append(SavingSessionsSensor(account))
        
        # Add billing sensors
        entities.append(BillingHistorySensor(account))

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


class SmartChargingScheduleSensor(SensorEntity):
    """Smart Charging Schedule"""

    def __init__(self, charger):
        self.charger = charger

        self._attr_name = self.charger.get_serial() + " Smart Charging Schedule"
        self._attr_icon = "mdi:ev-station"
        self._attr_unique_id = self.charger.get_serial() + "__" + "smart_charging_schedule"
        self._attr_extra_state_attributes = {}
    

    async def async_update(self) -> None:
        schedule = await self.charger.get_schedule()
        if schedule is not None:
            if len(schedule) > 0:
                self._attr_native_value = "Active"
                self._attr_extra_state_attributes["schedule"] = schedule
            else:
                self._attr_native_value = "No Schedule"
                self._attr_extra_state_attributes["schedule"] = []
        else:
            self._attr_native_value = "Unknown"


class NextChargeStartSensor(SensorEntity):
    """Start time of next charge"""

    def __init__(self, charger):
        self.charger = charger

        self._attr_name = self.charger.get_serial() + " Next Charge Start"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-start"
        self._attr_unique_id = self.charger.get_serial() + "__" + "next_charge_start"
    

    async def async_update(self) -> None:
        schedule = await self.charger.get_schedule()
        if schedule and len(schedule) > 0:
            self._attr_native_value = dt_util.parse_datetime(schedule[0]['start'])
        else:
            self._attr_native_value = None


class NextChargeEndSensor(SensorEntity):
    """End time of next charge"""

    def __init__(self, charger):
        self.charger = charger

        self._attr_name = self.charger.get_serial() + " Next Charge End"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-end"
        self._attr_unique_id = self.charger.get_serial() + "__" + "next_charge_end"
    

    async def async_update(self) -> None:
        schedule = await self.charger.get_schedule()
        if schedule and len(schedule) > 0:
            self._attr_native_value = dt_util.parse_datetime(schedule[0]['end'])
        else:
            self._attr_native_value = None


class NextChargeStartSensor2(SensorEntity):
    """Start time of next charge slot 2"""

    def __init__(self, charger):
        self.charger = charger

        self._attr_name = self.charger.get_serial() + " Next Charge Start 2"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-start"
        self._attr_unique_id = self.charger.get_serial() + "__" + "next_charge_start_2"
    

    async def async_update(self) -> None:
        schedule = await self.charger.get_schedule()
        if schedule and len(schedule) > 1:
            self._attr_native_value = dt_util.parse_datetime(schedule[1]['start'])
        else:
            self._attr_native_value = None


class NextChargeEndSensor2(SensorEntity):
    """End time of next charge slot 2"""

    def __init__(self, charger):
        self.charger = charger

        self._attr_name = self.charger.get_serial() + " Next Charge End 2"
        self._attr_device_class = SensorDeviceClass.TIMESTAMP
        self._attr_icon = "mdi:clock-end"
        self._attr_unique_id = self.charger.get_serial() + "__" + "next_charge_end_2"
    

    async def async_update(self) -> None:
        schedule = await self.charger.get_schedule()
        if schedule and len(schedule) > 1:
            self._attr_native_value = dt_util.parse_datetime(schedule[1]['end'])
        else:
            self._attr_native_value = None


class TariffNameSensor(SensorEntity):
    """Active tariff name for the account"""

    def __init__(self, account):
        self.account = account

        self._attr_name = f"Account {self.account.account_number} Tariff Name"
        self._attr_icon = "mdi:file-document-outline"
        self._attr_unique_id = f"{self.account.account_number}__tariff_name"
    

    async def async_update(self) -> None:
        await self.account._load_tariff_data()
        if self.account.tariff_data and len(self.account.tariff_data) > 0:
            # Get the most recent active agreement
            active = [a for a in self.account.tariff_data if not a.get('validTo') or dt_util.parse_datetime(a['validTo']) > dt_util.now()]
            if active:
                tariff = active[0].get('tariff', {})
                self._attr_native_value = tariff.get('displayName') or tariff.get('fullName')
                self._attr_extra_state_attributes = {
                    "tariff_code": tariff.get('tariffCode'),
                    "valid_from": active[0].get('validFrom'),
                    "valid_to": active[0].get('validTo')
                }
            else:
                self._attr_native_value = None
        else:
            self._attr_native_value = None


class StandingChargeSensor(SensorEntity):
    """Daily standing charge for the account"""

    def __init__(self, account):
        self.account = account

        self._attr_name = f"Account {self.account.account_number} Standing Charge"
        self._attr_icon = "mdi:currency-gbp"
        self._attr_unit_of_measurement = "GBP/day"
        self._attr_unique_id = f"{self.account.account_number}__standing_charge"
    

    async def async_update(self) -> None:
        await self.account._load_tariff_data()
        if self.account.tariff_data and len(self.account.tariff_data) > 0:
            active = [a for a in self.account.tariff_data if not a.get('validTo') or dt_util.parse_datetime(a['validTo']) > dt_util.now()]
            if active:
                tariff = active[0].get('tariff', {})
                standing_charge = tariff.get('standingCharge')
                if standing_charge is not None:
                    # Convert pence to pounds
                    self._attr_native_value = round(standing_charge / 100, 4)
                else:
                    self._attr_native_value = None
            else:
                self._attr_native_value = None
        else:
            self._attr_native_value = None


class UnitRateSensor(SensorEntity):
    """Unit rate for the account"""

    def __init__(self, account):
        self.account = account

        self._attr_name = f"Account {self.account.account_number} Unit Rate"
        self._attr_icon = "mdi:currency-gbp"
        self._attr_unit_of_measurement = "GBP/kWh"
        self._attr_unique_id = f"{self.account.account_number}__unit_rate"
        self._attr_extra_state_attributes = {}
    

    async def async_update(self) -> None:
        await self.account._load_tariff_data()
        
         # Check for active EV charger schedules
        ev_charger_active = False
        if self.account.ev_chargers:
            now = dt_util.now()
            for charger in self.account.ev_chargers:
                schedule = await charger.get_schedule()
                if schedule:
                    for dispatch in schedule:
                        start = dt_util.parse_datetime(dispatch.get('start'))
                        end = dt_util.parse_datetime(dispatch.get('end'))
                        if start and end and start <= now <= end:
                            ev_charger_active = True
                            break
                if ev_charger_active:
                    break
        
        if self.account.tariff_data and len(self.account.tariff_data) > 0:
            active = [a for a in self.account.tariff_data if not a.get('validTo') or dt_util.parse_datetime(a['validTo']) > dt_util.now()]
            if active:
                tariff = active[0].get('tariff', {})
                unit_rate = tariff.get('unitRate')
                
                 # Handle HalfHourlyTariff with multiple rates
                if unit_rate is None and tariff.get('unitRates'):
                    rates = tariff.get('unitRates')
                    unique_rates = sorted(list(set([r['value'] for r in rates])))
                    now = dt_util.now()
                    
                     # If EV charger is active, use the lower (off-peak) rate
                    if ev_charger_active and len(unique_rates) >= 2:
                        unit_rate = unique_rates[0]   # Lower rate
                        self._attr_extra_state_attributes = {
                             "meter_point": active[0].get('meterPoint', {}).get('mpan') or active[0].get('meterPoint', {}).get('mprn'),
                             "all_rates_p": unique_rates,
                             "current_period": "Charging (Off-Peak Rate Applied)",
                             "low_rate": round(unique_rates[0] / 100, 4),
                             "high_rate": round(unique_rates[-1] / 100, 4),
                             "rate_slots": len(rates),
                             "charging_active": True,
                             "using_off_peak_rate": True
                         }
                    else:
                         # Try to get tariff pattern for time-based rate selection
                        tariff_name = tariff.get('displayName') or tariff.get('fullName') or ''
                        pattern = get_tariff_pattern(tariff_name)
                        
                        if len(rates) == 48:
                             # 48-slot half-hourly tariff — index directly from current time
                            slot = now.hour * 2 + (1 if now.minute >= 30 else 0)
                            unit_rate = rates[slot]['value']
                            
                            self._attr_extra_state_attributes = {
                                 "meter_point": active[0].get('meterPoint', {}).get('mpan') or active[0].get('meterPoint', {}).get('mprn'),
                                 "all_rates_p": unique_rates,
                                 "current_slot": slot,
                                 "rate_slots": len(rates)
                             }
                        elif len(rates) == 2 and pattern:
                             # 2-rate tariff with known pattern (e.g., Next Drive, Economy 7)
                            rate_index = get_current_rate_index(pattern, now.hour)
                            unit_rate = rates[rate_index]['value']
                            
                            low_rate = unique_rates[0]
                            high_rate = unique_rates[-1]
                            current_period = get_current_period_name(pattern, now.hour)
                            
                            off_peak_str, peak_str = self._get_period_hours(pattern)
                            
                            self._attr_extra_state_attributes = {
                                 "meter_point": active[0].get('meterPoint', {}).get('mpan') or active[0].get('meterPoint', {}).get('mprn'),
                                 "all_rates_p": unique_rates,
                                 "current_period": current_period,
                                 "low_rate": round(low_rate / 100, 4),
                                 "high_rate": round(high_rate / 100, 4),
                                 "rate_slots": len(rates),
                                 "off_peak_hours": off_peak_str,
                                 "peak_hours": peak_str,
                                 "tariff_pattern": pattern.get('description', tariff_name)
                             }
                        elif len(rates) > 0:
                             # Fallback: use first rate for unknown multi-rate tariffs
                            unit_rate = rates[0]['value']
                            
                            low_rate = unique_rates[0]
                            high_rate = unique_rates[-1]
                            current_period = "Unknown"
                            
                            self._attr_extra_state_attributes = {
                                 "meter_point": active[0].get('meterPoint', {}).get('mpan') or active[0].get('meterPoint', {}).get('mprn'),
                                 "all_rates_p": unique_rates,
                                 "current_period": current_period,
                                 "low_rate": round(low_rate / 100, 4),
                                 "high_rate": round(high_rate / 100, 4),
                                 "rate_slots": len(rates),
                                 "warning": "Time-based rate selection not configured for this tariff"
                             }
                    # Convert pence to pounds
                    self._attr_native_value = round(unit_rate / 100, 4)
                    if not self._attr_extra_state_attributes:
                        self._attr_extra_state_attributes = {
                            "meter_point": active[0].get('meterPoint', {}).get('mpan') or active[0].get('meterPoint', {}).get('mprn')
                        }
                else:
                    self._attr_native_value = None
            else:
                self._attr_native_value = None
        else:
            self._attr_native_value = None


class SavingSessionsSensor(SensorEntity):
    """Upcoming and active saving sessions"""

    def __init__(self, account):
        self.account = account

        self._attr_name = f"Account {self.account.account_number} Saving Sessions"
        self._attr_icon = "mdi:piggy-bank-outline"
        self._attr_unique_id = f"{self.account.account_number}__saving_sessions"
    

    async def async_update(self) -> None:
        await self.account._load_saving_sessions()
        if self.account.saving_sessions:
            # Count active/upcoming sessions
            now = dt_util.now()
            upcoming = []
            active = []
            
            for s in self.account.saving_sessions:
                start_str = s.get('startedAt') or s.get('startAt')
                end_str = s.get('endedAt') or s.get('endAt')
                
                if start_str:
                    start_dt = dt_util.parse_datetime(start_str)
                    if start_dt > now:
                        upcoming.append(s)
                    elif end_str:
                        end_dt = dt_util.parse_datetime(end_str)
                        if start_dt <= now <= end_dt:
                            active.append(s)

            self._attr_native_value = len(upcoming) + len(active)
            self._attr_extra_state_attributes = {
                "active_count": len(active),
                "upcoming_count": len(upcoming),
                "sessions": [
                    {
                        "id": s.get('id'),
                        "start": s.get('startedAt') or s.get('startAt'),
                        "type": s.get('type')
                    }
                    for s in self.account.saving_sessions
                ]
            }
        else:
            self._attr_native_value = 0
            self._attr_extra_state_attributes = {
                "active_count": 0,
                "upcoming_count": 0,
                "sessions": []
            }


class BillingHistorySensor(SensorEntity):
    """Latest bill information for the account"""

    def __init__(self, account):
        self.account = account

        self._attr_name = f"Account {self.account.account_number} Latest Bill"
        self._attr_icon = "mdi:receipt"
        self._attr_unit_of_measurement = "GBP"
        self._attr_unique_id = f"{self.account.account_number}__latest_bill"
    

    async def async_update(self) -> None:
        await self.account._load_billing_data()
        if self.account.billing_data and len(self.account.billing_data) > 0:
            # Get the most recent bill
            latest_bill = sorted(self.account.billing_data, key=lambda x: x.get('billDate'), reverse=True)[0]
            self._attr_native_value = latest_bill.get('amount', 0) / 100  # Convert pence to pounds
            self._attr_extra_state_attributes = {
                "bill_date": latest_bill.get('billDate'),
                "due_date": latest_bill.get('dueDate'),
                "status": latest_bill.get('status'),
                "bill_id": latest_bill.get('id')
            }
        else:
            self._attr_native_value = None
