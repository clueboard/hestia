# Hestia - An MQTT thermostat

Turn a device on or off based on the temperature of a sensor. Intended for
HVAC, space heaters, water heaters, and other devices that need temperature
control.

## MQTT Details

Given a base topic of "heater" and a heater name of "bedroom", you would end up with the following mqtt topics:

* `heater/bedroom/status` - ON or OFF, whether the heater process is listening
* `heater/bedroom/set` - Publish ON/OFF to toggle the heater on or off, publish an int/float to change the set point.
