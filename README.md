# Pupil LSL Relay Plugin

Plugin for _[Pupil Capture](https://github.com/pupil-labs/pupil/wiki/Pupil-Capture)_ that publishes realtime gaze data using the [lab streaming layer](https://github.com/sccn/labstreaminglayer) framework.

## Installation

 [user plugin directory](https://docs.pupil-labs.com/#plugin-guide)

1. Install `pylsl`
2. Copy or symlink `pylsl` with all its content to the _plugin directory_.
3. Copy [`pupil_lsl_relay.py`](pupil_lsl_relay.py) to the _plugin directory_.


## Usage

1. Start _Pupil Capture_.
2. [Open the _Pupil LSL Relay_ plugin](https://docs.pupil-labs.com/#open-a-plugin).
3. Now the LSL outlet is ready to provide data to other inlets in the network.

## LSL Outlet

The plugin opens a single outlet named `pupil_capture` that follows the [Gaze Meta Data](https://github.com/sccn/xdf/wiki/Gaze-Meta-Data) format.

See our [pupil-helpers](https://github.com/pupil-labs/pupil-helpers/tree/master/LabStreamingLayer) for examples on how to record and visualize the published data.
