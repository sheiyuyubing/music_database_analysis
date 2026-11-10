#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤4: 对 HumTrans 数据进行预处理, 生成文本文件 (TSV)
输入: 本地解压后的 wav/ 与 midi/ (命名 person_music_segment_repetition_[U/D/DD/DDD])
输出: 制表符分隔的文本文件, 每行一个样本, 供 Hive 导入

字段(11个): stem difficulty duration_s rms_db low_energy_ratio voiced_ratio
             note_count note_density pitch_min pitch_max pitch_mean tempo_bpm

用法:
  python 03_preprocess.py --data_dir ../data/humtrans --out ../output/samples.tsv
  python 03_preprocess.py --data_dir ../data/humtrans --out ../output/samples.tsv --limit 200

依赖: pip install numpy soundfile librosa pretty_midi
"""

import argparse
import os
import re
import sys

import numpy as np

try:
    import soundfile as sf
    HAS_SF = True
except Exception:
    HAS_SF = False

try:
    import librosa
    HAS_LIBROSA = True
except Exception:
    HAS_LIBROSA = False

try:
    import pretty_midi
    HAS_PM = True
except Exception:
    HAS_PM = False

SR = 22050
HEADER = ["stem", "difficulty", "duration_s", "rms_db",
          "low_energy_ratio", "voiced_ratio", "note_count",
          "note_density", "pitch_min", "pitch_max", "pitch_mean",
          "tempo_bpm"]

NAME_RE = re.compile(
    r"^(?P<person>[^_]+)_(?P<music>[^_]+)_(?P<segment>[^_]+)_"
    r"(?P<repetition>[^_]+)_(?P<difficulty>[UD]+)$")


def parse_difficulty(stem: str) -> str:
    m = NAME_RE.match(stem)
    return m.group("difficulty") if m else ""


def audio_features(y: np.ndarray, sr: int):
    dur = len(y) / sr
    rms = float(np.sqrt(np.mean(y ** 2)) + 1e-12)
    rms_db = 20.0 * np.log10(rms)

    frame, hop = 1024, 512
    rms_f = librosa.feature.rms(y=y, frame_length=frame, hop_length=hop)[0]
    low_energy = float(np.mean((20.0 * np.log10(rms_f + 1e-12)) < -45.0))

    f0, voiced, _ = librosa.pyin(
        y, fmin=80.0, fmax=1000.0, sr=sr,
        frame_length=2048, hop_length=hop, fill_na=0.0)
    voiced_ratio = float(np.mean(voiced))
    return dur, rms_db, low_energy, voiced_ratio


def midi_features(midi_path: str):
    if not HAS_PM:
        return None
    pm = pretty_midi.PrettyMIDI(midi_path)
    notes = []
    for ins in pm.instruments:
        for n in ins.notes:
            notes.append((n.start, n.end, n.pitch))
    if not notes:
        return None
    note_count = len(notes)
    total = max(n.end for n in notes) - min(n.start for n in notes)
    density = note_count / total if total > 0 else float("nan")
    pitches = [n[2] for n in notes]
    p_min, p_max = int(min(pitches)), int(max(pitches))
    p_mean = float(np.mean(pitches))
    onsets = np.sort(np.array([n[0] for n in notes]))
    ioi = np.diff(onsets)
    ioi = ioi[ioi > 0]
    tempo = 60.0 / float(np.median(ioi)) if len(ioi) else float("nan")
    return note_count, density, p_min, p_max, p_mean, tempo


def process(wav_path: str, midi_path: str):
    if not (HAS_SF and HAS_LIBROSA):
        raise RuntimeError("需要 soundfile 与 librosa")
    y, fs = sf.read(wav_path, dtype="float32")
    if y.ndim > 1:
        y = y.mean(axis=1)
    if fs != SR:
        y = librosa.resample(y, orig_sr=fs, target_sr=SR)
    dur, rms_db, low, voiced = audio_features(y, SR)
    mf = midi_features(midi_path)
    if mf is None:
        note_count = density = p_min = p_max = p_mean = tempo = ""
    else:
        note_count, density, p_min, p_max, p_mean, tempo = mf
    return [dur, rms_db, low, voiced, note_count, density,
            p_min, p_max, p_mean, tempo]


def fmt(v):
    if v == "":
        return ""
    if isinstance(v, float):
        return f"{v:.4f}"
    return str(v)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--data_dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help=">0 只处理前 N 条")
    args = ap.parse_args()

    wav_dir = os.path.join(args.data_dir, "wavs")
    midi_dir = os.path.join(args.data_dir, "midis")
    if not (os.path.isdir(wav_dir) and os.path.isdir(midi_dir)):
        print("[ERROR] 找不到 wavs/ 与 midis/ 子目录", file=sys.stderr)
        sys.exit(1)

    wavs = sorted(f for f in os.listdir(wav_dir) if f.lower().endswith(".wav"))
    if args.limit > 0:
        wavs = wavs[:args.limit]

    os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\t".join(HEADER) + "\n")
        for i, w in enumerate(wavs, 1):
            stem = os.path.splitext(w)[0]
            midi_path = os.path.join(midi_dir, stem + ".mid")
            if not os.path.isfile(midi_path):
                print(f"[warn] 缺 MIDI, 跳过: {stem}", file=sys.stderr)
                continue
            try:
                feats = process(os.path.join(wav_dir, w), midi_path)
            except Exception as e:
                print(f"[warn] 处理失败 {stem}: {e}", file=sys.stderr)
                continue
            row = [stem, parse_difficulty(stem)] + [fmt(x) for x in feats]
            f.write("\t".join(row) + "\n")
            if i % 50 == 0:
                print(f"已处理 {i}/{len(wavs)}")

    print(f"完成, 输出: {args.out}")
