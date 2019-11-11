# Pupil Invisible Gaze Relay

## Installation

```bash
git clone https://github.com/labstreaminglayer/App-PupilLabs.git

cd App-PupilLabs/
git checkout pupil-invisible-relay

# Use the Python 3 installation of your choice
python -m pip install -U pip
python -m pip install -r requirements.txt
```

## Usage

#### Basic mode

The basic usage of the Pupil Invisible Gaze Relay module is to provide a device host name as an argument. The module will wait for that device to announce a gaze sensor, will connect to it and start pushing the gaze data to the LSL outlet named `pupil_invisible`.

```bash
pupil_invisible_lsl_relay --host-name <DEVICE_NAME>
```

#### Interactive mode

In interactive mode, there is no need to provide the device name beforehand. Instead, the module monitors the network and shows a list of available devices which the user can select.

```bash
pupil_invisible_lsl_relay
```
