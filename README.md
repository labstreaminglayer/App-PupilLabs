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

The published LSL data is simply a flattened version (see `extract_*()` functions in `pupil_lsl_relay.py`) of the original Pupil gaze data stream. The stream's channels will be filled with best effort, i.e. if there is a monocular gaze datum the values for the opposite eye will be set to `NaN`. The actual pairing of pupil data to binocular gaze data happens in [Capture](https://github.com/pupil-labs/pupil/blob/master/pupil_src/shared_modules/calibration_routines/gaze_mappers.py#L95-L140) and is not a LSL specific behaviour. Therefore, it is prossible to apply the same [flattening code](https://github.com/papr/App-PupilLabs/blob/master/pupil_lsl_relay.py#L226-L287) to offline calibrated gaze data and reproduce the stream published by the LSL outlet.

## LSL Clock Synchronization

The `Pupil LSL Relay` plugin adjusts Capture's timebase to synchronize Capture's own clock with the `pylsl.local_clock()`. This allows the recording of native Capture timestamps and removes the necessity of manually synchronize timestamps after the effect.

**Warning**: The time synchronization will potentially break if other time alternating actors (e.g. the `Time Sync` plugin or `hmd-eyes`) are active. 