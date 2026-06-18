"""Convert 16-bit mono PCM WAV to 64kbps MP3 (22050 Hz, mono).

Vectorized resample via numpy; encoding via lameenc (libmp3lame wheel).
No external ffmpeg needed.

Usage:
  python wav2mp3.py <input.wav> <output.mp3>
"""
import sys
sys.path.insert(0, r"C:\Users\Administrator\.workbuddy\binaries\python\site-packages")
import wave
import time
import struct
import numpy as np
import lameenc

def resample_linear(samples: np.ndarray, in_rate: int, out_rate: int) -> np.ndarray:
    """Vectorized linear-interpolation resample."""
    n_in = samples.shape[0]
    n_out = int(round(n_in * out_rate / in_rate))
    if n_out == n_in:
        return samples
    t_in = np.arange(n_in, dtype=np.float64)
    t_out = np.linspace(0, n_in - 1, n_out, dtype=np.float64)
    i0 = np.floor(t_out).astype(np.int64)
    frac = t_out - i0
    i1 = np.minimum(i0 + 1, n_in - 1)
    out = samples[i0] * (1.0 - frac) + samples[i1] * frac
    return out.astype(np.int16, copy=False)

def convert(src: str, dst: str, bit_rate: int = 64, out_rate: int = 22050) -> None:
    t0 = time.time()
    with wave.open(src, "rb") as w:
        in_rate = w.getframerate()
        in_channels = w.getnchannels()
        sampwidth = w.getsampwidth()
        nframes = w.getnframes()
        assert sampwidth == 2, f"expected 16-bit PCM, got sampwidth={sampwidth}"
        assert in_channels == 1, f"expected mono, got channels={in_channels}"
        print(f"src: {src}")
        print(f"  rate={in_rate}  ch={in_channels}  bits={sampwidth*8}  duration={nframes/in_rate:.1f}s  frames={nframes}")

        # Read all frames at once — 116MB at int16 = ~58M samples, well under memory
        raw = w.readframes(nframes)
    samples = np.frombuffer(raw, dtype="<i2").astype(np.float64)
    if in_rate != out_rate:
        samples = resample_linear(samples, in_rate, out_rate)
    else:
        samples = samples.astype(np.float64)

    enc = lameenc.Encoder()
    enc.set_bit_rate(bit_rate)
    enc.set_in_sample_rate(out_rate)
    enc.set_channels(1)
    enc.set_quality(5)

    FRAME = 1152
    pad = (-len(samples)) % FRAME
    if pad:
        samples = np.concatenate([samples, np.zeros(pad, dtype=samples.dtype)])
    pcm = samples.astype(np.int16).tobytes()

    written = 0
    CHUNK_FRAMES = 1152 * 64  # 73728 frames / chunk
    with open(dst, "wb") as out:
        i = 0
        total_bytes = len(pcm)
        while i < total_bytes:
            chunk = pcm[i:i + CHUNK_FRAMES * 2]
            mp3 = enc.encode(chunk)
            if mp3:
                out.write(mp3)
                written += len(mp3)
            i += CHUNK_FRAMES * 2
        tail = enc.flush()
        if tail:
            out.write(tail)
            written += len(tail)
    dt = time.time() - t0
    print(f"dst: {dst}")
    print(f"  size={written/1024/1024:.2f} MB  bitrate={bit_rate}kbps  out_rate={out_rate}  time={dt:.1f}s")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print(__doc__, file=sys.stderr)
        sys.exit(2)
    convert(sys.argv[1], sys.argv[2])
