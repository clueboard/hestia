"""Pure MQTT based thermostat.
"""
from functools import lru_cache
from os import environ
from statistics import mean
from time import time
from threading import Lock

from gourd import Gourd

from hestia import config


@lru_cache(maxsize=None)
def get_heater_state(gourd_app):
    return HeaterState(gourd_app)


class HeaterState:
    """Track state for the heater, and report it to MQTT.
    """
    def __init__(self, gourd_app, logger=None, heater_switch=config.topic_heater_switch, active=True, last_received=0, lock=Lock(), readings=None, target=config.default_target_temp, state_topic=config.mqtt_state_topic, current_temp_topic=config.mqtt_current_temp_topic, target_temp_topic=config.mqtt_target_temp_topic, display_units_topic=config.mqtt_display_units_topic, humidity_topic=config.topic_humidity_probe):
        self.gourd_app = gourd_app
        self.log = logger if logger else gourd_app.log
        self.heater_switch = heater_switch
        self._active = active
        self._last_received = last_received
        self.lock = lock
        self._latest_reading = None
        self._readings = readings if readings else []
        self._target = target
        self.state_topic = state_topic
        self.current_temp_topic = current_temp_topic
        self.target_temp_topic = target_temp_topic
        self.display_units_topic = display_units_topic
        self.humidity_topic = humidity_topic

    def __repr__(self):
        return f"{self.__class__.__name__}(active={self._active}, last_received={self._last_received}, lock=self.lock, readings=self._readings, target=self._target, state_topic=self._state_topic, current_temp_topic=self._current_temp_topic, target_temp_topic=_self.target_temp_topic, display_units_topic=_self.display_units_topic, humidity_topic=_self.humidity_topic)"

    def add_reading(self, temperature):
        """Add a reading to the current list.
        """
        self._last_received = time()
        self._readings.append(temperature)

    @property
    def dedupe_complete(self):
        """Returns True if the deduplication period has passed.
        """
        last_received_delta = time() - self.last_received

        if (last_received_delta > config.dedupe_time) and self._readings:
            return True

        return False

    def action(self):
        """Determine what action the heater needs to perform

        We return using tri-state logic here-
            * `HEATER_ON` means the heater should be turned on
            * `HEATER_OFF` means the heater should be turned off
            * `None` means do nothing
        """
        if self._active and self.temperature:
            if self._latest_reading < self.target - config.temp_variance:
                self.log.debug('HEATER_ON: Temp: %s, ON < %s, OFF > %s', self.temperature, self.target-config.temp_variance, self.target)
                return config.payload_heater_on

            elif self._latest_reading > self.target:
                self.log.debug('HEATER_OFF: Temp: %s, ON < %s, OFF > %s', self.temperature, self.target-config.temp_variance, self.target)
                return config.payload_heater_off

    @property
    def temperature(self):
        """Return the last known temperature.
        """
        self.lock.acquire()

        try:
            if self._readings:
                self._latest_reading = mean(self._readings)
                self._readings = []  # Reset the readings to prep for the next burst of data

                self.gourd_app.publish(config.mqtt_current_temp_topic, self._latest_reading)

        except Exception as e:
            self.log.error('Uncaught exception: %s: %s', e.__class__.__name__, e)
            self.log.exception(e)

        finally:
            self.lock.release()

        return self._latest_reading

    @property
    def active(self):
        return self._active

    @active.setter
    def active(self, enabled):
        self.gourd_app.publish(self.state_topic, enabled)
        self._active = enabled

    @property
    def last_received(self):
        return self._last_received

    @property
    def target(self):
        return self._target

    @target.setter
    def target(self, value):
        self.gourd_app.publish(self._target_temp_topic, value)
        self._target = value
