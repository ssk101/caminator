import picamera2
from picamera2 import Picamera2
from picamera2.encoders.jpeg_encoder import JpegEncoder
from picamera2.encoders import H264Encoder
from picamera2.encoders import MJPEGEncoder
from lib.helpers import get_env, logging

ENV = get_env()
ENCODERS = {
  'jpeg': JpegEncoder,
  'mjpeg': MJPEGEncoder,
  'h264': H264Encoder,
}

width   = ENV['width']
height  = ENV['height']

def create_camera(width=width, height=height):
  picam2 = Picamera2()
  print(picam2.camera_properties)
  picam2.video_configuration.size = (width, height)
  picam2.video_configuration.format = 'XBGR8888'
  return picam2

def create_encoder(encoder_type=ENV['encoder'], quality=ENV['quality']):
  Encoder = ENCODERS.get(encoder_type, ENV['encoder'])
  encoder = Encoder(q=quality)
  return encoder
