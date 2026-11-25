import importlib.util
import tempfile
import types
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, Mock, patch


with patch.dict("sys.modules", {
    "config": Mock(),
    "phototools": Mock(),
    "resources": Mock(),
    "database": Mock(),
}):
    spec = importlib.util.spec_from_file_location(
        "photos", Path(__file__).resolve().parents[1] / "transcriberbot/blueprints/photos.py"
    )
    assert spec is not None and spec.loader is not None
    photos = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(photos)


class PhotoSettingsTests(unittest.IsolatedAsyncioTestCase):
    async def test_photo_settings_and_results(self):
        cases = [
            # chat type, OCR enabled, QR enabled, QR result, OCR result, expected reply
            ("group", False, False, None, None, None),
            ("group", False, True, None, None, None),
            ("group", False, True, "code", None, "qr_result\ncode"),
            ("group", True, False, "code", "hello", "ocr_result\nhello"),
            ("group", True, False, "code", None, "photo_no_text"),
            ("group", True, True, "code", "hello", "qr_result\ncode"),
            ("group", True, True, None, "hello", "ocr_result\nhello"),
            ("group", True, True, None, None, "photo_no_text"),
            ("private", False, False, None, None, "photo_no_text"),
        ]
        for chat_type, ocr_enabled, qr_enabled, qr, text, expected in cases:
            with self.subTest(chat_type=chat_type, ocr=ocr_enabled, qr=qr_enabled, result=qr):
                with tempfile.TemporaryDirectory() as directory:
                    photos.config.get_config_prop.return_value = {"media_path": directory}
                    photos.TBDB.get_chat_photos_enabled.return_value = ocr_enabled
                    photos.TBDB.get_chat_qr_enabled.return_value = qr_enabled
                    photos.TBDB.get_chat_lang.return_value = "en"
                    photos.R.get_string_resource.side_effect = lambda key, lang: key
                    photos.phototools.read_qr.reset_mock(return_value=True, side_effect=True)
                    photos.phototools.image_ocr.reset_mock(return_value=True, side_effect=True)
                    photos.phototools.read_qr.return_value = qr
                    photos.phototools.image_ocr.return_value = text
                    file = types.SimpleNamespace(download_to_drive=AsyncMock())
                    async def download(path):
                        Path(path).touch()
                    file.download_to_drive.side_effect = download
                    bot = types.SimpleNamespace(get_file=AsyncMock(return_value=file), send_message=AsyncMock())
                    message = types.SimpleNamespace(id=42, photo=[types.SimpleNamespace(file_id="image")])
                    update = types.SimpleNamespace(effective_chat=types.SimpleNamespace(id=1, type=chat_type),
                                                   effective_message=message, message=message, channel_post=None)
                    await photos.photo(update, types.SimpleNamespace(bot=bot))
                    if expected is None:
                        bot.send_message.assert_not_awaited()
                    else:
                        self.assertEqual(bot.send_message.await_args.kwargs["text"], expected)
                    if chat_type != "private" and not qr_enabled:
                        photos.phototools.read_qr.assert_not_called()
                    if chat_type != "private" and not ocr_enabled:
                        photos.phototools.image_ocr.assert_not_called()
                    self.assertFalse(Path(directory, "image").exists())


if __name__ == "__main__":
    unittest.main()
