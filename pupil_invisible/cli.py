import abc
import logging
import typing

import click

from .host_controller import ConnectionController
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

    if host_name is not None:
        controller = ConnectionController(host_name=host_name)
    else:
        raise NotImplementedError

    gaze_relay = PupilInvisibleGazeRelay()

    try:
        while True:
            controller.poll_events()
            for gaze in controller.fetch_gaze():
                # print(gaze)
                gaze_relay.push_gaze_sample(gaze)
    except KeyboardInterrupt:
        pass
    finally:
        controller.cleanup()


if __name__ == "__main__":
    main()
