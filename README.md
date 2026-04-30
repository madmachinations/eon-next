# Eon Next

This is a custom component for Home Assistant which integrates with the Eon Next API to retrieve meter readings and smart charging schedules from your Eon Next accounts.

## Features

### Meter Readings
A sensor will be created for each meter showing:

- **Latest Reading**: The most recent consumption value
- **Reading Date**: When the latest reading was taken

For electric meters, readings are displayed in kWh. For gas meters, readings are in m³.

An additional sensor is created for gas meters showing the latest reading converted to kWh using standard calorific values.

### Smart Charging (EV Chargers)
For each connected smart charger, the following sensors are created:

- **Next Charge Start**: Scheduled start time of the next charging slot
- **Next Charge End**: Scheduled end time of the next charging slot
- **Next Charge Start 2**: Scheduled start time of the second charging slot
- **Next Charge End 2**: Scheduled end time of the second charging slot
- **Smart Charging Schedule**: Full schedule data for the charger

These sensors allow you to monitor and automate your EV charging based on Eon Next's smart charging recommendations.

### Tariff Information
For each account, the following tariff sensors are created:

- **Tariff Name**: The display name of your active tariff
- **Standing Charge**: Daily standing charge in GBP/day
- **Unit Rate**: Energy unit rate in GBP/kWh

These sensors include additional attributes such as tariff code, valid dates, and meter point information.

### Saving Sessions
If your account participates in saving sessions (similar to Octopus Energy's scheme):

- **Saving Sessions**: Count of active and upcoming saving sessions, with full session details in attributes including start/end times, reward amounts, and session status


## Installation

Copy the `eon_next` folder to the `custom_components` folder inside your HA config directory. If a `custom_components` folder does not exist, just create it.

Next restart Home Assistant.

Setting up this component is done entirely in the UI. Go to your Integration settings, press to add a new integration, and find "Eon Next".

The setup wizard will ask you to enter your account login details, and that is all there is too it!

The integration should now be showing on your list, along with a number of new entities for all the sensors it has created.