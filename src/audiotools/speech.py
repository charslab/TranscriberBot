import io
import logging
import traceback

import requests
import pydub
from pydub import AudioSegment


logger = logging.getLogger("speech")

def __transcribe_chunk(chunk, api_key):
  headers = {
    'authorization': 'Bearer ' + api_key,
    'accept': 'application/vnd.wit.20180705+json',
    'content-type': 'audio/raw;encoding=signed-integer;bits=16;rate=8000;endian=little',
  }

  text = None
  try:
    request = requests.request(
      "POST",
      "https://api.wit.ai/speech",
      headers=headers,
      params={'verbose': True},
      data=io.BufferedReader(io.BytesIO(chunk.raw_data))
    )

    logger.debug("Request response %s", request.text)
    res = request.json()

    if '_text' in res:
      text = res['_text']
    elif 'text' in res:  # Changed in may 2020
      text = res['text']

  except Exception as e:
    logger.error("Could not transcribe chunk: %s", traceback.format_exc())

  return text

def __generate_chunks(segment, length=20000/1001, split_on_silence=False, noise_threshold=-36):
  chunks = list()
  if split_on_silence is False:
    for i in range(0, len(segment), int(length*1000)):
      chunks.append(segment[i:i+int(length*1000)])
  else:
    while len(chunks) < 1:
      logger.debug('split_on_silence (threshold %d)', noise_threshold)
      chunks = pydub.silence.split_on_silence(segment, noise_threshold)
      noise_threshold += 4

    for i, chunk in enumerate(chunks):
      if len(chunk) > int(length*1000):
        subchunks = __generate_chunks(chunk, length, split_on_silence, noise_threshold+4)
        chunks = chunks[:i-1] + subchunks + chunks[i+1:]

  return chunks

def __preprocess_audio(audio):
  return audio.set_sample_width(2).set_channels(1).set_frame_rate(8000)


def transcribe(path, api_key):
  logger.info("Transcribing file %s", path)
  audio = AudioSegment.from_file(path)

  chunks = __generate_chunks(__preprocess_audio(audio))
  logger.debug("Got %d chunks", len(chunks))

  for i, chunk in enumerate(chunks):
    logger.debug("Transcribing chunk %d", i)
    r = __transcribe_chunk(chunk, api_key)
    logger.debug("Response received: %s", r)

    if r is not None:
      yield r


if __name__ == "__main__":
  import argparse
  import sys

  parser = argparse.ArgumentParser()
  parser.add_argument("api_key")
  parser.add_argument("input_filename")
  parser.add_argument("output_filename")
  args = parser.parse_args()

  if args.output_filename == "-":
      output = sys.stdout
  else:
      output = open(args.output_filename, mode="w")

  result = transcribe(args.input_filename, args.api_key)
  for part in result:
      output.write(part + "\n")
      output.flush()

  output.close()
