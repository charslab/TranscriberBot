#!/bin/sh

docker pull ghcr.io/charslab/transcriberbot:ptb-async
docker run \
   -e LC_ALL=C \
   -d --restart unless-stopped \
   --name "transcriberbot-async" \
   -v "$(pwd)"/data:/data \
   -v "$(pwd)"/config:/config \
   -v "$(pwd)"/values:/values \
   -v "$(pwd)"/media:/media \
   --cpus=4.0 \
   --memory=3000m \
   -u "$(id -u):1337" \
   ghcr.io/charslab/transcriberbot:ptb-async