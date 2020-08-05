import os
import time
import torch
import numpy as np
from scipy.io.wavfile import write

from TTS.utils.generic_utils import setup_model
from TTS.utils.io import load_config
from TTS.utils.text.symbols import symbols, phonemes
from TTS.utils.audio import AudioProcessor
from TTS.utils.synthesis import synthesis

def tts(model, text, CONFIG, use_cuda, ap, use_gl):
    t_1 = time.time()
    waveform, alignment, mel_spec, mel_postnet_spec, stop_tokens, inputs = synthesis(model, text, CONFIG, use_cuda, ap, speaker_id, style_wav=None,
                                                                             truncated=False, enable_eos_bos_chars=CONFIG.enable_eos_bos_chars)
    if not use_gl:
        waveform = vocoder_model.inference(torch.FloatTensor(mel_postnet_spec.T).unsqueeze(0))
        waveform = waveform.flatten()
    if use_cuda:
        waveform = waveform.cpu()
    waveform = waveform.numpy()
    return waveform

use_cuda = False

# model paths
root = os.path.dirname(os.path.abspath(__file__))
TTS_MODEL = os.path.join(root, 'tts_model.pth.tar')
TTS_CONFIG = os.path.join(root, 'config.json')
VOCODER_MODEL = os.path.join(root, 'vocoder_model.pth.tar')
VOCODER_CONFIG = os.path.join(root, 'config_vocoder.json')
# load configs
TTS_CONFIG = load_config(TTS_CONFIG)
VOCODER_CONFIG = load_config(VOCODER_CONFIG)
TTS_CONFIG['audio']['stats_path'] = os.path.join(root, 'scale_stats.npy')
VOCODER_CONFIG['audio']['stats_path'] = os.path.join(root, 'scale_stats.npy')
# load the audio processor
ap = AudioProcessor(**TTS_CONFIG.audio)
# LOAD TTS MODEL
# multi speaker
speaker_id = None
speakers = []

# load the model
num_chars = len(phonemes) if TTS_CONFIG.use_phonemes else len(symbols)
model = setup_model(num_chars, len(speakers), TTS_CONFIG)

# load model state
cp = torch.load(TTS_MODEL, map_location=torch.device('cpu'))

# load the model
model.load_state_dict(cp['model'])
if use_cuda:
    model.cuda()
model.eval()

# set model stepsize
if 'r' in cp:
    model.decoder.set_r(cp['r'])

from TTS.vocoder.utils.generic_utils import setup_generator

# LOAD VOCODER MODEL
vocoder_model = setup_generator(VOCODER_CONFIG)
vocoder_model.load_state_dict(torch.load(VOCODER_MODEL, map_location="cpu")["model"])
vocoder_model.remove_weight_norm()
vocoder_model.inference_padding = 0

ap_vocoder = AudioProcessor(**VOCODER_CONFIG['audio'])
if use_cuda:
    vocoder_model.cuda()
vocoder_model.eval()

def run(text, fileout, noise=0):
    rate = 22050
    audios = []
    for l in text.split('\n'):
        if not l:
            continue
        if l == '%>pause':
            audios.append(np.random.randn(int(rate * 0.5))*noise)
        elif l == '%>shortpause':
            audios.append(np.random.randn(int(rate * 0.1))*noise)
        else:
            l = l.replace('%> ', '')
            print(l)
            audio = tts(model, l, TTS_CONFIG, use_cuda, ap, use_gl=False)
            audios.append(audio + np.random.randn(*audio.shape)*noise)
            audios.append(np.random.randn(int(rate * 0.3))*noise)
    if audios:
        write(fileout, rate, np.concatenate(audios))
        print(fileout, 'saved.')

if __name__ == '__main__':
    import fire
    fire.Fire(run)

