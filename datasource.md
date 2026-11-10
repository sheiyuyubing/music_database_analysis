# 数据来源说明 (HumTrans)

| 项目 | 内容 |
|---|---|
| 数据集名称 | HumTrans |
| 全称 | Humming Melody Transcription Dataset |
| 论文 | Shansong Liu, Xu Li, Dian Li, Ying Shan, "HumTrans: A Novel Open-Source Dataset for Humming Melody Transcription and Beyond", IEEE ICASSP 2024 |
| 官方仓库 | https://huggingface.co/datasets/dadinghh2/HumTrans |
| 镜像下载 | 设置环境变量 HF_ENDPOINT=https://hf-mirror.com |
| 许可 | Creative Commons Attribution 4.0 (CC-BY-4.0) |
| 规模 | 56.22 小时哼唱音频, 1000 段, 500 首曲目, 20 位演唱者 |
| 数据内容 | 音频 all_wav.zip (.wav) + 对应标签 all_midi.zip (.mid) |
| 命名规则 | personID_musicID_segmentID_repetitionID_[U/D/DD/DDD] |
| 困难等级 | U=无困难, D=1种, DD=2种, DDD=3种及以上 |

## 下载命令

```bash
cd scripts
python 01_download_humtrans.py --out_dir ../data/humtrans
```

访问受限时改用镜像：

```bash
HF_ENDPOINT=https://hf-mirror.com python 01_download_humtrans.py --out_dir ../data/humtrans
```

## 上传 HDFS

```bash
cd scripts
LOCAL_ROOT=../data/humtrans HDFS_ROOT=/user/humtrans/raw bash 02_upload_hdfs.sh
```

只截取前 200 条上传：

```bash
SAMPLE_LIMIT=200 LOCAL_ROOT=../data/humtrans bash 02_upload_hdfs.sh
```
