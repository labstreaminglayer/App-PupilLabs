# Pupil Capture LSL Relay Plugin

Plugin for _[Pupil Capture](https://github.com/pupil-labs/pupil/releases/latest)_ that publishes realtime gaze data using the [lab streaming layer](https://github.com/sccn/labstreaminglayer) framework.

## Installation

Please see our documentation on where to find the [user plugin directory](https://docs.pupil-labs.com/developer/core/plugin-api/#adding-a-plugin).

1. Install `pylsl`
2. Copy or symlink `pylsl` with all its content to the _plugin directory_.
3. Copy [`pupil_capture_lsl_relay.py`](pupil_capture_lsl_relay.py) to the _plugin directory_.


## Usage

1. Start _Pupil Capture_.
2. [Open the _Pupil Capture LSL Relay_ plugin](https://docs.pupil-labs.com/core/software/pupil-capture/#plugins).
3. Now the LSL outlet is ready to provide data to other inlets in the network.

## LSL Outlet

The plugin opens a single outlet named `pupil_capture` that follows the [Gaze Meta Data](https://github.com/sccn/xdf/wiki/Gaze-Meta-Data) format.

See our [pupil-helpers](https://github.com/pupil-labs/pupil-helpers/tree/master/LabStreamingLayer) for examples on how to record and visualize the published data.

The published LSL data is simply a flattened version (see `extract_*()` functions in `pupil_capture_lsl_relay.py`) of the original Pupil gaze data stream. The stream's channels will be filled with best effort, i.e. if there is a monocular gaze datum the values for the opposite eye will be set to `NaN`. The actual pairing of pupil data to binocular gaze data happens in [Capture](https://github.com/pupil-labs/pupil/blob/master/pupil_src/shared_modules/calibration_routines/gaze_mappers.py#L95-L140) and is not a LSL specific behaviour. Therefore, it is possible to apply the same [flattening code](https://github.com/papr/App-PupilLabs/blob/master/pupil_lsl_relay.py#L226-L287) to offline calibrated gaze data and reproduce the stream published by the LSL outlet.

## Data Format

'confidence': Normalized (0-1) confidence.

'norm_pos_x', 'norm_pos_y': Normalized (0-1) coordinates on the screen.

'gaze_point_3d_x', 'gaze_point_3d_y', 'gaze_point_3d_z': World coordinates in mm

'eye_centerright_3d_x' ... (for right/left eyes, for x/y/z): Position of eye center in world coordinates in mm.

'gaze_normalright_x' (right/left, x/y/z): End point of vector from eye center (I think).

'diameterright_2d' (right/left): Pupil diameter in pixels

'diameterright_3d' (right/left): Pupil diameter in mm

## LSL Clock Synchronization

The `Pupil LSL Relay` plugin adjusts Capture's timebase to synchronize Capture's own clock with the `pylsl.local_clock()`. This allows the recording of native Capture timestamps and removes the necessity of manually synchronize timestamps after the effect.

**Warning**: The time synchronization will potentially break if other time alternating actors (e.g. the `Time Sync` plugin, `hmd-eyes`, or `T` Pupil Remote command) are active. Note that hmd-eyes v1.4 and later no longer adjusts Pupil Capture's clock and is therefore compatible with the LSL Relay Plugin.

### Synchronizing Other Pupil Core Data Post-hoc

The [LSL LabRecorder](https://github.com/labstreaminglayer/App-LabRecorder) records LSL data streams to XDF (extensible data format) files. These include the [native stream time (as measured by the `pylsl.local_clock()`) as well as the necessary clock offset to the synchronized time domain between the recorded streams](https://github.com/sccn/xdf/wiki/Specifications#general-comments). Most XDF importers will apply the clock offset when loading the recorded data, yielding time-synchronized samples. 

Should you ever want to synchronize other data recorded by Pupil Capture that is not published via LSL, you can do so by building a time-mapping between the original stream time and the synchronized time. In this case, your XDF importer needs to support loading the recorded samples without automatically applying the corresponding clock offset.

- Python - [`pyxdf`](https://github.com/xdf-modules/pyxdf/) accepts [`synchronize_clocks=True` in its `load_xdf()` function](https://github.com/xdf-modules/pyxdf/blob/main/pyxdf/pyxdf.py#L74)
- MATLAB - The [MATLAB importer](https://github.com/xdf-modules/xdf-Matlab/tree/master) accepts the [`HandleClockSynchronization` argument in its `load_xdf` function](https://github.com/xdf-modules/xdf-Matlab/blob/18f699eecb4259fde55e2cf51f874d6966f6d5ba/load_xdf.m#L25-L26) (default `true`).
- EEGLab - Please note that [EEGLab's `xdf_importer`](https://github.com/xdf-modules/xdf-EEGLAB/) does **not** support this functionality since it uses the Matlab implementation above without setting the `HandleClockSynchronization` argument to `false`.

After loading the timeseries once with and once without time synchronization, you have a one-to-one mapping between the two time domains which can be interpolated linearly for new timestamps. This time mapping can then be used to transform other LSL-recorded data streams to native Pupil Capture time, or vice versa.
