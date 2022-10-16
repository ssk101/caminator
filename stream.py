#!/usr/bin/python3

import os
import io
import sys
import json
import logging
import socketserver
import time
from http import server
from threading import Condition
from picamera2.outputs import FileOutput
from lib.helpers import get_env, exit_self
from lib.camera import create_camera

ENV = get_env()

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
    'value': 0,
    'min': 0,
    'max': 3,
  },
  'AeExposureMode': {
    'type': 'int',
    'control': 'range',
    'value': 0,
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
    'value': 0,
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
    'value': 63835,
  },
  'ExposureValue': {
    'type': 'float',
    'control': 'range',
    'step': 0.1,
    'value': 0.0,
    'min': -8.0,
    'max': 8.0,
  },
  'AnalogueGain': {
    'type': 'int',
    'control': 'range',
    'step': 1,
    'value': 8,
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

class StreamHandler(server.BaseHTTPRequestHandler):
  def get_respond(self, code=200, response={}, content_type='application/json', extra_headers=[]):
    self._set_headers(code, content_type, extra_headers)
    self.wfile.write(json.dumps(response).encode(encoding='utf-8'))
    self.end_headers()

  def get_body(self):
    body_length = int(self.headers['Content-Length'])
    return self.rfile.read(body_length)

  def post_respond(self, code=200, response={}, content_type='application/json', extra_headers=[]):
    self._set_headers(code, content_type, extra_headers)
    self.wfile.write(json.dumps(response).encode(encoding='utf-8'))
    self.end_headers()

  def _set_headers(self, code=200, content_type='application/json', extra_headers=[]):
    self.send_response(200)
    self.send_header('Age', 0)
    self.send_header('Cache-Control', 'no-cache, private')
    self.send_header('Pragma', 'no-cache')
    self.send_header('Content-type', content_type)

    for extra in extra_headers:
      self.send_headers(extra[0], extra[1])

    self.end_headers()

  def do_HEAD(self):
    self._set_headers()

  def do_POST(self):
    if self.path == '/quality':
      body = json.loads(self.get_body())
      picam2.stop_recording()
      start_camera(quality=body)
      self.post_respond(response={ 'message': 'ok' })

    elif self.path == '/controls':
      response = dict()

      try:
        body = json.loads(self.get_body())

        try:
          set_camera_meta(body)
        except Exception as e:
          logging.error(e)

      except Exception as e:
        logging.error(e)

      self.post_respond(response=formatted_meta())

    else:
      self.send_error(404)
      self.end_headers()

  def do_GET(self):
    if self.path == '/':
      self.get_respond(
        code=301,
        content_type='multipart/x-mixed-replace; boundary=FRAME',
      )

    elif self.path == '/stream':
      self.get_respond(
        content_type='multipart/x-mixed-replace; boundary=FRAME',
      )

      try:
        while True:
          with output.condition:
            output.condition.wait()
            frame = output.frame
          self.wfile.write(b'--FRAME\r\n')
          self.send_header('Content-Type', 'image/jpeg')
          self.send_header('Content-Length', len(frame))
          self.end_headers()
          self.wfile.write(frame)
          self.wfile.write(b'\r\n')

      except Exception as e:
        logging.warning(
          'Removed streaming client %s: %s',
          self.client_address, str(e)
        )

    elif self.path == '/meta':
      self.get_respond(response=formatted_meta())

    else:
      self.send_error(404)
      self.end_headers()

class CamServer(socketserver.ThreadingMixIn, server.HTTPServer):
  allow_reuse_address = True
  daemon_threads = True

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
  output = StreamingOutput()

  try:
    picam2, encoder = create_camera(quality=quality)
    picam2.start_recording(encoder, FileOutput(output))
    return picam2, output
  except Exception as e:
    logging.warn(e)

picam2, output = start_camera(quality=20)
set_camera_meta()

if __name__ == '__main__':

  try:
    try:
      address = ('', ENV['port'])
      server = CamServer(address, StreamHandler)
      server.serve_forever()

    except Exception as e:
      exit_self(e)

    finally:
      picam2.stop_recording()

  except KeyboardInterrupt:
    exit_self('KeyboardInterrupt')