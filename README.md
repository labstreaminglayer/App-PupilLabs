# Pupil LSL Relay Plugin

Plugin for _[Pupil Capture](https://github.com/pupil-labs/pupil/wiki/Pupil-Capture)_ that relays pupil and gaze data, as well as notification, to the [lab streaming layer](https://github.com/sccn/labstreaminglayer).

## Installation

 [user plugin directory](https://docs.pupil-labs.com/#plugin-guide)

1. Install `pylsl`
2. Copy the `pylsl` with all its content to the plugin directory_.
3. Copy [`pupil_lsl_relay.py`](pupil_lsl_relay.py) to the .


## Usage

1. Start _Pupil Capture_.
2. [Open the _Pupil LSL Relay_ plugin](https://docs.pupil-labs.com/#open-a-plugin).
3. Optional: Deselect relaying for pupil data, gaze data, or notifications.
4. Now the LSL outlets are ready to provide data to other inlets in the network.

## LSL Outlets

All stream outlets are of type `Pupil Capture`.

Primitive data streams consist of 5 channels (`lsl.cf_double64`):
    - `diameter` (`-1.0` for gaze streams)
    - `confidence`
    - `timestamp`
    - `norm_pos.x`
    - `norm_pos.y`

Python Representation streams consist of 1 channel containing the
Python repr() string of the datum.

The plugin provides following outlets:

- When relaying pupil data:
    - Pupil Primitive Data - Eye 0
    - Pupil Primitive Data - Eye 1
    - Pupil Python Representation - Eye 0
    - Pupil Python Representation - Eye 1
- When relaying gaze data:
    - Gaze Primitive Data
    - Gaze Python Representation
- When relaying notifications:
    - Notifications
