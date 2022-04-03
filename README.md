# Hestia - An MQTT thermostat

Turn a device on or off based on the temperature of a sensor. Intended for
HVAC, space heaters, water heaters, and other devices that need temperature
control.

## MQTT Details

Given a base topic of "heater" and a heater name of "bedroom", you would end up with the following mqtt topics:

* `heater/bedroom/status` - ON or OFF, whether the heater process is listening
* `heater/bedroom/set` - Publish ON/OFF to toggle the heater on or off, publish an int/float to change the set point.

## Setup

Clone this repository into the location of your choosing.

Install the requirements using

    python3 -m pip install -U -r requirements.txt

## Running

Use gourd to run this:

    gourd hestia:app

### Systemd

There's a sample `hestia.service` file you can use as a starting point. Symlink or copy it into `/etc/systemd/system` and modify for your environment.

## Configuration

You can control the configuration using environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `MQTT_CLIENT_ID` | `hestia` | The client name to supply to the MQTT server. |
| `MQTT_USER` | `` | The username to authenticate to MQTT with. |
| `MQTT_PASS` | `` | The password to authenticate to MQTT with. |
| `MQTT_HOST` | `localhost` | The MQTT server to connect to. |
| `MQTT_PORT` | `1883` | The MQTT port number to connect to. |
| `MQTT_QOS | `1` | The default QOS value. |
| `MQTT_TIMEOUT` | `30` | The default timeout value. |
| `MQTT_BASE_TOPIC` | `heater` | The topic you want your thermostats to live under. |
| `DEDUPE_TIME` | `5` | Some sensors send multiple messages, this is how long we wait before considering it a new reading. |
| `TEMP_PROBE` | `office_sensor/sensor/office_temperature/state` | The MQTT topic where temperatures will be reported as bare floats. |
| `TEMP_DESIRED` | `21` | The target setpoint. |
| `TEMP_VARIANCE` | `1` | How much we allow the probe to cool before turning on again. |
| `HEATER_NAME` | `office_heater` | The name for this thermostat. |
| `HEATER_SWITCH` | `zwave/Office/OfficeTubPlugs/37/2/targetValue/set` | The MQTT topic we write to to turn the heater on or off. |
| `HEATER_ON` | `true` | The value to write to turn the heater on. |
| `HEATER_OFF` | `false` | The value to write to turn the heater off. |
