#!/usr/bin/env bash
# 步骤3: 将 HumTrans 数据上传到 HDFS (可截取部分数据上传)
# 在 Linux 虚拟机上运行; 请先确认 HDFS 已启动: hdfs dfs -ls /
set -euo pipefail

LOCAL_ROOT="${LOCAL_ROOT:-./data/humtrans}"   # 本地解压后的根目录
HDFS_ROOT="${HDFS_ROOT:-/user/humtrans/raw}"  # HDFS 目标根目录
SAMPLE_LIMIT="${SAMPLE_LIMIT:-0}"             # >0 表示只上传前 N 个 wav(及同名 midi), 0 表示全部

WAV_DIR="$LOCAL_ROOT/wavs"
MIDI_DIR="$LOCAL_ROOT/midis"

echo "[1/4] 创建 HDFS 目录"
hdfs dfs -mkdir -p "$HDFS_ROOT/wavs" "$HDFS_ROOT/midis"

echo "[2/4] 生成本次上传清单"
LIST_FILE="upload_list.txt"
if [ "$SAMPLE_LIMIT" -gt 0 ]; then
  find "$WAV_DIR" -maxdepth 1 -name '*.wav' | sort | head -n "$SAMPLE_LIMIT" > "$LIST_FILE"
  echo "截取前 $SAMPLE_LIMIT 个 wav 上传"
else
  find "$WAV_DIR" -maxdepth 1 -name '*.wav' | sort > "$LIST_FILE"
  echo "上传全部 wav"
fi

echo "[3/4] 上传 wav 与同名 midi"
N=0
while IFS= read -r wav; do
  stem="$(basename "$wav" .wav)"
  midi="$MIDI_DIR/$stem.mid"
  hdfs dfs -put -f "$wav" "$HDFS_ROOT/wavs/"
  if [ -f "$midi" ]; then
    hdfs dfs -put -f "$midi" "$HDFS_ROOT/midis/"
  else
    echo "[warn] 缺少 MIDI: $stem"
  fi
  N=$((N+1))
done < "$LIST_FILE"

echo "[4/4] 上传清单文件"
hdfs dfs -put -f "$LIST_FILE" "$HDFS_ROOT/upload_list.txt"

echo "完成: 共上传 $N 个样本"
hdfs dfs -count "$HDFS_ROOT"
