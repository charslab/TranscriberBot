import requests
import config

yandex_detect_url = "https://translate.yandex.net/api/v1.5/tr.json/detect?key={}"
yandex_translate_url = "https://translate.yandex.net/api/v1.5/tr.json/translate?key={}"


def detect_language(text):
  global yandex_detect_url

  r = requests.post(
    yandex_detect_url.format(config.get_config_prop("yandex")["translate_key"]), 
    data={'text': text}
  )
  res = r.json()

  if 'lang' in res:
    return res['lang']
  else:
    return None


def translate(source, target, text):
  global yandex_translate_url

  autodetect = detect_language(text)

  if autodetect is not None:
    source = autodetect
    print("Autodetected language: {0}".format(autodetect))

  lang = source + "-" + target
  print(lang)
  
  r = requests.post(
    yandex_translate_url.format(config.get_config_prop("yandex")["translate_key"]), 
    data={'lang': lang, 'text': text}
  )
  
  print(r)
  res = r.json()
  print(res)
  return str(res['text'][0]) + "\n\nPowered by Yandex.Translate http://translate.yandex.com"
