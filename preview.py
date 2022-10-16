#!/usr/bin/python3

import time
import numpy as np
from picamera2 import Picamera2, Preview
from lib.helpers import get_env, exit_self

ENV = get_env()

if __name__ == "__main__":
  try:
    try:
      picam2 = Picamera2()
      picam2.start_preview(Preview.QTGL, width=ENV['width'], height=ENV['height'])


      preview_config = picam2.create_preview_configuration(
        {'size': (ENV['width'], ENV['height'])}
      )
      picam2.configure(preview_config)
      picam2.start()

      while not time.sleep(30):
        print('Still running')

    except Exception as e:
      exit_self(e)


  except KeyboardInterrupt:
    exit_self('KeyboardInterrupt')