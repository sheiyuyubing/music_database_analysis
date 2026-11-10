#!/usr/bin/env bash
# 步骤6: 用 Sqoop 把 Hive 表导出到 MySQL (可选步骤, 按课程要求保留)
# 在 Linux 虚拟机上运行; 请先确认 MySQL 已启动且账号可用
set -euo pipefail

MYSQL_HOST="${MYSQL_HOST:-localhost}"
MYSQL_PORT="${MYSQL_PORT:-3306}"
MYSQL_USER="${MYSQL_USER:-root}"
MYSQL_PASS="${MYSQL_PASS:-}"
MYSQL_DB="${MYSQL_DB:-humtrans}"
MYSQL_TABLE="${MYSQL_TABLE:-samples}"

# Hive 表在 HDFS 上的目录(LOAD 后位于 Hive 仓库; 如不同请用
#   hive -e "DESCRIBE FORMATTED humtrans.samples;" 查询 Location 后修改)
EXPORT_DIR="${EXPORT_DIR:-/user/hive/warehouse/humtrans.db/samples}"

CONN="jdbc:mysql://${MYSQL_HOST}:${MYSQL_PORT}/${MYSQL_DB}?useUnicode=true&characterEncoding=UTF-8"

echo "[1/3] 创建 MySQL 目标库表(不存在则建)"
mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" ${MYSQL_PASS:+-p"$MYSQL_PASS"} <<'SQL'
CREATE DATABASE IF NOT EXISTS humtrans CHARACTER SET utf8mb4;
USE humtrans;
CREATE TABLE IF NOT EXISTS samples (
  stem             VARCHAR(128) NOT NULL PRIMARY KEY,
  difficulty       VARCHAR(8),
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
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
SQL

echo "[2/3] Sqoop 导出 Hive 表 -> MySQL"
sqoop export \
  --connect "$CONN" \
  --username "$MYSQL_USER" \
  --password "$MYSQL_PASS" \
  --table "$MYSQL_TABLE" \
  --export-dir "$EXPORT_DIR" \
  --input-fields-terminated-by '\t' \
  --input-lines-terminated-by '\n' \
  --input-null-string '\\N' \
  --input-null-non-string '\\N'

echo "[3/3] 校验"
mysql -h"$MYSQL_HOST" -P"$MYSQL_PORT" -u"$MYSQL_USER" ${MYSQL_PASS:+-p"$MYSQL_PASS"} \
  -e "SELECT COUNT(*) AS total FROM ${MYSQL_DB}.${MYSQL_TABLE}; SELECT difficulty, COUNT(*) FROM ${MYSQL_DB}.${MYSQL_TABLE} GROUP BY difficulty;"

echo "完成"
