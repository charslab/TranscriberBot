#!/bin/sh

# docker pull ghcr.io/charslab/transcriberbot:development
docker build -t transcriberbot .
docker run \
   -e LC_ALL=C \
   -d --restart unless-stopped \
   --name "transcriberbot" \
   -v "$(pwd)"/data:/data \
   -v "$(pwd)"/config:/config \
   -v "$(pwd)"/values:/values \
   -v "$(pwd)"/media:/media \
   --cpus=4.0 \
   --memory=3000m \
   -u "$(id -u):1337" \
   --net=host \
   transcriberbot