# Caminator
### Setup
```bash
apt install python3-picamera2
python -m venv --system-site-packages ./venv
source ./venv/bin/activate
pip install -r ./requirements.txt
```

### Starting web server

Start camera stream:
```bash
python ./stream.py
```

Start Express server:
```bash
yarn start
```

or

```bash
node ./caminator.js
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
ExecStart=/bin/bash -ac 'exec /usr/bin/node /home/pi/caminator/caminator.js'

[Install]
WantedBy=multi-user.target
```

`sudo systemctl enable caminator.service && sudo systemctl start caminator.service`
