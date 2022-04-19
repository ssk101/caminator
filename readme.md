# Caminator
---
Multi-distro Picamera2 web streaming wrapper
---

This repo was created to simplify (somewhat) the setup process of the work-in-progress [Picamera2](https://github.com/raspberrypi/picamera2) interface and to include instructions for installing the required dependencies for Arch-based RPI distros such as Manjaro. The installation steps have been condensed to a copy/paste-able list from the Picamera2 installation instructions, and the equivalent libraries listed under the Arch installation section below should (hopefully) cover the Debian-based package requirements outlined in the Picamera2 installation instructions. The required pip packages have been gathered in [requirements.txt](requirements.txt), with a few additions required for streaming.

## Initial setup
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
# Your Camerator path
echo "CAMERATOR_PATH=$HOME/git/camerator" >> ~/.bashrc
# These are required for local Python package resolutions
echo 'export PYTHONPATH="$CAMERATOR_PATH/picamera2:$CAMERATOR_PATH/libcamera/build/src/py:$CAMERATOR_PATH/kmsxx/build/py:$CAMERATOR_PATH/python-v4l2"' >> ~/.bashrc
source ~/.bashrc
```

### Running

```bash
python ./camerator.py
```