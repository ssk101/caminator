# Caminator
---
Multi-distro Picamera2 web streaming wrapper
---

This repo was created to simplify (somewhat) the setup process of the work-in-progress [Picamera2](https://github.com/raspberrypi/picamera2) interface and to include instructions for installing the required dependencies for Arch-based RPI distros such as Manjaro. The installation steps have been condensed to a copy/paste-able list from the Picamera2 installation instructions, and the equivalent libraries listed under the Arch installation section below should (hopefully) cover the Debian-based package requirements outlined in the Picamera2 installation instructions. However, Picamera2 might not behave as expected in an Arch-based environment. If you encounter issues running Caminator in an Arch-based distro, check that the versions of the installed python packages are up to date, and check the package repos for any open or closed issues related to your problem.

All required pip packages have been gathered in [requirements.txt](requirements.txt), with a few additions required for streaming, such as `pillow`.

### Clone local package dependencies
```bash
git clone --branch picamera2 https://github.com/raspberrypi/libcamera.git
git clone https://github.com/tomba/kmsxx.git
git clone https://github.com/RaspberryPiFoundation/python-v4l2.git
git clone https://github.com/raspberrypi/picamera2.git
```

### Ubuntu/Debian/Raspberry Pi OS packages
```bash
sudo apt install -y \
python3-pip \
libboost-dev \
libgnutls28-dev \
openssl \
libtiff5-dev \
qtbase5-dev \
libqt5core5a \
libqt5gui5 \
libqt5widgets5 \
meson \
python3-pyqt5 \
python3-opencv \
opencv-data \
libglib2.0-dev \
libgstreamer-plugins-base1.0-dev
```

### Arch packages
```bash
sudo pacman -S \
boost \
gnutls \
openssl \
libtiff \
qt5-base \
meson \
python-pyqt5 \
python-opencv \
glib2 \
gst-plugins-base
```

### Common steps
```bash
pip install --upgrade --force-reinstall -r requirements.txt
```

```bash
cd libcamera

meson build --buildtype=release \
-Dpipelines=raspberrypi \
-Dipas=raspberrypi \
-Dv4l2=true \
-Dgstreamer=enabled \
-Dtest=false \
-Dlc-compliance=disabled \
-Dcam=disabled \
-Dqcam=enabled \
-Ddocumentation=disabled \
-Dpycamera=enabled \
-Dwerror=false

ninja -C build # -j 2 if RPi 3 or earlier
sudo ninja -C build install
```

```bash
cd ../kmsxx
meson build && ninja -C build
```

```bash
cat <<EOT >> ~/.caminator
# Modify these as needed
CAMINATOR_PATH=$HOME/caminator"
CAMINATOR_VIDEO_WIDTH=2592
CAMINATOR_VIDEO_HEIGHT=1944
CAMINATOR_PORT=8888
CAMINATOR_TITLE='Caminator'

# Required for local package resolutions
export PYTHONPATH="$CAMINATOR_PATH/picamera2:$CAMINATOR_PATH/libcamera/build/src/py:$CAMINATOR_PATH/kmsxx/build/py:$CAMINATOR_PATH/python-v4l2"
```

```bash
# Sourcing .caminator isn't required if you only run Caminator via systemd, but the PYTHONPATH above needs to exist in your environment if you run caminator.py directly.
echo "source $HOME/.caminator" >> ~/.bashrc # or ~/.zshrc, etc.
source ~/.bashrc # or ~/.zshrc, etc.
```

### Running

```bash
python ./caminator.py
```

### Run as a systemd service
`sudo nano /etc/systemd/system/caminator.service`

```ini
[Unit]
Description=Caminator
After=multi-user.target

[Service]
User=pi
Type=simple
Restart=always
# Change Caminator path as needed
ExecStart=/bin/bash -ac '. /home/pi/.caminator; exec /usr/bin/python3 /home/pi/caminator/caminator.py'

[Install]
WantedBy=multi-user.target
```

`sudo systemctl enable caminator.service && sudo systemctl start caminator.service`
