[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/labstreaminglayer/App-PupilLabs/master.svg)](https://results.pre-commit.ci/latest/github/labstreaminglayer/App-PupilLabs/master)

# App-PupilLabs

This repository contains various integrations of the [lab streaming layer](https://github.com/sccn/labstreaminglayer) framework with Pupil Labs products.

## Pupil Invisible LSL Relay

To receive and save Pupil Invisible data in realtime via LSL, checkout the dedicated
Pupil Invisible LSL Relay application: https://pupil-invisible-lsl-relay.readthedocs.io/en/stable/

The legacy PI LSL Relay can be found [here](https://github.com/labstreaminglayer/App-PupilLabs/tree/legacy-pi-lsl-relay/pupil_invisible_lsl_relay).

## Pupil Capture Plugins

- The **`pupil_capture`** folder contains various [Pupil Capture][pupil-capture-app]
  plugins that work with the [Pupil Core headset][pupil-core-headset] and the [VR/AR add-ons][vr-ar-addons].
  More information on how to install and use the plugin is available [here][pupil-core-lsl-readme]


[pupil-capture-app]: https://github.com/pupil-labs/pupil/releases/latest
[pupil-core-headset]: https://pupil-labs.com/products/core
[pupil-core-lsl-readme]: https://github.com/labstreaminglayer/App-PupilLabs/blob/master/pupil_capture/README.md
[vr-ar-addons]: https://pupil-labs.com/products/vr-ar/
