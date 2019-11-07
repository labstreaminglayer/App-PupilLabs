# Pupil Invisible Gaze Relay

## Usage

#### Basic mode

The basic usage of the Pupil Invisible Gaze Relay module is to provide a device host name as an argument. The module will wait for that device to announce a gaze sensor, will connect to it and start pushing the gaze data to the LSL outlet.

```bash
python3 -m pupil_invisible --host-name <DEVICE_NAME>
```

#### Interactive mode

In interactive mode, there is no need to provide the device name beforehand. Instead, the module monitors the network and shows a list of available devices which the user can select.

```bash
python3 -m pupil_invisible
```
