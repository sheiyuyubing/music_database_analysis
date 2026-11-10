#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤7: Spark 机器学习/人工智能分析 (PySpark)
任务1: 困难等级分类 (RandomForestClassifier)
任务2: 哼唱风格聚类 (KMeans)
数据源: Hive 表 humtrans.samples (由 04_hive_load.sql 导入)

提交方式(spark-submit 会保证 Hive 元数据可见):
  spark-submit --master yarn --deploy-mode client 06_spark_ml.py --out /user/humtrans/ml
  (单机可用: spark-submit --master local[*] 06_spark_ml.py --out ./output/ml)

输出(写入 --out 指定目录):
  confusion.csv          分类混淆矩阵
  cluster_result.csv     每个样本的聚类簇编号
  metrics.json           模型评估指标
"""

import argparse
import json

from pyspark.sql import SparkSession, functions as F
from pyspark.ml import Pipeline
from pyspark.ml.feature import StringIndexer, VectorAssembler, StandardScaler
from pyspark.ml.classification import RandomForestClassifier
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import MulticlassClassificationEvaluator

FEATURES = ["duration_s", "rms_db", "low_energy_ratio", "voiced_ratio",
            "note_count", "note_density", "pitch_min", "pitch_max",
            "pitch_mean", "tempo_bpm"]


def build_spark():
    spark = (SparkSession.builder
             .appName("HumTrans-ML")
             .config("spark.sql.warehouse.dir", "/user/hive/warehouse")
             .enableHiveSupport()
             .getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    return spark


def save_csv(df, spark, path):
    (df.coalesce(1)
       .write.mode("overwrite")
       .option("header", "true")
       .csv(path))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="/user/humtrans/ml")
    args = ap.parse_args()

    spark = build_spark()
    spark.sql("USE humtrans")

    # 1) 读取并清洗
    df = (spark.sql("SELECT * FROM humtrans.samples")
          .dropna(subset=FEATURES + ["difficulty"]))
    print(f"样本数(清洗后): {df.count()}")

    # 2) 特征装配 + 标准化
    assembler = VectorAssembler(inputCols=FEATURES, outputCol="features")
    scaler = StandardScaler(inputCol="features", outputCol="scaled",
                            withStd=True, withMean=True)

    # 3) 任务1: 困难等级分类
    indexer = StringIndexer(inputCol="difficulty", outputCol="label")
    rf = RandomForestClassifier(featuresCol="scaled", labelCol="label",
                                numTrees=50, maxDepth=8, seed=42)
    pipe = Pipeline(stages=[assembler, scaler, indexer, rf])
    train, test = df.randomSplit([0.8, 0.2], seed=42)
    model = pipe.fit(train)
    pred = model.transform(test)

    acc = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="accuracy")
    f1 = MulticlassClassificationEvaluator(
        labelCol="label", predictionCol="prediction", metricName="f1")
    accuracy = acc.evaluate(pred)
    f1_score = f1.evaluate(pred)
    print(f"分类 Accuracy={accuracy:.4f}, F1={f1_score:.4f}")

    conf = (pred.groupBy("label", "prediction").count()
            .withColumnRenamed("count", "cnt"))
    save_csv(conf, spark, args.out + "/confusion")
    print("混淆矩阵已写入 confusion.csv")

    # 4) 任务2: KMeans 哼唱风格聚类
    k = 4
    scaled_df = scaler.fit(assembler.transform(df)).transform(
        assembler.transform(df))
    km = KMeans(featuresCol="scaled", k=k, seed=42)
    km_model = km.fit(scaled_df)
    clustered = km_model.transform(scaled_df).select(
        "stem", "difficulty", "prediction")

    save_csv(clustered.withColumnRenamed("prediction", "cluster"),
             spark, args.out + "/cluster_result")
    print("聚类结果已写入 cluster_result.csv")

    cluster_stat = (clustered.groupBy("difficulty", "prediction").count()
                    .orderBy("difficulty", "prediction"))
    cluster_stat.show()

    # 5) 汇总指标
    metrics = {
        "classification_accuracy": accuracy,
        "classification_f1": f1_score,
        "kmeans_k": k,
        "train_count": train.count(),
        "test_count": test.count(),
        "feature_columns": FEATURES,
    }
    spark.sparkContext.parallelize([json.dumps(metrics, ensure_ascii=False)]) \
        .coalesce(1).saveAsTextFile(args.out + "/metrics")
    print(json.dumps(metrics, ensure_ascii=False, indent=2))

    spark.stop()


if __name__ == "__main__":
    main()

