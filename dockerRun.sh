docker run \
   -e LC_ALL=C \
   -d --restart unless-stopped \
   -v "$(pwd)"/data:/data \
   -v "$(pwd)"/config:/config \
   -v "$(pwd)"/values:/values \
   transcriberbot
