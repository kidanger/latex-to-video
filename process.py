#!/usr/bin/env python3

'''
follow the "# NOTE:" for some details

usage:
    (the main.pdf should be generated first)
    $ python process.py main.tex main.pdf main.mp4 [--fast]
    use --fast to do a fast run (video low resolution = fast encoding)
'''

import os
import sys
import errno
from tts import run
from mutagen.mp3 import MP3
import iio
import numpy as np
import ffmpeg

framerate = 24
vcodec='libx264'
# vcodec='h264_nvenc'
pix_fmt='yuv420p'
crf=18
preset='slow'

def main(tex, pdf, vid, fast=False):
    lines = open(tex).readlines()
    lines = [l.strip() for l in lines]
    lines = list(filter(lambda l: '%>' in l, lines))
    cur = -1
    frames = {}
    for l in lines:
        if l == '%>next':
            cur += 1
            frames[cur] = []
        elif l == '%>stop':
            break
        else:
            frames[cur].append(l)

    tmpdir = 'slides'
    try: os.makedirs(tmpdir)
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(tmpdir): pass
        else: raise
    density = 304.8 if not fast else 61
    command = f'convert -verbose -density {density} {pdf} {tmpdir}/%d.png'
    print(f'Executing command: {command}')
    os.system(command)

    # NOTE: the audio files are cached if the next did not change of a slide
    # delete the folder to clear the cache
    try: os.makedirs('audios')
    except OSError as exc:
        if exc.errno == errno.EEXIST and os.path.isdir(tmpdir): pass
        else: raise

    lengths = {}
    for i in sorted(frames.keys()):
        text = '\n'.join(frames[i])
        oldtext = ''
        try:
            oldtext = open(f'audios/{i}.wav.txt', 'r').read()
        except:
            pass
        if text != oldtext:
            # NOTE: the noise is just to make it a bit more real
            run(text, f'audios/{i}.wav', noise=0.0005)
            with open(f'audios/{i}.wav.txt', 'w') as f:
                f.write(text)
        # NOTE: feel free to adjust this sox processing (eg change the pitch to -500)
        os.system(f'sox audios/{i}.wav audios/{i}.mp3 reverb 25 25 lowpass -1 2500 pitch 0 rate -v 44100 tempo 1.05')
        length = MP3(f'audios/{i}.mp3').info.length
        lengths[i] = length
        print(i, length)
    files = ' '.join(f'audios/{i}.mp3' for i in sorted(frames.keys()))
    os.system(f'sox --combine concatenate {files} audio.mp3')

    images = {}
    for f in sorted(frames.keys()):
        p = f'slides/{f}.png'
        i = iio.read(p)
        print(f'{p}: {i.shape}')
        if i.shape[2] == 3:
            pass
        elif i.shape[2] == 4:
            # i.e. with an alpha channel (in [0., 255.])
            # 255 seems to mean opaque, so I guess 0 is fully transparent
            i = i[:,:,0:3] * (i[:,:,3:] / 255.) \
                + np.full(i.shape, 255.)[:,:,0:3] * (1. - i[:,:,3:] / 255.)
            print(f'{p}: {i.shape} (same image, removed alpha channel)')
        elif i.shape[2] == 1:  # iio gives (h, w, 1) shape for gray images
            i = np.repeat(i, 3, axis=2)
            print(f'{p}: {i.shape} (same image, replicated single channel)')
        else:
            print(f'ERROR: Incorrect number of channels in image {p}')
            raise ValueError

        i = i.astype(np.uint8)
        images[f] = i.astype(np.uint8)

    height, width, channels = i.shape
    audio_stream = ffmpeg.input('audio.mp3')
    process = (
            ffmpeg
            .input('pipe:',
                   format='rawvideo',
                   pix_fmt='rgb24',
                   s='{}x{}'.format(width, height),
                   r=framerate)
            .concat(audio_stream.audio, a=1)
            .output(vid,
                    pix_fmt=pix_fmt,
                    crf=crf,
                    preset=preset,
                    vcodec=vcodec,
                    r=framerate,
                    tune='stillimage')
            .overwrite_output()
            .run_async(pipe_stdin=True)
            )

    for f in sorted(frames.keys()):
        frame = images[f]
        l = lengths[f]
        print(f, l)
        # TODO: this rounding can produce desync between audio and video
        # should use a counter and compare with the cumulated lengths
        for _ in range(int(l * framerate)):
            process.stdin.write(
                    frame
                    .astype(np.uint8)
                    .tobytes()
            )

    process.stdin.close()
    process.wait()

if __name__ == '__main__':
    import fire
    fire.Fire(main)
