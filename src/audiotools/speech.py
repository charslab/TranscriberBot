import functional
import requests
import config
import logging
import traceback
import pydub
import io

from pydub import AudioSegment

logger = logging.getLogger("speech")

def __transcribe_chunk(chunk, lang):
  if lang not in config.get_config_prop("wit"):
    logger.error("Language not found in wit.json %s", lang)
    return None

  logging.debug("Using key %s %s", lang, config.get_config_prop("wit")[lang])

  headers = {
    'authorization': 'Bearer ' + config.get_config_prop("wit")[lang],
    'accept': 'application/vnd.wit.20180705+json',
    'content-type': 'audio/raw;encoding=signed-integer;bits=16;rate=8000;endian=little',
  }

  text = None
  try: 
    request = requests.request(
      "POST",
      "https://api.wit.ai/speech", 
      headers=headers, 
      params = {'verbose': True},
      data=io.BufferedReader(io.BytesIO(chunk.raw_data))
    )

    logger.debug("Request response %s", request.text)
    res = request.json()
  
    if '_text' in res:
      text = res['_text']

  except Exception as e:
    logger.error("Could not transcribe chunk: %s", traceback.format_exc())

  return text

def __generate_chunks(segment, length=20, split_on_silence=False, noise_threshold=-16): 
  chunks = list()
  if split_on_silence is False:
    for i in range(0, len(segment), length*1000):
      chunks.append(segment[i:i+length*1000])
  else:
    chunks = pydub.silence.split_on_silence(segment, noise_threshold)
    for i, chunk in enumerate(chunks):
      if len(chunk) > length*1000:
        subchunks = __generate_chunks(chunk, length, split_on_silence, noise_threshold+4)
        chunks = chunks[:i-1] + subchunks + chunks[i+1:]

  return chunks

def __preprocess_audio(audio):
  return audio.set_sample_width(2).set_channels(1).set_frame_rate(8000)

def transcribe(path, lang):
  logging.info("Transcribing file %s", path)
  audio = AudioSegment.from_file(path)

  chunks = __generate_chunks(__preprocess_audio(audio))
  logging.debug("Got %d chunks", len(chunks))

  for i, chunk in enumerate(chunks):
    logging.debug("Transcribing chunk %d", i)
    r = __transcribe_chunk(chunk, lang)
    logging.debug(r)

    if r is not None:
      yield r