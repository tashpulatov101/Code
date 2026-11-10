import sys, torch, numpy as np, scipy.io.wavfile as wf
from transformers import VitsModel, AutoTokenizer
from transformers.utils import logging; logging.set_verbosity_error()
M, src, out = sys.argv[1], sys.argv[2], sys.argv[3]
tok = AutoTokenizer.from_pretrained(M); model = VitsModel.from_pretrained(M).eval()
model.config.speaking_rate = 0.95; model.config.noise_scale = 0.55
sr = model.config.sampling_rate
lines = [l.strip() for l in open(src, encoding="utf-8") if l.strip()]
for i, t in enumerate(lines):
    parts = []
    for ph in t.split("/"):
        torch.manual_seed(7)
        with torch.no_grad(): w = model(**tok(ph.strip(), return_tensors="pt")).waveform[0].numpy()
        parts += [w / np.abs(w).max() * 0.9, np.zeros(int(0.22 * sr))]
    w = np.concatenate(parts[:-1])
    wf.write(f"{out}/v{i}.wav", sr, (w * 32767).astype(np.int16))
    print(i, round(len(w) / sr, 2))
