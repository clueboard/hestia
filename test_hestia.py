#!/usr/bin/env python3

import atexit
from os import environ
from subprocess import Popen
from time import sleep

from gourd import Gourd
from milc import cli

# Tweak the behavior of this script
MOSQUITTO_SLEEP_TIME=5
HESTIA_SLEEP_TIME=5

# Set some variables to control hestia's behavior
environ['DEDUPE_TIME'] = '0.5'
environ['HEATER_NAME'] = 'test_heater'
environ['MQTT_BASE_TOPIC'] = 'test_hestia'
environ['MQTT_CLIENT_ID'] = 'test_hestia'
environ['MQTT_USER'] = ''
environ['MQTT_PASSWD'] = ''
environ['MQTT_HOST'] = 'localhost'
environ['MQTT_PORT'] = '3883'
environ['MQTT_QOS'] = '1'
environ['MQTT_TIMEOUT'] = '30'
environ['PAYLOAD_HEATER_ON'] = 'HEATER_TURNS_ON'
environ['PAYLOAD_HEATER_OFF'] = 'HEATER_TURNS_OFF'
environ['TEMP_DESIRED'] = '20'
environ['TEMP_VARIANCE'] = '1'
environ['TEMP_MIN'] = '15'
environ['TEMP_MAX'] = '25'
environ['TOPIC_TEMP_PROBE'] = 'probe/temp'
environ['TOPIC_HUMIDITY_PROBE'] = 'probe/humidity'
environ['TOPIC_HEATER_SWITCH'] = 'switch/heater'

# Objects
app = Gourd(app_name='test_hestia_script', mqtt_host=environ['MQTT_HOST'], mqtt_port=int(environ['MQTT_PORT']), username=environ['MQTT_USER'], password=environ['MQTT_PASSWD'], timeout=int(environ['MQTT_TIMEOUT']))
mqtt_messages = {}  # {topic: payload}
processes = {}


@app.subscribe('#')
def mqtt_listen(msg):
    if not msg.topic.endswith('/debug'):
        cli.log.info('MQTT Message: %s: %s', msg.topic, msg.payload)
        mqtt_messages[msg.topic] = msg.payload


@atexit.register
def atexit_cleanup():
    """Cleanup background processes before exiting.
    """
    # Tell all processes to exit, in a nice way
    cli.log.info('Cleaning up background processes...')
    for process in processes.values():
        process.terminate()

    # Give them at least 5 seconds to stop
    for i in range(5):
        for process in processes.values():
            if process.poll() is None:
                sleep(1)

    # Tell any remaining processes to exit, non-politely
    for process_name, process in processes.items():
        if process.poll() is None:
            cli.log.error('%s did not terminate, killing...', processs_name.title())
            process.kill()


def check_procs():
    """Returns True if all background processes are running.
    """
    for process_name, process in processes.items():
        process_status = process.poll()
        if process_status is not None:
            cli.log.error('%s is no longer running! errno %s', process_name.title(), process_status)
            return False

    return True


def check_temps(temp_list, on_temps, off_temps):
    """Iterate through a list of temperatures and make sure the heater turns on and off as needed.
    """
    success = True

    for temp in temp_list:
        cli.log.info('Sending temperature %s', temp)
        app.publish(environ['TOPIC_TEMP_PROBE'], temp)
        sleep(0.6)

        if not check_procs():
            success = False
            break

        for switch_action, switch_temps in [['ON', on_temps], ['OFF', off_temps]]:
            if temp in switch_temps:
                if mqtt_messages.get(environ['TOPIC_HEATER_SWITCH']) == environ[f'PAYLOAD_HEATER_{switch_action}']:
                    cli.log.info('Sucessfully turned %s heater!', switch_action)
                else:
                    cli.log.error('Did not turn %s heater! TOPIC_HEATER_SWITCH=%s', switch_action, mqtt_messages.get(environ['TOPIC_HEATER_SWITCH']))
                    success = False

        if environ['TOPIC_HEATER_SWITCH'] in mqtt_messages:
            del mqtt_messages[environ['TOPIC_HEATER_SWITCH']]

    return success


@cli.entrypoint('Test hestia')
def main(cli):
    success = True

    # Start the daemons we'll need
    cli.log.info('Starting mosquitto in the background and waiting %s seconds for initialization', MOSQUITTO_SLEEP_TIME)
    args = 'mosquitto', '-c', './test_mosquitto.conf'
    processes['mosquitto'] = Popen(args)
    sleep(MOSQUITTO_SLEEP_TIME)

    cli.log.info('Starting MQTT listener and waiting %s seconds for initialization', MOSQUITTO_SLEEP_TIME)
    app.loop_start()
    sleep(MOSQUITTO_SLEEP_TIME)

    cli.log.info('Starting hestia in the background and waiting %s seconds for initialization', HESTIA_SLEEP_TIME)
    args = './run_hestia'
    processes['hestia'] = Popen(args)
    sleep(HESTIA_SLEEP_TIME)

    # Send temperature readings from the turn on point to the turn off point to test that hestia is working correctly
    if not check_temps([i/10 for i in range(188, 203)], [18.9, 19.0], [20.2]):
        success = False

    # Send temperature readings from the turn off point to the turn on point to test that hestia is working correctly
    if not check_temps([i/10 for i in range(202, 187, -1)], [18.8], [20.0, 20.1, 20.2]):
        success = False

    # Report status
    return success


if __name__ == '__main__':
    if cli():
        exit(0)
    exit(1)
