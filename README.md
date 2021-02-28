# Transcriber Bot

[![Generic badge](https://img.shields.io/badge/Bot-@Transcriber_bot-0d86d7.svg)](https://t.me/Transcriber_bot)
[![Generic badge](https://img.shields.io/badge/News-@Transcriber_botNewsChannel-0d86d7.svg)](https://t.me/Transcriber_botNewsChannel)

## Quick Start

1. Create your own Telegram bot from @BotFather and take the bot token

2. Edit the file **config/telegram.json**

   `{
   	  "username": "BOT USERNAME",
   	  "token": "BOT TOKEN",
   	  "admins": [ "YOUR TELEGRAM ID" ]
   }`

3. Create your own Wit token on [Wit website](https://wit.ai/docs/quickstart)

4. Edit the file **config/wit.json** (for example with italian token)

   `{
   	"it-IT": "WIT TOKEN FOR Italian"
   }`

   You can repeat the points 3 and 4 for support multiple languages.

   You can test if your token is working by running:

   `
   $ python src/audiotools/speech.py wit_api_key some_file.mp3 transcription.txt
   `

5. Create your own Yandex translate token on [Yandex website](https://tech.yandex.com/translate/)

6. Edit the file **config/yandex.json**

   `{
   	"translate_key": "YOUR YANDEX TOKEN"
   }`



## Installation with virtualenv

1. Install virtualenv and setuptools package

   `$ python3 -m pip install --upgrade pip`
   `$ pip3 install virtualenv setuptools`

2. Make a note of the full file path to the custom version of Python you just installed

   `$ which python3 `

3. Create the virtual environment while you specify the version of Python you wish to use

   `$ virtualenv -p /usr/bin/python3 venv`

4. Activate the new virtual environment

   `$ source venv/bin/activate`

5. Install the requirement packages

   `(venv) $ pip3 install -r requirements.txt`

6. Run the bot

   `(venv) $ python3 src/main.py`

## Installation with Docker

You can install easily with Docker.

1. Run the script **dockerBuild.sh** to generate the docker image from the Dockerfile.

2. Run the script **dockerRun.sh** to create and start the docker container.

   In the run script, the docker directories **config**, **data** and **values** are binding with the repository directory.
   If you want to edit the files in the configuration directories you can do this simply by stopping the container.
   As soon as you finish editing the files, just restart the container to make them active.

## TODO

- [x] Voice Messages
- [x] Audio Files
- [x] Video notes
- [x] Pictures
- [x] Multithreading
- [x] Stop callback
- [ ] Stats
- [x] Admin commands only in groups
- [x] Antiflood
- [x] Translations
- [ ] Voice ask
- [x] Channels support
