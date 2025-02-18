import logging

from tesserocr import PyTessBaseAPI

logger = logging.getLogger(__name__)


def image_ocr(path, lang):
    return image_ocr_tesserocr(path, lang)


def image_ocr_docts(path, lang):
    from doctr.models import ocr_predictor

    predictor = ocr_predictor.create_predictor()

    # Perform OCR on the image
    predictor(path)


def image_ocr_easyocr(path, lang):
    import easyocr

    logger.info("opening %s", path)

    reader = easyocr.Reader(['en'], gpu=False)
    result = reader.readtext(path)
    text = " ".join([x[1] for x in result])

    return text


def image_ocr_tesserocr(path, lang):
    logger.info("opening %s", path)

    with PyTessBaseAPI(path='/usr/share/tesseract-ocr/5/tessdata/') as api:
        api.SetImageFile(path)
        text = api.GetUTF8Text().strip()

    return text
