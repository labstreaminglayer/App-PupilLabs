import abc
import logging
import typing

import click

from .controllers import ConnectionController
from .pi_gaze_relay import PupilInvisibleGazeRelay


@click.command()
@click.option("--host-name", default=None, help="Device (host) name to connect")
def main(host_name: str):

    handlers = [
        logging.StreamHandler(),
    ]
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=handlers,
        style="{",
        format="{asctime} [{levelname}] {message}",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("pyre").setLevel(logging.WARNING)

    if host_name is None:
        NotImplementedError("Interactive mode not yet implemented")

    gaze_relay = PupilInvisibleGazeRelay()

    for gaze in gaze_data_stream(host_name):
        print(gaze)
        gaze_relay.push_gaze_sample(gaze)


def gaze_data_stream(host_name):
    controller = ConnectionController(host_name=host_name)
    try:
        while True:
            controller.poll_events()
            for gaze in controller.fetch_gaze():
                yield gaze
    except KeyboardInterrupt:
        pass
    finally:
        controller.cleanup()


if __name__ == "__main__":
    main()
