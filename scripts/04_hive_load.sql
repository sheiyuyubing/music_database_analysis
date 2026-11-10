-- 步骤5: Hive 建表并导入预处理文本文件
-- 执行方式: hive -f 04_hive_load.sql
-- 前提: 已执行 03_preprocess.py 生成 samples.tsv 并上传到 /user/humtrans/processed/

CREATE DATABASE IF NOT EXISTS humtrans;
USE humtrans;

DROP TABLE IF EXISTS humtrans.samples;

-- 字段顺序与 samples.tsv 表头完全一致
CREATE TABLE humtrans.samples (
  stem             STRING,
  difficulty       STRING,
  duration_s       DOUBLE,
  rms_db           DOUBLE,
  low_energy_ratio DOUBLE,
  voiced_ratio     DOUBLE,
  note_count       INT,
  note_density     DOUBLE,
  pitch_min        INT,
  pitch_max        INT,
  pitch_mean       DOUBLE,
  tempo_bpm        DOUBLE
)
ROW FORMAT DELIMITED
FIELDS TERMINATED BY '\t'
LINES TERMINATED BY '\n'
STORED AS TEXTFILE;

-- 从 HDFS 加载(会移动文件到 Hive 仓库目录)
LOAD DATA INPATH '/user/humtrans/processed/samples.tsv'
OVERWRITE INTO TABLE humtrans.samples;

-- 校验
SELECT COUNT(*) AS total_rows FROM humtrans.samples;
SELECT difficulty, COUNT(*) AS cnt FROM humtrans.samples GROUP BY difficulty;
SELECT * FROM humtrans.samples LIMIT 5;
