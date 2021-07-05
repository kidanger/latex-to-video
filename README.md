# latex-to-video

## Installation

System requirements:

- sox
- ffmpeg
- 'convert' from imagemagick
- conda, not mandatory

Download the weights:

```bash
$ wget https://github.com/kidanger/latex-to-video/releases/download/v1/data.tar.gz
$ tar xvf data.tar.gz
```

Tested from a fresh conda with python 3.7:

```bash
$ conda create -n tts2 python=3.7
$ conda activate tts2
$ git clone https://github.com/mozilla/TTS
$ cd TTS
$ git checkout b1935c97
$ pip install -r requirements.txt
$ python setup.py install
$ cd ..
$ pip install inflect fire mutagen iio ffmpeg-python
```

Try the TTS:

```bash
$ python tts.py 'bla bla bla' out.wav
$ play out.wav
```

Try the demo:

```bash
$ cd demo
$ latexmk -pdf main.tex
$ python ../process.py main.tex main.pdf main.mp4
$ vlc main.mp4
```

## Installation (docker)

Build the docker image locally:

```bash
$ docker build . --tag latex-to-video
```

Try the demo: (**recommended**)

```bash
$ cd demo
$ latexmk -pdf main.tex
$ docker run --rm -u (id -u) -v (pwd):/data latex-to-video main.tex main.pdf main.mp4
$ vlc main.mp4
```

## Usage

Try on your slides:

```bash
$ cd somewhere
$ latexmk main.tex -pdf
$ conda activate tts2
# remove --fast for the final build
$ python /path/to/latex-to-video/process.py main.tex main.pdf main.mp4 --fast
$ vlc main.mp4
```

```
syntax:
    %>next        -> go to next slide
    %>pause       -> 500ms pause
    %>shortpause  -> 100ms pause
    %> <text to be speeched>
```

Warning: do not use sentence that would be too long or the TTS might fail.
It works on a line per line basis, so put each sentence in its own line.

## Credits

[TTS engine by Mozilla](https://github.com/mozilla/TTS)

Code and weights of the tts taken from [colab](https://colab.research.google.com/drive/1u_16ZzHjKYFn1HNVuA4Qf_i2MMFB9olY?usp=sharing)

PDF to mp4 conversion by Charles Hessel

