import os, glob
import xml.etree.ElementTree as ElementTree
import functools
import functional
import logging

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

logger = logging.getLogger(__name__)
strings_r = {}
__resources_directory = None

class EventHandler(FileSystemEventHandler):
  @staticmethod
  def on_any_event(event):
    if event.event_type == "modified" or event.event_type == "created":
      logger.info("Reloading resource folder")
      load_config()

def install_observer():
  handler = EventHandler()
  observer = Observer()
  observer.schedule(handler, __resources_directory)
  observer.start()

def _load_xml_resouce(path):
  logger.info("Loading resource %s", path)

  e = ElementTree.parse(path).getroot()
  lang = e.get('lang')
  if lang not in strings_r:
    strings_r[lang] = {}

  replacements = (('{b}', '<b>'), ('{/b}', '</b>'), 
  ('{i}', '<i>'), ('{/i}', '</i>'), 
  ('{code}', '<code>'), ('{/code}', '</code>'))  
  
  for string in e.findall('string'):
    if string.text is None: 
      continue

    value = functools.reduce(lambda s, kv: s.replace(*kv), replacements, string.text)
    value = value.strip()
    strings_r[lang][string.get('name')] = value
    logger.debug("Loaded string resource [%s] (%s): %s", string.get('name'), lang, value)

def load_config():
  files = glob.glob(os.path.join(__resources_directory, "strings*.xml"))
  functional.apply_fn(files, _load_xml_resouce)

def init(values_folder):
  global __resources_directory
  __resources_directory = values_folder

  load_config()
  install_observer()

def iso639_2_to_639_1(lang):
  # Convert ISO 639-2 to 639-1 based on available translations (i.e it -> it-IT)
  return next(iter(list(filter(lambda s: s.startswith(lang), strings_r.keys()))), "en-US")

def get_string_resource(id, lang=None):
  global strings_r

  if lang is not None and len(lang) < 5:
    lang = iso639_2_to_639_1(lang)

  rr = None
  if lang in strings_r and id in strings_r[lang]:
    rr = strings_r[lang][id]
  elif id in strings_r['default']:
    rr = strings_r['default'][id]

  return rr

