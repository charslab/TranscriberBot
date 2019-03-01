import zbarlight
import logging
from PIL import Image

logger = logging.getLogger(__name__)

def read_qr(path, lang):
  logger.info("opening %s", path)

  with open(path, 'rb') as f:
    image = Image.open(f)
    image.load()
    qr = zbarlight.scan_codes('qrcode', image)
    if qr is not None:
      qr = qr[0].decode("utf-8")

  return qr

