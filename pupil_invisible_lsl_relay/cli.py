import abc
import logging
import typing

import click

from .controllers import ConnectionController, InteractionController
from .pi_gaze_relay import PupilInvisibleGazeRelay


logger = logging.getLogger(__name__)


@click.command()
@click.option("--host-name", default=None, help="Device (host) name to connect")
@click.option(
    "--timeout",
    default=5.0,
    help="Time limit in seconds to try to connect to the device (only works with --host-name argument)",
)
def main(host_name: str, timeout: float):

    if host_name is None:
        toggle_logging(enable=False)
        host_name = interactive_mode_get_host_name()
        timeout = (
            None
        )  # Since the user picked a device from the discovered list, ignore the timeout

    if host_name is None:
        exit(0)

    toggle_logging(enable=True)

    gaze_relay = PupilInvisibleGazeRelay()

    for gaze in gaze_data_stream(host_name, connection_timeout=timeout):
        gaze_relay.push_gaze_sample(gaze)


def interactive_mode_get_host_name():
    interaction = InteractionController()
    try:
        while True:
            host_name = interaction.get_user_selected_host_name()
            if host_name is not None:
                return host_name
    except KeyboardInterrupt:
        return None
    finally:
        interaction.cleanup()


def gaze_data_stream(host_name, connection_timeout):
    connection = ConnectionController(host_name=host_name, timeout=connection_timeout)
    try:
        while True:
            connection.poll_events()
            for gaze in connection.fetch_gaze():
                # logger.debug(gaze)
                yield gaze
    except KeyboardInterrupt:
        pass
    except ConnectionController.Timeout:
        print(f"===============================================")
        print(f'Failed to discover device named "{host_name}"')
        print(f"Discovered devices:")
        for host_name in connection.discovered_hosts:
            print(f"\t{host_name}")
        print(f"===============================================")
    finally:
        connection.cleanup()


def toggle_logging(enable: bool):
    handlers = []
    if enable:
        handlers.append(logging.StreamHandler())
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=handlers,
        style="{",
        format="{asctime} [{levelname}] {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("pyre").setLevel(logging.WARNING)


if __name__ == "__main__":
    main()
