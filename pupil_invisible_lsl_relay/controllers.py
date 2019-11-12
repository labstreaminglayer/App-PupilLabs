import logging
import threading
import typing as T
import ndsi


logger = logging.getLogger(__name__)


class DiscoveryController:
    def __init__(self):
        self.discovered_hosts = set()  # Set of discovered hosts with gaze sensors
        self.network = ndsi.Network(
            formats={ndsi.DataFormat.V4}, callbacks=(self.on_event,)
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
                host_name=event["host_name"], sensor_uuid=event["sensor_uuid"]
            )
        if event["subject"] == "detach":
            self.on_gaze_sensor_detach(host_name=event["host_name"])

    def on_gaze_sensor_attach(self, host_name, sensor_uuid):
        self.discovered_hosts.add(host_name)

    def on_gaze_sensor_detach(self, host_name):
        self.discovered_hosts.remove(host_name)


class ConnectionController(DiscoveryController):
    class Timeout(Exception):
        pass

    def __init__(self, host_name, timeout=None):
        self._target_host_name = host_name
        self._gaze_sensor = None
        super().__init__()
        self._connection_did_timeout = False
        if timeout is not None:
            self._connection_timer = threading.Timer(
                timeout, self.on_connection_timeout
            )
            self._connection_timer.start()
        else:
            self._connection_timer = None

    def cleanup(self):
        if self._connection_timer:
            self._connection_timer.cancel()
        self._disconnect_sensor()
        super().cleanup()

    def poll_events(self):
        if self._connection_did_timeout:
            raise ConnectionController.Timeout
        super().poll_events()
        if self._gaze_sensor:
            while self._gaze_sensor.has_notifications:
                self._gaze_sensor.handle_notification()

    def fetch_gaze(self):
        if self._connection_did_timeout:
            raise ConnectionController.Timeout
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

    def on_connection_timeout(self):
        self._connection_did_timeout = True

    def _connect_sensor(self, sensor_uuid):
        self._disconnect_sensor()
        gaze_sensor = self.network.sensor(sensor_uuid)
        self._gaze_sensor = gaze_sensor
        self._gaze_sensor.set_control_value("streaming", True)
        self._gaze_sensor.refresh_controls()
        if self._connection_timer:
            self._connection_timer.cancel()
        logger.debug(f"Sensor connected: {gaze_sensor}")

    def _disconnect_sensor(self):
        if self._gaze_sensor:
            gaze_sensor = self._gaze_sensor
            self._gaze_sensor.unlink()
            self._gaze_sensor = None
            logger.debug(f"Sensor disconnected: {gaze_sensor}")


class InteractionController(DiscoveryController):
    def __init__(self):
        super().__init__()
        self._initial_discovery_event = threading.Event()
        self._network_should_stop = threading.Event()

        self._network_thread = threading.Thread(
            target=self._discovery_run, name="Host discovery", args=(), daemon=False
        )
        self._network_thread.start()

    def _discovery_run(self):
        while not self._network_should_stop.wait(1):
            self.poll_events()
        super().cleanup()  # NOTE: Only call super implementation, since it is the one running in the background thread.

    def cleanup(self):
        self._network_should_stop.set()
        self._network_thread.join()

    def on_gaze_sensor_attach(self, host_name, sensor_uuid):
        super().on_gaze_sensor_attach(host_name, sensor_uuid)
        self._initial_discovery_event.set()

    def on_gaze_sensor_detach(self, host_name):
        super().on_gaze_sensor_detach(host_name)

    def get_user_selected_host_name(self):
        if not self._initial_discovery_event.wait(1):
            return None

        RELOAD_COMMAND = "R"
        shown_hosts = sorted(self.discovered_hosts)

        print("\n======================================")
        print("Please select a Pupil Invisible device:")
        for host_index, host_name in enumerate(shown_hosts):
            print(f"\t{host_index}\t{host_name}")
        print(f"\t{RELOAD_COMMAND}\tReload list")

        user_input = input(">>> ").strip()

        try:
            host_index = int(user_input)
        except ValueError:
            host_index = None

        if host_index is not None and 0 <= host_index < len(shown_hosts):
            return shown_hosts[host_index]
        elif user_input.upper() == RELOAD_COMMAND.upper():
            pass
        else:
            print(f"Invalid input: {user_input}. Please try again.")

        return None
