import os
import sys
import logging
from logging.config import dictConfig

dictConfig({
  'version': 1,
  'formatters': {'default': {
    'format': '%(levelname)s: %(message)s',
  }},
  'handlers': {'wsgi': {
    'class': 'logging.StreamHandler',
    'stream': 'ext://sys.stdout',
    'formatter': 'default'
  }},
  'root': {
    'level': 'INFO',
    'handlers': ['wsgi']
  }
})

def exit_self(e=''):
  logging.info('Exiting')

  if e:
    logging.error(e)

  sys.exit(1)

def get_env():
  return {
    'width'  : int(os.getenv('CAMINATOR_VIDEO_WIDTH', 2592)),
    'height' : int(os.getenv('CAMINATOR_VIDEO_HEIGHT', 1944)),
    'quality': int(os.getenv('CAMINATOR_QUALITY', 50)),
    'port'   : int(os.getenv('CAMINATOR_PORT', 8888)),
    'host'   : str(os.getenv('CAMINATOR_HOST', '0.0.0.0')),
    'title'  : str(os.getenv('CAMINATOR_TITLE', 'Caminator')),
  }
