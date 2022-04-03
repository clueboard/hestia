"""Pure MQTT based thermostat.
"""
from os import environ
from statistics import mean
from time import time
from threading import Lock

from gourd import Gourd

MQTT_CLIENT_ID = environ.get('MQTT_CLIENT_ID', 'hestia')
MQTT_USER = environ.get('MQTT_USER', '')
MQTT_PASS = environ.get('MQTT_PASSWD', '')
MQTT_HOST = environ.get('MQTT_HOST', 'localhost')
MQTT_PORT = int(environ.get('MQTT_PORT', '1883'))
MQTT_QOS = int(environ.get('MQTT_QOS', 1))
MQTT_TIMEOUT = int(environ.get('MQTT_TIMEOUT', '30'))
MQTT_BASE_TOPIC = environ.get('MQTT_BASE_TOPIC', 'heater')

# Info about what to set everything to
DEDUPE_TIME = float(environ.get('DEDUPE_TIME', '5'))
TEMP_PROBE = environ.get('TEMP_PROBE', 'office_sensor/sensor/office_temperature/state')
TEMP_DESIRED = float(environ.get('TEMP_DESIRED', '21'))
TEMP_VARIANCE = float(environ.get('TEMP_VARIANCE', '1'))
HEATER_NAME = environ.get('HEATER_NAME', 'office_heater')
HEATER_SWITCH = environ.get('HEATER_SWITCH', 'zwave/Office/OfficeTubPlugs/37/2/targetValue/set')
HEATER_ON = environ.get('HEATER_ON', 'true')
HEATER_OFF = environ.get('HEATER_OFF', 'false')

# Build our list of topics
MQTT_TOPIC = '/'.join((MQTT_BASE_TOPIC, HEATER_NAME))
MQTT_SET_TOPIC = '/'.join((MQTT_TOPIC, 'set'))

# State tracking
heater_state = {
    'active': True,
    'last_received': 0,
    'lock': Lock(),
    'readings': [],
    'target': TEMP_DESIRED
}

app = Gourd(app_name='hestia', mqtt_host=MQTT_HOST, mqtt_port=MQTT_PORT, username=MQTT_USER, password=MQTT_PASS, timeout=MQTT_TIMEOUT)


@app.subscribe(MQTT_SET_TOPIC)
def set_topic(msg):
    if msg.payload.lower() in ('on', 'off'):
        app.log.info('Turning heater %s...', msg.payload)
    else:
        app.log.info('Handle temperature setting here...')
    return


@app.subscribe(TEMP_PROBE)
def process_reading(msg):
    """Process a temperature report from our probe.

    Some temperature probes send multiple messages in case the transmission
    is garbled. Because of this we wait until sufficient time has passed
    before acting on a temperature reading. In practice this means that when
    a reading comes in we are actually acting on the last reading, which may
    be some time ago.
    """
    heater_state['lock'].acquire()

    try:
        # Dedupe messages
        if time() - heater_state['last_received'] > DEDUPE_TIME and heater_state['readings']:
            # Act upon the last message
            temperature = mean(heater_state['readings'])

            app.log.debug('Temperature reading: %s, Turn on < %s, Turn Off > %s', temperature, heater_state['target']-TEMP_VARIANCE, heater_state['target'])

            if temperature < heater_state['target'] - TEMP_VARIANCE:
                app.log.debug('Turning heater on.')
                app.publish(HEATER_SWITCH, HEATER_ON)
            elif temperature > heater_state['target']:
                app.log.debug('Turning heater off.')
                app.publish(HEATER_SWITCH, HEATER_OFF)

            heater_state['readings'] = []

        # Record reading
        try:
            app.log.debug('Processing message to %s: %s', msg.topic, msg.payload)
            msg.payload = msg.payload.decode('utf-8')
            reading = float(msg.payload)
        except ValueError:
            app.log.error('Invalid temperature: %s', msg.payload)
            return
        heater_state['last_received'] = time()
        heater_state['readings'].append(reading)

    except Exception as e:
        app.log.error('Uncaught exception: %s: %s', e.__class__.__name__, e)
        app.log.exception(e)

    finally:
        heater_state['lock'].release()


if __name__ == '__main__':
    app.run_forever()
