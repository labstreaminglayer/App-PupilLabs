import logging
import typing as T
import ndsi


logger = logging.getLogger(__name__)


class HostController():

    def __init__(self, host_name):
        self._target_host_name = host_name
        self._gaze_sensor = None
        self.network = ndsi.Network(
            formats={ndsi.DataFormat.V4},
            callbacks=(self.on_event,)
        )
        self.network.start()

    def cleanup(self):
        self._disconnect_sensor()
        self.network.stop()

    def poll_events(self):
        while self.network.has_events:
            self.network.handle_event()
        if self._gaze_sensor:
            while self._gaze_sensor.has_notifications:
                self._gaze_sensor.handle_notification()

    def fetch_gaze(self):
        if self._gaze_sensor:
            yield from self._gaze_sensor.fetch_data()

    def _connect_sensor(self, sensor_uuid):
        self._disconnect_sensor()
        gaze_sensor = self.network.sensor(sensor_uuid)
        self._gaze_sensor = gaze_sensor
        self._gaze_sensor.set_control_value("streaming", True)
        self._gaze_sensor.refresh_controls()
        logger.debug(f"Sensor connected: {gaze_sensor}")

    def _disconnect_sensor(self):
        if self._gaze_sensor:
            gaze_sensor = self._gaze_sensor
            self._gaze_sensor.unlink()
            self._gaze_sensor = None
            logger.debug(f"Sensor disconnected: {gaze_sensor}")

    def on_event(self, caller, event):
        if event["subject"] == "attach" and event["host_name"] == self._target_host_name and event["sensor_type"] == "gaze":
            self._connect_sensor(event["sensor_uuid"])

        if event["subject"] == "detach" and event["host_name"] == self._target_host_name:
            self._disconnect_sensor()
