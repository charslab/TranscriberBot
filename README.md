# Transcriber Bot

[![Generic badge](https://img.shields.io/badge/Bot-@Transcriber_bot-0d86d7.svg)](https://t.me/Transcriber_bot)
[![Generic badge](https://img.shields.io/badge/News-@Transcriber_botNewsChannel-0d86d7.svg)](https://t.me/Transcriber_botNewsChannel)

## Quick Start

1. Create your own Telegram bot from @BotFather and take the bot token

2. Edit the file **config/telegram.json**

   ```json
   {
   	  "username": "BOT USERNAME",
   	  "token": "BOT TOKEN",
   	  "admins": [ "YOUR TELEGRAM ID" ]
   }
   ```

3. Create your own Wit token on [Wit website](https://wit.ai/docs/quickstart)

4. Edit the file **config/wit.json** (for example with italian token)

   ```json
   {
   	"it-IT": "WIT TOKEN FOR Italian"
   }
   ```

   You can repeat the points 3 and 4 for support multiple languages.

   You can test if your token is working by running: `python src/audiotools/speech.py wit_api_key some_file.mp3 transcription.txt`

5. Create your own Yandex translate token on [Yandex website](https://tech.yandex.com/translate/)

6. Edit the file **config/yandex.json**

   ```json
   {
   	"translate_key": "YOUR YANDEX TOKEN"
   }
   ```

## Running with Docker

We provide prebuilt images on [ghcr.io](https://github.com/charslab/TranscriberBot/pkgs/container/transcriberbot).
See **[run.sh](https://github.com/charslab/TranscriberBot/blob/developement/run.sh)** to start a docker container with the latest release.

Altenratevely, you can build the image from the Dockerfile with **[build.sh](https://github.com/charslab/TranscriberBot/blob/developement/build.sh)** 

In **[run.sh](https://github.com/charslab/TranscriberBot/blob/developement/run.sh)**, the docker directories **config**, **data** and **values** are binding with the repository directory.
If you want to edit the files in the configuration directories you can do this simply by stopping the container.
As soon as you finish editing the files, just restart the container to make them active.


## Running with virtualenv

Tested with: `python 3.12.0`

First, install the required dependencies (Ubuntu):

```bash
sudo apt install tesseract-ocr libtesseract-dev libleptonica-dev libpython3-dev libzbar-dev
```
Create a virtual environment and install the required packages:

```bash
python3 -m venv transcriber-bot
source transcriber-bot/bin/activate
pip install -r requirements.txt
```
Run the bot:

```
cd src
python3 main.py
```




