"""Pure MQTT based thermostat.
"""
from os import environ

mqtt_client_id = environ.get('MQTT_CLIENT_ID', 'hestia')
mqtt_user      = environ.get('MQTT_USER', '')
mqtt_pass      = environ.get('MQTT_PASSWD', '')
mqtt_host      = environ.get('MQTT_HOST', 'localhost')
mqtt_port      = int(environ.get('MQTT_PORT', '1883'))
mqtt_qos       = int(environ.get('MQTT_QOS', 1))
mqtt_timeout   = int(environ.get('MQTT_TIMEOUT', '30'))

# Basic Behavioral Configuration
dedupe_time         = float(environ.get('DEDUPE_TIME', '5'))      # In seconds, how long to wait for all messages to come in
default_target_temp = float(environ.get('TEMP_DESIRED', '20'))    # In celsius, the default setpoint, or at which temp the heater will turn off
temp_variance       = float(environ.get('TEMP_VARIANCE', '1'))    # AKA Swing, this is how many far below the setpoint the heater turns on
temp_min            = float(environ.get('TEMP_MIN', '2'))         # The lowest temperature this thermostat will control
temp_max            = float(environ.get('TEMP_MAX', '30'))        # The highest temperature this thermostat will control
payload_heater_on   = environ.get('PAYLOAD_HEATER_ON', 'true')    # The payload for the MQTT message to turn the heater switch on
payload_heater_off  = environ.get('PAYLOAD_HEATER_OFF', 'false')  # The payload for the MQTT message to turn the heater switch off

# Basic facts about this heater
heater_name          = environ.get('HEATER_NAME', 'office_heater')
topic_temp_probe     = environ.get('TOPIC_TEMP_PROBE', 'office_sensor/sensor/office_temperature/state')
topic_humidity_probe = environ.get('TOPIC_HUMIDITY_PROBE', 'office_sensor/sensor/office_humidity/state')
topic_heater_switch  = environ.get('TOPIC_HEATER_SWITCH', 'zwave/Office/OfficeTubPlugs/37/2/targetValue/set')

# Build our list of MQTT control topics
mqtt_base_topic          = environ.get('MQTT_BASE_TOPIC', 'hestia')
mqtt_heater_topic        = '/'.join((mqtt_base_topic, heater_name))
mqtt_state_topic         = '/'.join((mqtt_heater_topic, 'state'))          # Values can be OFF or HEAT
mqtt_target_temp_topic   = '/'.join((mqtt_heater_topic, 'target_C'))       # Target Temperature in Celsius
mqtt_current_temp_topic  = '/'.join((mqtt_heater_topic, 'current_C'))      # Current Temperature in Celsius
mqtt_current_humidity_topic  = '/'.join((mqtt_heater_topic, 'humidity'))   # Current Humidity
mqtt_display_units_topic = '/'.join((mqtt_heater_topic, 'display_units'))  # Temperature Display Units (?)
