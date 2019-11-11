# App-PupilLabs

This repository contains implementations of relays that publish realtime gaze data using the [lab streaming layer](https://github.com/sccn/labstreaminglayer) framework.

- **`pupil_capture`** contains a [Pupil Capture][pupil-capture-app] plugin that works with the [Pupil Core headset][pupil-core-headset].  
More information on how to install and use the plugin is available [here][pupil-core-lsl-readme]
- **`pupil_invisible_lsl_relay`** is a command line tool for publishing data from the [Pupil Invisible headset][pupil-invisible-headset-and-app].  
More information on how to install and use the tool is available [here][pupil-invisible-lsl-readme].


[pupil-capture-app]: https://docs.pupil-labs.com/core
[pupil-core-headset]: https://docs.pupil-labs.com/core/hardware
[pupil-invisible-headset-and-app]: https://docs.pupil-labs.com/invisible
[pupil-core-lsl-readme]: https://github.com/labstreaminglayer/App-PupilLabs/blob/master/pupil_capture/README.md
[pupil-invisible-lsl-readme]: https://github.com/labstreaminglayer/App-PupilLabs/blob/master/pupil_invisible_lsl_relay/README.md
