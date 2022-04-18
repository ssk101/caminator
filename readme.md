# CAMERATOR

## Setup
```bash
git clone --branch picamera2 https://github.com/raspberrypi/libcamera.git
git clone https://github.com/tomba/kmsxx.git
git clone https://github.com/RaspberryPiFoundation/python-v4l2.git
git clone https://github.com/raspberrypi/picamera2.git
```

### Ubuntu/Debian/Raspberry Pi OS packages installation
```bash
sudo apt install -y python3-pip \
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

### Arch packages installation
```bash
sudo pacman -S boost \
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
ninja -C build # use -j 2 on Raspberry Pi 3 or earlier devices
sudo ninja -C build install

cd ../kmsxx/
meson build
ninja -C build

cd ..
echo "CAMERATOR_PATH=$HOME/git/camerator" >> ~/.bashrc # or wherever you clone this repo
echo 'export PYTHONPATH="$CAMERATOR_PATH/picamera2:$CAMERATOR_PATH/libcamera/build/src/py:$CAMERATOR_PATH/kmsxx/build/py:$CAMERATOR_PATH/python-v4l2"' >> ~/.bashrc
source ~/.bashrc
```

# Running

```bash
python ./camerator.py
```