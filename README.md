# 音乐库分析 (HumTrans 大数据管线)

课程实验: 哼唱音乐数据分析, 采用 Hadoop 生态管线
HDFS -> Hive -> Sqoop -> Spark ML -> 可视化

## 目录结构
- data/       本地下载与解压后的 HumTrans 数据
- scripts/    各步骤脚本 (按序号执行)
- output/     预处理文本、模型结果、可视化图片

## 步骤脚本
| 步骤 | 脚本 | 说明 |
|---|---|---|
| 2 | scripts/01_download_humtrans.py | 下载数据(注明来源) |
| 3 | scripts/02_upload_hdfs.sh | 上传 HDFS(可截取部分) |
| 4 | scripts/03_preprocess.py | 预处理生成文本文件 |
| 5 | scripts/04_hive_load.sql | Hive 建表并导入 |
| 6 | scripts/05_sqoop_export.sh | Sqoop 导出到 MySQL |
| 7 | scripts/06_spark_ml.py | Spark 机器学习分析 |
| 8/9 | scripts/07_visualize.py | 可视化分析结果 |

(4-9 步骤脚本随后续批次陆续生成)
