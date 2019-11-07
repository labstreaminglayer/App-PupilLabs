import logging
import typing as T
import ndsi


logger = logging.getLogger(__name__)


class DiscoveryController():

    def __init__(self):
        self.network = ndsi.Network(
            formats={ndsi.DataFormat.V4},
            callbacks=(self.on_event,)
        )
        self.network.start()

    def cleanup(self):
        self.network.stop()

    def poll_events(self):
        while self.network.has_events:
            self.network.handle_event()

    def on_event(self, caller, event):
        if event["subject"] == "attach" and event["sensor_type"] == "gaze":
            self.on_gaze_sensor_attach(
                host_name=event["host_name"],
                sensor_uuid=event["sensor_uuid"]
            )
        if event["subject"] == "detach":
            self.on_gaze_sensor_detach(
                host_name=event["host_name"]
            )

    def on_gaze_sensor_attach(self, host_name, sensor_uuid):
        pass

    def on_gaze_sensor_detach(self, host_name):
        pass


class ConnectionController(DiscoveryController):

    def __init__(self, host_name):
        self._target_host_name = host_name
        self._gaze_sensor = None
        super().__init__()

    def cleanup(self):
        self._disconnect_sensor()
        super().cleanup()

    def poll_events(self):
        super().poll_events()
        if self._gaze_sensor:
            while self._gaze_sensor.has_notifications:
                self._gaze_sensor.handle_notification()

    def fetch_gaze(self):
        if self._gaze_sensor:
            yield from self._gaze_sensor.fetch_data()

    def on_gaze_sensor_attach(self, host_name, sensor_uuid):
        super().on_gaze_sensor_attach(host_name, sensor_uuid)
        if host_name == self._target_host_name:
            self._connect_sensor(sensor_uuid)

    def on_gaze_sensor_detach(self, host_name):
        super().on_gaze_sensor_detach(host_name)
        if host_name == self._target_host_name:
            self._disconnect_sensor()

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
