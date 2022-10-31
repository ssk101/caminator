#!/usr/bin/python3

import os
import io
import sys
import json
import logging
import time
import socketserver
from http import server
from flask import Flask, Response, request, redirect
from threading import Condition
from picamera2.outputs import FileOutput
from lib.helpers import get_env, exit_self
from lib.camera import create_camera, create_encoder

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
  # 'ScalerCrop': {
  #   'type': 'list',
  #   'controlType': 'input',
  #   'description': ['X', 'Y', 'width', 'height'],
  #   'step': 1,
  #   'value': [0, 0, ENV.get('width', 1296), ENV.get('height', 972)],
  # },
  'Quality': {
    'type': 'int',
    'controlType': 'range',
    'description': ['Stream quality'],
    'step': 1,
    'min': 0,
    'max': 100,
    'value': ENV['quality'],
  },
  # 'ColourFilterArrangement': {
  #   'type': 'int',
  #   'controlType': 'range',
  #   'description': ['RGGB', 'GRBG', 'GBRG', 'BGGR', 'monochrome'],
  #   'value': 0,
  #   'min': 0,
  #   'max': 4,
  #   'step': 1.
  # },
  'AeEnable': {
    'type': 'bool',
    'controlType': 'checkbox',
    'value': False,
  },
  'AwbEnable': {
    'type': 'bool',
    'controlType': 'checkbox',
    'value': False,
  },
  'AwbMode': {
    'type': 'int',
    'controlType': 'range',
    'step': 1,
    'value': 0,
    'min': 0,
    'max': 6,
    'description': ['Auto', 'Tungsten', 'Fluorescent', 'Indoor', 'Daylight', 'Cloudy'],
  },
  'AeConstraintMode': {
    'type': 'int',
    'controlType': 'range',
    'min': 0,
    'max': 1,
    'value': 0,
    'description': ['Normal', 'Highlights'],
  },
  'AeExposureMode': {
    'type': 'int',
    'controlType': 'range',
    'min': 0,
    'max': 2,
    'value': 0,
    'description': ['Normal', 'Short', 'Long'],
  },
  'AeMeteringMode': {
    'type': 'int',
    'controlType': 'range',
    'min': 0,
    'max': 2,
    'value': 0,
    'description': ['CentreWeighted', 'Spot', 'Matrix'],
  },
  'NoiseReductionMode': {
    'type': 'int',
    'controlType': 'range',
    'value': 1,
    'min': 0,
    'max': 2,
    'description': ['Off', 'Fast', 'HQ'],
  },
  'FrameRate': {
    'type': 'int',
    'controlType': 'range',
    'step': 1,
    'min': 1,
    'max': 90,
    'value': ENV.get('fps', 42),
  },
  'ExposureTime': {
    'type': 'int',
    'controlType': 'range',
    'step': 1000,
    'min': 0,
    'max': 400000,
    'value': 0,
  },
  'ExposureValue': {
    'type': 'float',
    'controlType': 'range',
    'step': 1,
    'min': -8.0,
    'max': 8.0,
    'value': 0.0,
  },
  'AnalogueGain': {
    'type': 'float',
    'controlType': 'range',
    'step': 1,
    'min': 1.0,
    'max': 16.0,
    'value': 0.0,
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
    'min': 0.0,
    'max': 32.0,
    'value': 1.0,
  },
  'Sharpness': {
    'type': 'float',
    'controlType': 'range',
    'step': 1,
    'min': 0.0,
    'max': 16.0,
    'value': 1.0,
  },
}

frame_delay = ENV['frame_delay']

class StreamingOutput(io.BufferedIOBase):
  def __init__(self):
    self.frame = None
    self.condition = Condition()

  def write(self, buf):
    with self.condition:
      self.frame = buf
      self.condition.notify_all()

class StreamingServer(socketserver.ThreadingMixIn, server.HTTPServer):
  allow_reuse_address = True
  daemon_threads = True

def stop_start(quality=CONTROLS['Quality']['value']):
  output = StreamingOutput()

  try:
    picam2.stop_recording()
  except Exception as e:
    pass

  encoder = create_encoder(quality=quality)
  picam2.start_recording(encoder, FileOutput(output))
  return output

def relay():
  output = stop_start(quality=CONTROLS['Quality']['value'])

  while True:
    time.sleep(frame_delay)

    with output.condition:
      output.condition.wait()
      frame = output.frame

    yield (b'--frame\r\nContent-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def on_slash():
  return Response(relay(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/meta')
def on_meta():
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
        'description': CONTROLS[key].get('description', []),
      }
    except Exception as e:
      logging.error(e)

  return formatted

def set_camera_meta(meta={}):
  sanitized = dict()

  for key in CONTROLS:
    t = TYPES[CONTROLS[key]['type']]

    value = meta.get(key)

    if value is not None:
      CONTROLS[key]['value'] = meta[key]

    # if key == 'ScalerCrop':
    #   if value is not None:

    if key == 'Quality':
      if value is not None:
        stop_start(quality=value)
      continue

    sanitized[key] = t(CONTROLS[key]['value'])

  try:
    logging.info(sanitized)
    picam2.set_controls(sanitized)
  except Exception as e:
    logging.error(e)

if __name__ == '__main__':
  try:
    picam2 = create_camera()
    stop_start(quality=CONTROLS['Quality']['value'])
    set_camera_meta()

    try:
      app.run(host=ENV['host'], port=ENV['port'], threaded=True)

    except Exception as e:
      exit_self(e)

    finally:
      picam2.stop_recording()

  except KeyboardInterrupt:
    exit_self('KeyboardInterrupt')

  finally:
    picam2.stop_recording()
