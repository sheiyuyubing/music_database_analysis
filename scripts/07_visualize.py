#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
步骤8/9: 可视化数据分析结果
数据源: Hive 表 humtrans.samples (PySpark 读取)
产出 5 张图 + 分析报告:
  01_pitch_by_difficulty.png  音高均值按困难等级柱状图
  02_duration_density.png     时长 vs 音符密度散点图
  03_corr_heatmap.png         特征相关系数热力图
  04_pca_clusters.png         主成分降维散点图(按困难等级着色)
  05_confusion.png            分类混淆矩阵(需 --confusion_dir 指定 ML 输出)
  analysis_report.md          分析报告文字

运行(与 Spark 同环境):
  spark-submit --master local[*] 07_visualize.py --out ../output/viz
  spark-submit --master local[*] 07_visualize.py --out ../output/viz \
      --confusion_dir /user/humtrans/ml/confusion
"""

import argparse
import os

import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

# 中文字体回退链(Linux 常见中文字体)
for fname in ["Noto Sans CJK SC", "WenQuanYi Zen Hei", "SimHei",
              "Microsoft YaHei", "DejaVu Sans"]:
    try:
        matplotlib.rcParams["font.sans-serif"] = [fname]
        break
    except Exception:
        continue
matplotlib.rcParams["axes.unicode_minus"] = False
sns.set_theme(style="whitegrid")

FEATURES = ["duration_s", "rms_db", "low_energy_ratio", "voiced_ratio",
            "note_count", "note_density", "pitch_min", "pitch_max",
            "pitch_mean", "tempo_bpm"]
NUM_FEATURES = ["duration_s", "rms_db", "low_energy_ratio", "voiced_ratio",
                "note_density", "pitch_mean", "tempo_bpm"]
DIFF_ORDER = ["U", "D", "DD", "DDD"]


def load_df(spark):
    df = spark.sql("SELECT * FROM humtrans.samples")
    pdf = df.toPandas()
    pdf = pdf.dropna(subset=FEATURES)
    for c in NUM_FEATURES:
        pdf[c] = pd.to_numeric(pdf[c], errors="coerce")
    pdf = pdf.dropna(subset=NUM_FEATURES)
    return pdf


def fig1(pdf, out):
    g = (pdf.groupby("difficulty")["pitch_mean"]
            .mean().reindex(DIFF_ORDER))
    plt.figure(figsize=(6, 4))
    g.plot(kind="bar", color="#4C78A8")
    plt.title("音高均值(半音) 按困难等级")
    plt.xlabel("困难等级")
    plt.ylabel("pitch_mean")
    plt.tight_layout()
    plt.savefig(os.path.join(out, "01_pitch_by_difficulty.png"), dpi=150)
    plt.close()


def fig2(pdf, out):
    plt.figure(figsize=(7, 5))
    sns.scatterplot(data=pdf, x="duration_s", y="note_density",
                    hue="difficulty", hue_order=DIFF_ORDER, alpha=0.7)
    plt.title("时长 vs 音符密度")
    plt.xlabel("时长 (s)")
    plt.ylabel("音符密度 (个/s)")
    plt.tight_layout()
    plt.savefig(os.path.join(out, "02_duration_density.png"), dpi=150)
    plt.close()


def fig3(pdf, out):
    corr = pdf[NUM_FEATURES].corr()
    plt.figure(figsize=(7, 6))
    sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r",
                center=0, square=True)
    plt.title("特征相关系数")
    plt.tight_layout()
    plt.savefig(os.path.join(out, "03_corr_heatmap.png"), dpi=150)
    plt.close()


def fig4(pdf, out):
    from sklearn.decomposition import PCA
    from sklearn.preprocessing import StandardScaler
    X = StandardScaler().fit_transform(pdf[NUM_FEATURES].values)
    pca = PCA(n_components=2).fit(X)
    xy = pca.transform(X)
    plt.figure(figsize=(7, 5))
    for d, color in zip(DIFF_ORDER, ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]):
        m = (pdf["difficulty"].values == d)
        plt.scatter(xy[m, 0], xy[m, 1], s=20, alpha=0.6, label=d, color=color)
    plt.title("主成分降维分布(按困难等级)")
    plt.xlabel(f"PC1 ({pca.explained_variance_ratio_[0]*100:.1f}%)")
    plt.ylabel(f"PC2 ({pca.explained_variance_ratio_[1]*100:.1f}%)")
    plt.legend(title="difficulty")
    plt.tight_layout()
    plt.savefig(os.path.join(out, "04_pca_clusters.png"), dpi=150)
    plt.close()


def fig5(confusion_dir, out):
    import glob
    files = glob.glob(os.path.join(confusion_dir, "part-*.csv"))
    if not files:
        print("[warn] 未找到混淆矩阵 part 文件, 跳过图5")
        return False
    conf = pd.read_csv(files[0])
    conf.columns = ["label", "prediction", "cnt"]
    pivot = conf.pivot_table(index="label", columns="prediction",
                             values="cnt", fill_value=0)
    plt.figure(figsize=(5, 4))
    sns.heatmap(pivot, annot=True, fmt="d", cmap="Blues", cbar=False)
    plt.title("分类混淆矩阵")
    plt.xlabel("预测")
    plt.ylabel("真实")
    plt.tight_layout()
    plt.savefig(os.path.join(out, "05_confusion.png"), dpi=150)
    plt.close()
    return True


def report(pdf, out, has_confusion):
    lines = ["# 哼唱音乐数据分析报告", ""]
    lines.append(f"- 样本数: {len(pdf)}")
    lines.append(f"- 困难等级分布: "
                 + ", ".join(f"{d}={int((pdf['difficulty']==d).sum())}"
                             for d in DIFF_ORDER))
    lines.append(f"- 平均时长: {pdf['duration_s'].mean():.2f} s")
    lines.append(f"- 平均音符密度: {pdf['note_density'].mean():.2f} 个/s")
    lines.append("")
    lines.append("## 图表说明")
    lines.append("- 图1: 音高均值随困难等级的变化, 可观察哼唱难度与音高的关系。")
    lines.append("- 图2: 时长与音符密度的分布, 反映样本复杂度差异。")
    lines.append("- 图3: 特征两两相关性, 为特征选择提供依据。")
    lines.append("- 图4: PCA 降维后样本分布, 观察各难度是否可分离。")
    if has_confusion:
        lines.append("- 图5: 随机森林分类混淆矩阵, 对角线越集中分类越准。")
    lines.append("")
    lines.append("## 结论(请结合本机运行数值补充)")
    lines.append("- 各难度等级在音高/密度上的差异: [请填写]")
    lines.append("- 对分类/聚类的业务解释: [请填写]")
    lines.append("- 数据质量问题与改进建议: [请填写]")
    with open(os.path.join(out, "analysis_report.md"), "w",
              encoding="utf-8") as f:
        f.write("\n".join(lines))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="./output/viz")
    ap.add_argument("--confusion_dir", default=None,
                    help="ML 输出中 confusion 目录(可选)")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    from pyspark.sql import SparkSession
    spark = (SparkSession.builder.appName("HumTrans-Viz")
             .config("spark.sql.warehouse.dir", "/user/hive/warehouse")
             .enableHiveSupport().getOrCreate())
    spark.sparkContext.setLogLevel("WARN")
    spark.sql("USE humtrans")

    pdf = load_df(spark)
    print(f"加载样本数: {len(pdf)}")

    fig1(pdf, args.out)
    fig2(pdf, args.out)
    fig3(pdf, args.out)
    fig4(pdf, args.out)
    has_confusion = False
    if args.confusion_dir:
        has_confusion = fig5(args.confusion_dir, args.out)
    report(pdf, args.out, has_confusion)

    print(f"可视化完成: {args.out}")
    spark.stop()


if __name__ == "__main__":
    main()
