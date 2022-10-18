#!/usr/bin/python3

import os
import io
import sys
import json
import logging
import time
from flask import Flask, Response, request
from threading import Condition
from picamera2.outputs import FileOutput
from lib.helpers import get_env, exit_self
from lib.camera import create_camera

ENV = get_env()

app = Flask(__name__)

TYPES = {
  'int': int,
  'float': float,
  'bool': bool,
  'list': list,
  'str': str,
  'dict': dict
}

CONTROLS = {
  'AeEnable': {
    'type': 'int',
    'control': 'checkbox',
    'value': True,
  },
  'AeConstraintMode': {
    'type': 'int',
    'control': 'range',
    'value': 1,
    'min': 0,
    'max': 3,
  },
  'AeExposureMode': {
    'type': 'int',
    'control': 'range',
    'value': 2,
    'min': 0,
    'max': 3,
  },
  'AeMeteringMode': {
    'type': 'int',
    'control': 'range',
    'value': 0,
    'min': 0,
    'max': 3,
  },
  'NoiseReductionMode': {
    'type': 'int',
    'control': 'range',
    'value': 1,
    'min': 0,
    'max': 2,
  },
  'AwbEnable': {
    'type': 'int',
    'control': 'checkbox',
    'value': True,
  },
  'AwbMode': {
    'type': 'int',
    'control': 'range',
    'step': 1,
    'value': 0,
    'min': 0,
    'max': 6,
  },
  'FrameDurationLimits': {
    'type': 'list',
    'control': 'range',
    'step': 0,
    'value': [0, 0],
    'enabled': False,
  },
  'ExposureTime': {
    'type': 'int',
    'control': 'range',
    'step': 1000,
    'min': 0,
    'max': 200000,
    # 'value': 200000,
    'value': 63835,
  },
  'ExposureValue': {
    'type': 'float',
    'control': 'range',
    'step': 1.0,
    'value': 0.0,
    'min': -8.0,
    'max': 8.0,
  },
  'AnalogueGain': {
    'type': 'float',
    'control': 'range',
    'step': 1,
    'value': 0.0,
    'min': -8.0,
    'max': 8.0,
  },
  'Brightness': {
    'type': 'float',
    'control': 'range',
    'step': 0.1,
    'value': 0.0,
    'min': -1.0,
    'max': 1.0,
  },
  'Contrast': {
    'type': 'float',
    'control': 'range',
    'step': 0.1,
    'value': 1.0,
    'min': 0.0,
    'max': 32.0,
  },
  'Sharpness': {
    'type': 'float',
    'control': 'range',
    'step': 0.1,
    'value': 0.0,
    'min': 0.0,
    'max': 16.0,
  },
}

class StreamingOutput(io.BufferedIOBase):
  def __init__(self):
    self.frame = None
    self.condition = Condition()

  def write(self, buf):
    with self.condition:
      self.frame = buf
      self.condition.notify_all()

stream = StreamingOutput()

def relay():
  while True:
    with stream.condition:
      time.sleep(0.2)
      stream.condition.wait()
      yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + stream.frame + b'\r\n')

@app.route('/')
def on_slash():
  return Response(relay(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/meta')
def on_meta():
  return json.dumps(formatted_meta())

@app.route('/quality', methods = ['POST'])
def on_quality():
  body = request.get_json()
  picam2.stop_recording()
  start_camera(quality=body)
  return json.dumps(formatted_meta())

@app.route('/controls', methods = ['POST'])
def on_controls():
  response = dict()

  try:
    body = request.get_json()

    try:
      set_camera_meta(body)

    except Exception as e:
      logging.error(e)

  except Exception as e:
    logging.error(e)

  return json.dumps(formatted_meta())

def formatted_meta():
  formatted = dict()

  for key in CONTROLS:
    if not CONTROLS[key].get('enabled', True):
      continue

    t = TYPES[CONTROLS[key]['type']]

    try:
      formatted[key] = {
        'value': str(t(CONTROLS[key]['value'])),
        'control': CONTROLS[key].get('control'),
        'min': CONTROLS[key].get('min'),
        'max': CONTROLS[key].get('max'),
        'step': CONTROLS[key].get('step'),
      }
    except Exception as e:
      logging.error(e)

  return formatted

def set_camera_meta(meta={}):
  sanitized = dict()

  for key in CONTROLS:
    if meta.get(key) is not None:
      CONTROLS[key]['value'] = meta[key]

    sanitized[key] = CONTROLS[key]['value']

  logging.info(sanitized)

  try:
    picam2.set_controls(sanitized)
  except Exception as e:
    logging.error(e)

def start_camera(quality=20):
  try:
    picam2, encoder = create_camera(quality=quality)

    try:
      picam2.start_recording(encoder, FileOutput(output))
      return picam2, output
    except Exception as e:
      logging.error(e)

  except Exception as e:
    logging.error(e)

picam2, output = start_camera(quality=20)
set_camera_meta()

if __name__ == '__main__':
  try:
    try:
      app.run(host=ENV['host'], port=ENV['port'])

    except Exception as e:
      exit_self(e)

    finally:
      picam2.stop_recording()

  except KeyboardInterrupt:
    exit_self('KeyboardInterrupt')

  finally:
    picam2.stop_recording()
