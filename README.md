[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/labstreaminglayer/App-PupilLabs/master.svg)](https://results.pre-commit.ci/latest/github/labstreaminglayer/App-PupilLabs/master)

# App-PupilLabs

This repository contains implementations of relays that publish realtime gaze data using the [lab streaming layer](https://github.com/sccn/labstreaminglayer) framework.

- **`pupil_capture`** contains a [Pupil Capture][pupil-capture-app] plugin that works with the [Pupil Core headset][pupil-core-headset] and the [VR/AR add-ons][vr-ar-addons].
More information on how to install and use the plugin is available [here][pupil-core-lsl-readme]
- **`pupil_invisible_lsl_relay`** is a command line tool for publishing data from [Pupil Invisible][pupil-invisible-headset-and-app].
More information on how to install and use the tool is available [here][pupil-invisible-lsl-readme].


[pupil-capture-app]: https://github.com/pupil-labs/pupil/releases/latest
[pupil-core-headset]: https://pupil-labs.com/products/core
[pupil-invisible-headset-and-app]: https://pupil-labs.com/products/invisible/
[pupil-core-lsl-readme]: https://github.com/labstreaminglayer/App-PupilLabs/blob/master/pupil_capture/README.md
[pupil-invisible-lsl-readme]: https://github.com/labstreaminglayer/App-PupilLabs/blob/master/pupil_invisible_lsl_relay/README.md
[vr-ar-addons]: https://pupil-labs.com/products/vr-ar/
