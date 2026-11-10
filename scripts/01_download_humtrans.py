#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤2: 下载 HumTrans 数据集 (注明数据来源)
数据来源:
  - 名称: HumTrans (Humming Melody Transcription)
  - 论文: Shansong Liu, Xu Li, Dian Li, Ying Shan,
          "HumTrans: A Novel Open-Source Dataset for Humming Melody
           Transcription and Beyond", ICASSP 2024.
  - 仓库: https://huggingface.co/datasets/dadinghh2/HumTrans
  - 许可: Creative Commons Attribution 4.0 (CC-BY-4.0)
  - 规模: 56.22 小时哼唱音频, 1000 段, 500 首曲目, 20 位演唱者;
          音频 .wav + 对应标签 .mid, 命名 person_music_segment_repetition_[U/D/DD/DDD]

用法:
  python 01_download_humtrans.py --out_dir ./data/humtrans
  使用镜像: HF_ENDPOINT=https://hf-mirror.com python 01_download_humtrans.py --out_dir ./data/humtrans
"""

import argparse
import os
import shutil
import subprocess
import sys
import zipfile

REPO_ID = "dadinghh2/HumTrans"
FILES = ["all_wav.zip", "all_midi.zip", "README.md"]


def download_file(filename: str, out_dir: str) -> str:
    dest = os.path.join(out_dir, filename)
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        print(f"[skip] 已存在: {dest}")
        return dest

    try:
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(
            repo_id=REPO_ID, filename=filename,
            local_dir=out_dir, repo_type="dataset",
        )
        print(f"[ok] {filename} -> {path}")
        return path
    except Exception as e:
        print(f"[warn] huggingface_hub 下载失败: {e}")
        print("[info] 回退到直接 HTTP 下载 (支持 HF_ENDPOINT 镜像)")

    base = os.environ.get("HF_ENDPOINT", "https://huggingface.co")
    url = f"{base}/datasets/{REPO_ID}/resolve/main/{filename}"
    print(f"[info] 下载 {url}")
    ret = subprocess.run(
        ["curl", "-L", "--fail", "-o", dest, url],
        check=False,
    )
    if ret.returncode != 0:
        raise RuntimeError(f"下载失败: {url} (可设置 HF_ENDPOINT=https://hf-mirror.com 重试)")
    return dest


def extract_zip(zip_path: str, dest_dir: str) -> None:
    os.makedirs(dest_dir, exist_ok=True)
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dest_dir)
    print(f"[ok] 解压 {zip_path} -> {dest_dir}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out_dir", default="./data/humtrans")
    args = ap.parse_args()
    os.makedirs(args.out_dir, exist_ok=True)

    print(f"数据来源: {REPO_ID}  (CC-BY-4.0)")
    for f in FILES:
        p = download_file(f, args.out_dir)

    wav_zip = os.path.join(args.out_dir, "all_wav.zip")
    midi_zip = os.path.join(args.out_dir, "all_midi.zip")
    extract_zip(wav_zip, os.path.join(args.out_dir, "wavs"))
    extract_zip(midi_zip, os.path.join(args.out_dir, "midis"))

    n_wav = len([x for x in os.listdir(os.path.join(args.out_dir, "wavs"))
                 if x.lower().endswith(".wav")])
    n_mid = len([x for x in os.listdir(os.path.join(args.out_dir, "midis"))
                 if x.lower().endswith(".mid")])
    print(f"完成: wav={n_wav}, midi={n_mid}")


if __name__ == "__main__":
    main()
