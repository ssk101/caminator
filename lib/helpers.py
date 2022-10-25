import os
import sys
import json
from pathlib import Path
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

cwd = Path(os.getcwd())

with open(cwd / 'config.json') as config_file:
  config = json.load(config_file)

def exit_self(e=''):
  logging.info('Exiting')

  if e:
    logging.error(e)

  sys.exit(1)

def get_env():
  logging.info(os.getenv('CAMINATOR_FRAME_DELAY'))
  return {
    'width'        : int(os.getenv('CAMINATOR_WIDTH', config.get('width', 1296))),
    'height'       : int(os.getenv('CAMINATOR_HEIGHT', config.get('height', 972))),
    'encoder'      : str(os.getenv('CAMINATOR_ENCODER', config.get('encoder', 'jpeg'))),
    'quality'      : int(os.getenv('CAMINATOR_QUALITY', config.get('quality', 75))),
    'frame_delay'  : float(os.getenv('CAMINATOR_FRAME_DELAY', config.get('frame_delay', 0.1))),
    'port'         : int(os.getenv('CAMINATOR_PORT', config.get('port', 8888))),
    'host'         : str(os.getenv('CAMINATOR_HOST', config.get('host', '0.0.0.0'))),
    'title'        : str(os.getenv('CAMINATOR_TITLE', config.get('title', 'Caminator'))),
  }
