"""Pure MQTT based thermostat.
"""
from os import environ
from statistics import mean
from time import time
from threading import Lock

from gourd import Gourd

from hestia import config
from hestia.heater_state import get_heater_state

app = Gourd(app_name='hestia', mqtt_host=config.mqtt_host, mqtt_port=config.mqtt_port, username=config.mqtt_user, password=config.mqtt_pass, timeout=config.mqtt_timeout)

### mqttthing configuration
print(f"""Homebridge mqttthing configuration for this device:

{"{"}
    "accessory": "mqttthing",
    "type": "thermostat",
    "name": "{config.heater_name}",
    "topics":
    {"{"}
        "getCurrentHeatingCoolingState": "{config.mqtt_state_topic}",
        "setTargetHeatingCoolingState":  "{config.mqtt_state_topic}/set",
        "getTargetHeatingCoolingState":  "{config.mqtt_state_topic}",
        "getCurrentTemperature":         "{config.mqtt_current_temp_topic}",
        "setTargetTemperature":          "{config.mqtt_target_temp_topic}/set",
        "getTargetTemperature":          "{config.mqtt_target_temp_topic}",
        "setTemperatureDisplayUnits":    "{config.mqtt_display_units_topic}/set",
        "getTemperatureDisplayUnits":    "{config.mqtt_display_units_topic}",
        "getCurrentRelativeHumidity":    "{config.topic_humidity_probe}",
    {"}"},
    "minTemperature": config.temp_min,
    "maxTemperature": config.temp_max,
    "restrictHeatingCoolingState": [0, 1]
{"}"}
""")
### end mqttthing configuration


def payload_to_float(payload):
    """Convert a raw payload to float.
    """
    try:
        if hasattr(payload, 'decode'):
            payload = payload.decode('utf-8')

        temperature = float(payload)

    except ValueError:
        temperature = None

        app.log.error('Invalid temperature payload from MQTT: %s', payload)

    return temperature


@app.subscribe(config.topic_temp_probe)
def process_reading(msg):
    """Process a temperature report from our probe.

    Some temperature probes send multiple messages in case the transmission
    is garbled. Because of this we wait until sufficient time has passed
    before acting on a temperature reading. In practice this means that when
    a reading comes in we are actually acting on the last reading, which may
    be some time ago.

    This introduces some imprecision in terms of temperature variance and
    actual temperatures reached. You can turn the temp down a little bit to
    compensate as a cheap fix. If it bothers you I'd love to get a PR
    improving that.
    """
    heater_state = get_heater_state(app)

    app.log.debug('Processing message to %s: %s', msg.topic, msg.payload)

    try:
        # If this is the first message of a new burst, process the previous burst
        if heater_state.dedupe_complete:
            heater_action = heater_state.action()

            if heater_action:
                app.publish(config.topic_heater_switch, heater_action)

        # Record reading
        temperature = payload_to_float(msg.payload)
        heater_state.add_reading(temperature)

    except Exception as e:
        app.log.error('Uncaught exception: %s: %s', e.__class__.__name__, e)
        app.log.exception(e)
