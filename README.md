# Eon Next

This is a custom component for Home Assistant which integrates with the Eon Next API and gets all the meter readings from your accounts.

A sensor will be created for each meter showing:

- The latest reading
- The date the latest reading was taken

For electric meters the readings are in kWh. For gas meter the readings are in m³.

An additional sensor is created for gas meters showing the latest reading in kWh.


## Installation

Copy the `eon_next` folder to the `custom_components` folder inside your HA config directory. If a `custom_components` folder does not exist, just create it.

Next restart Home Assistant.

Setting up this component is done entirely in the UI. Go to your Integration settings, press to add a new integration, and find "Eon Next".

The setup wizard will ask you to enter your account login details, and that is all there is too it!

The integration should now be showing on your list, along with a number of new entities for all the sensors it has created.