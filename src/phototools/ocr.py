import logging

from tesserocr import PyTessBaseAPI

logger = logging.getLogger(__name__)

def image_ocr(path, lang):
  logger.info("opening %s", path)

  with PyTessBaseAPI() as api:
    api.SetImageFile(path)
    text = api.GetUTF8Text().strip()

  return text