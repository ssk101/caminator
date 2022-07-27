from picamera2 import Picamera2
from picamera2.encoders.jpeg_encoder import JpegEncoder
from picamera2.encoders import H264Encoder
from picamera2.encoders import MJPEGEncoder
from lib.helpers import get_env

ENV = get_env()

ENCODERS = {
  'jpeg': JpegEncoder,
  'mjpeg': MJPEGEncoder,
  'h264': H264Encoder,
}

def create_camera(
  Encoder=ENCODERS['jpeg'],
  width=ENV['width'],
  height=ENV['height'],
  quality=ENV['quality']
):
  picam = Picamera2()
  video_config = picam.video_configuration(main={"size": (width, height)})
  picam.configure(video_config)
  encoder = Encoder(q=quality)
  return picam, encoder
