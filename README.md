# Transcriber Bot
[![Generic badge](https://img.shields.io/badge/Bot-@Transcriber_bot-0d86d7.svg)](https://t.me/Transcriber_bot)
[![Generic badge](https://img.shields.io/badge/News-@Transcriber_botNewsChannel-0d86d7.svg)](https://t.me/Transcriber_botNewsChannel)

## Installation

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

5. Create your own Yandex translate token on [Yandex website](https://tech.yandex.com/translate/)

6. Edit the file **config/yandex.json** 

   `{
   	"translate_key": "YOUR YANDEX TOKEN"
   }`

## Installation with virtualenv

**Todo...**

## Installation with Docker

You can install easily with Docker.

1. Run the script **dockerBuild.sh** to generate the docker image from the Dockerfile.

2. Run the script **dockerRun.sh** to create and start the docker container.

   In the run script, the docker directories **config**, **data** and **values** are binding with the repository directory. 
   If you want to edit the files in the configuration directories you can do this simply by stopping the container.
   As soon as you finish editing the files, just restart the container  to make them active.

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
