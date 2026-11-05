# Eon Next


THIS IS DEAD UNTIL I CAN WORK MY WAY AROUND LIMITATIONS EON HAVE PUT IN PLACE.

I CAN GET IT TO AUTHENTICATE, BUT THEY NOW FORCE YOU TO INSTALL THEIR SHIT FUCKING MOBILE APP TO ACCESS YOUR ENERGY USAGE. 
WEB WILL ONLY GIVE ACCESS TO MONTHLY METER READINGS.



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
