#!/usr/bin/python3

import os
import io
import sys
import logging
import socketserver
from http import server
from threading import Condition
from picamera2.outputs import FileOutput
from lib.helpers import get_env, exit_self
from lib.camera import create_camera

ENV = get_env()

class StreamingOutput(io.BufferedIOBase):
  def __init__(self):
    self.frame = None
    self.condition = Condition()

  def write(self, buf):
    with self.condition:
      self.frame = buf
      self.condition.notify_all()

class StreamHandler(server.BaseHTTPRequestHandler):
  def do_GET(self):
    if self.path == '/':
      self.send_response(301)
      self.send_header('Location', '/stream')
      self.end_headers()

    elif self.path == '/stream':
      self.send_response(200)
      self.send_header('Age', 0)
      self.send_header('Cache-Control', 'no-cache, private')
      self.send_header('Pragma', 'no-cache')
      self.send_header('Content-Type', 'multipart/x-mixed-replace; boundary=FRAME')
      self.end_headers()

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
          self.client_address, str(e))

    else:
      self.send_error(404)
      self.end_headers()

class CamServer(socketserver.ThreadingMixIn, server.HTTPServer):
  allow_reuse_address = True
  daemon_threads = True

if __name__ == "__main__":
  output = StreamingOutput()
  picam, encoder = create_camera()
  picam.start_recording(encoder, FileOutput(output))

  try:
    try:
      address = ('', ENV['port'])
      server = CamServer(address, StreamHandler)
      server.serve_forever()

    except Exception as e:
      exit_self(e)

    finally:
      picam.stop_recording()

  except KeyboardInterrupt:
    exit_self('KeyboardInterrupt')