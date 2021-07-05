FROM debian:bullseye-slim

RUN apt-get update \
&& apt-get install --no-install-recommends -y ca-certificates wget git python3-pip libpng-dev libtiff-dev libjpeg-dev gcc imagemagick ffmpeg sox libsox-fmt-mp3 espeak ghostscript \
&& rm -r /var/cache/apt

RUN wget https://github.com/kidanger/latex-to-video/releases/download/v1/data.tar.gz \
&& tar xvf data.tar.gz \
&& rm data.tar.gz

RUN git clone https://github.com/mozilla/TTS \
&& cd TTS \
&& git checkout b1935c97 \
&& pip3 install -r requirements.txt \
&& python3 setup.py install \
&& cd .. \
&& rm -r TTS \
&& pip install inflect fire mutagen iio ffmpeg-python \
&& rm -rf /tmp/pip \
&& rm -rf /root/.cache

COPY process.py .
COPY tts.py .

# current version of imagemagick prevent reading from pdf or something
RUN sed -i 's/none/read|write/g' /etc/ImageMagick-6/policy.xml

WORKDIR /data
RUN useradd 1000 && chown -R 1000 . \
    && mkdir /home/1000 && chown 1000:1000 /home/1000
USER 1000
ENTRYPOINT ["python3", "/process.py"]

