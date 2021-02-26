FROM python:3.8.5-buster
RUN apt-get update
RUN apt-get install libzbar-dev libleptonica-dev libtesseract-dev ffmpeg -y
RUN rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN export LC_ALL=C
RUN export LC_CTYPE=C
RUN export LC_NUMERIC=C
RUN pip3 install -r requirements.txt
RUN pip cache purge
COPY src/ src/
CMD [ "python3.8", "src/main.py" ]

