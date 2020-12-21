# A(utomated)Capture

![Logo](https://github.com/maslyankov/Automated-Android-PhotoVideo-Testing/blob/master/images/automated-video-testing-header.png?raw=true "Logo Header")

This project automates the process of testing photo/video capture (Android / USB webcam) devices, generation of reports and more. 

  * [Features](#features)
  * [Prerequisites](#prerequisites)
  * [Setup project](#setup-project)
  * [Building](#building)
  * [Contact](#contact)
  * [License](#license)

## Features:
- Persistence of devices settings
- Lights control of SpectriWave (easy to add support for more) with GUI and programmatically
- Light Intensity Sensors (Luxmeters) support (Currently supported - Konita Minolta CL-200A)
- Automated capturing of test cases - video/photo based on template build in GUI with different light temperatures and intensities.
- Integration with Imatest IT for automated images analysis

Tools:
- Generating of Objective Testing Reports based on requirements templates build in GUI and using imported files or automatically captured ones. 
- Generating of Real-Life Testing Reports based on settings in GUI
- Extract frames from video (names extracted frames accordingly, supports multiple files at once, skipping frames, etc)

#### Android*:
- Roots, Remounts device automatically
- Sets device sleep time to max, wakes device etc automatically
- Execute taps on Android devices screens (actions) => Works on any rooted Android
- Supports multiple actions (called actions sequence) for capture of video / photos (ex change mode to video then shoot video)
- Capturing Images / Videos using device
- Pulling captured Images / videos to the computer
- Renaming of pulled Images / videos properly
- Getting logs automatically

##### Android with GUI*:
- Push one or multiple files to device's specific directory
- Pull one or multiple files from device using a visual tree GUI (work in progress)
- Easy to use text editor for frequently used text files (for ex. camxoverridesettings.txt)
- Reboot Device
- View device info (build, android versions etc)
- Device screen control and mirroring

for automated/semi-automated testing:

- Setup aciton sequences in GUI
- Enable/Disable logs during testing
- Add logs filter string
- Change default images capture app for automated testing (dropdown of all apps on device)
- Add a time gap between actions to give time to the device to load the screens and etc

*requires device to be rooted

#### Devices:
- Set friendly name of device (used for naming saved files/folders etc)
- Identify device (Blink screen/leds)
- Attach to and capture using multiple devices at once

#### App GUI Preview

<img src="https://github.com/ttodorov9/acapture/blob/master/README/Beta/app-screenshot.jpg?raw=true" width="300">

#### Lights Control GUI Preview

<img src="https://github.com/ttodorov9/acapture/blob/master/README/Beta/lights-test-screenshot.jpg?raw=true" width="300">

#### Automated Cases GUI Preview

<img src="https://github.com/ttodorov9/acapture/blob/master/README/Beta/Automated-cases-gui.jpg?raw=true" width="300">

## Prerequisites

Before you begin, ensure you have met the following requirements:
<!--- These are just example requirements. Add, duplicate or remove as required --->
* You have a `Windows` machine. 
Most code is written OS-independent, but more work is needed for proper support of `Linux` and `Mac`
* You have installed the `Python 3.6`
* You have a working `pip` (Python Package Manager).

## Setup project

To setup the project, follow these steps:

1. Clone the project:
    ```
    git clone https://github.com/ttodorov9/acapture.git
    ```

2. Open the cloned project folder in cmd

3. Download and install requirements:
    ```
    pip install -r requirements.txt
    ```

## Building

To build the project, execute a single command:

```
build_exe.bat
```
This should build files and save them to /dist

## Contact

If you want to contact me you can reach me at mmaslyankov@mm-sol.com

## License
<!--- If you're not sure which open license to use see https://choosealicense.com/--->