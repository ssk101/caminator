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
  'dict': dict,
  'tuple': tuple,
}

CONTROLS = {
  'AeEnable': {
    'type': 'int',
    'controlType': 'checkbox',
    'value': True,
  },
  'AeConstraintMode': {
    'type': 'int',
    'controlType': 'range',
    'value': 0,
    'min': 0,
    'max': 3,
  },
  'AeExposureMode': {
    'type': 'int',
    'controlType': 'range',
    'value': 0,
    'min': 0,
    'max': 2,
  },
  'AeMeteringMode': {
    'type': 'int',
    'controlType': 'range',
    'value': 0,
    'min': 0,
    'max': 3,
  },
  'NoiseReductionMode': {
    'type': 'int',
    'controlType': 'range',
    'value': 0,
    'min': 0,
    'max': 2,
  },
  'AwbEnable': {
    'type': 'int',
    'controlType': 'checkbox',
    'value': True,
  },
  'AwbMode': {
    'type': 'int',
    'controlType': 'range',
    'step': 1,
    'value': 0,
    'min': 0,
    'max': 6,
  },
  'FrameDurationLimits': {
    'type': 'tuple',
    'controlType': 'input',
    'step': 0,
    'value': [0, 0],
  },
  'ExposureTime': {
    'type': 'int',
    'controlType': 'range',
    'step': 1000,
    'min': 0,
    'max': 200000,
    'value': 1000,
  },
  'ExposureValue': {
    'type': 'float',
    'controlType': 'range',
    'step': 1,
    'value': 0.0,
    'min': -8.0,
    'max': 8.0,
  },
  'AnalogueGain': {
    'type': 'float',
    'controlType': 'range',
    'step': 1,
    'value': 0.0,
    'min': -8.0,
    'max': 8.0,
  },
  'Brightness': {
    'type': 'float',
    'controlType': 'range',
    'step': 0.1,
    'value': 0.0,
    'min': -1.0,
    'max': 1.0,
  },
  'Contrast': {
    'type': 'float',
    'controlType': 'range',
    'step': 1,
    'value': 1.0,
    'min': 0.0,
    'max': 32.0,
  },
  'Sharpness': {
    'type': 'float',
    'controlType': 'range',
    'step': 1,
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
      time.sleep(0.1)
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
    if CONTROLS[key].get('disabled', False):
      continue

    t = TYPES[CONTROLS[key]['type']]

    try:
      formatted[key] = {
        'value': CONTROLS[key]['value'],
        'controlType': CONTROLS[key].get('controlType'),
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
    t = TYPES[CONTROLS[key]['type']]

    if meta.get(key) is not None:
      CONTROLS[key]['value'] = meta[key]

    sanitized[key] = t(CONTROLS[key]['value'])

  logging.info(sanitized)

  try:
    picam2.set_controls(sanitized)
  except Exception as e:
    logging.error(e)

def start_camera(quality=20):
  try:
    picam2, encoder = create_camera(quality=quality)

    try:
      picam2.start_recording(encoder, FileOutput(stream))
      return picam2
    except Exception as e:
      logging.error(e)

  except Exception as e:
    logging.error(e)

picam2 = start_camera(quality=20)
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
