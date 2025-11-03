#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Protein Ensemble Analysis Script
--------------------------------
Analyzes PDB ensembles, computing:
 - File size (MB)
 - Sequence length (first model)
 - Summary statistics and distributions
 - Sequence length vs. file size relationship

Output:
 - TSV files with detailed and summary data
 - Plots (distribution and correlation)
 - Readable text report
"""

import os
import warnings
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === CONFIGURATION ===
folders = [
#    "/home/balbio/unipd/ped_deposition/AlphaFlex-IDPCG_cat2/completed_mediumF",
    "/home/balbio/unipd/ped_deposition/AlphaFlex-IDPCG_cat3/completed_hardF_idpcg",
]

# Sequence length bins
seq_bins = list(range(0, 2551, 50))  # 0–50, 51–100, ...
seq_labels = [f"{i+1}-{i+50}" for i in seq_bins[:-1]]
seq_labels.append(">2500")

# Suppress unhelpful warnings
warnings.filterwarnings("ignore", category=FutureWarning)


# === CORE FUNCTION ===
def analyze_pdb(path):
    """Compute file size and protein length for the first model."""
    size_mb = os.path.getsize(path) / (1024**2)
    residues = set()
    model_started = False

    with open(path, "r") as f:
        for line in f:
            if line.startswith("MODEL") and not model_started:
                model_started = True
            elif line.startswith("ATOM"):
                res_id = line[21:22].strip() + line[22:26].strip()
                residues.add(res_id)
            elif line.startswith("ENDMDL") and model_started:
                break

    # If no MODEL tag found, use all ATOM lines
    if not model_started:
        with open(path, "r") as f:
            residues = {line[21:22].strip() + line[22:26].strip()
                        for line in f if line.startswith("ATOM")}

    return size_mb, len(residues)


# === MAIN WORKFLOW ===
for folder in folders:
    parent_folder = os.path.dirname(folder)
    project_name = os.path.basename(parent_folder)
    results_dir = os.path.join(parent_folder, "results")
    os.makedirs(results_dir, exist_ok=True)

    pdb_files = [f for f in os.listdir(folder) if f.endswith(".pdb")]
    total_pdbs = len(pdb_files)

    print("\n" + "=" * 65)
    print(f"📁 Processing folder: {project_name}")
    print("=" * 65)
    print(f"Path: {folder}")
    print(f"Total PDB files detected: {total_pdbs}\n")

    # === ANALYSIS ===
    data = []
    for i, f in enumerate(pdb_files, start=1):
        path = os.path.join(folder, f)
        print(f"  🔹 Analyzing {f} ({i}/{total_pdbs})...", end="\r")
        try:
            size_mb, length = analyze_pdb(path)
            data.append({"file": f, "size_MB": size_mb, "avg_length": length})
        except Exception as e:
            print(f"\n  ⚠️ Error analyzing {f}: {e}")

    df = pd.DataFrame(data)
    print(f"\n✅ Completed analysis of {len(df)} PDBs.\n")

    # === SAVE DATA ===
    tsv_path = os.path.join(results_dir, f"{project_name}_ensemble_analysis.tsv")
    df.to_csv(tsv_path, sep="\t", index=False)

    # === DISTRIBUTIONS ===
    bins_edges = seq_bins + [np.inf]
    df['seq_bin'] = pd.cut(df['avg_length'], bins=bins_edges, labels=seq_labels, right=True)
    seq_dist = df['seq_bin'].value_counts().reindex(seq_labels, fill_value=0)

    # === STATS ===
    summary = {
        "Total ensembles": len(df),
        "Min size (MB)": df["size_MB"].min(),
        "25th percentile size (MB)": df["size_MB"].quantile(0.25),
        "Median size (MB)": df["size_MB"].median(),
        "75th percentile size (MB)": df["size_MB"].quantile(0.75),
        "Max size (MB)": df["size_MB"].max(),
        "Mean size (MB)": df["size_MB"].mean(),
        "Min protein length": df['avg_length'].min(),
        "25th percentile length": df['avg_length'].quantile(0.25),
        "Median protein length": df['avg_length'].median(),
        "75th percentile length": df['avg_length'].quantile(0.75),
        "Max protein length": df['avg_length'].max(),
        "Mean protein length": df['avg_length'].mean(),
    }

    pd.DataFrame([summary]).to_csv(
        os.path.join(results_dir, f"{project_name}_ensemble_summary_stats.tsv"),
        sep="\t", index=False
    )

    # === REPORT ===
    report_path = os.path.join(results_dir, f"{project_name}_summary_report.txt")
    with open(report_path, "w") as report:
        report.write(f"=== Ensemble Analysis Report: {project_name} ===\n\n")
        report.write(f"Total ensembles analyzed: {summary['Total ensembles']}\n\n")

        report.write("File size statistics (MB):\n")
        for key in ["Min size (MB)", "25th percentile size (MB)", "Median size (MB)",
                    "75th percentile size (MB)", "Max size (MB)", "Mean size (MB)"]:
            report.write(f"  {key.replace(' size (MB)', '')}: {summary[key]:.2f}\n")

        report.write("\nProtein length statistics (residues):\n")
        for key in ["Min protein length", "25th percentile length", "Median protein length",
                    "75th percentile length", "Max protein length", "Mean protein length"]:
            report.write(f"  {key.replace(' protein length', '')}: {int(summary[key])}\n")

        report.write("\nSequence length distribution (50-residue bins):\n")
        for label, count in seq_dist.items():
            report.write(f"  {label}: {count}\n")

    # === PLOTS ===
    print("📊 Generating plots...")

    # Sequence length distribution (with clean bin labels)
    plt.figure(figsize=(10, 6))
    seq_dist.plot(kind='bar', color='steelblue')
    plt.xlabel("Sequence length range (residues)")
    plt.ylabel("Number of ensembles")
    plt.title(f"Sequence length distribution - {project_name}")
    plt.xticks(ticks=range(len(seq_labels)), labels=seq_labels, rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, f"{project_name}_plot_sequence_length_distribution.png"), dpi=200)
    plt.close()

    # File size histogram
    plt.figure(figsize=(10, 6))
    plt.hist(df['size_MB'], bins=30, color='coral')
    plt.xlabel("File size (MB)")
    plt.ylabel("Number of ensembles")
    plt.title(f"Ensemble file size distribution - {project_name}")
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, f"{project_name}_plot_file_size_distribution.png"), dpi=200)
    plt.close()

    # Length vs. size scatter plot
    plt.figure(figsize=(10, 6))
    plt.scatter(df['avg_length'], df['size_MB'], alpha=0.6, color='seagreen')
    plt.xlabel("Protein length (residues)")
    plt.ylabel("File size (MB)")
    plt.title(f"Protein length vs File size - {project_name}")
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, f"{project_name}_plot_seq_length_vs_size.png"), dpi=200)
    plt.close()

    print(f"🎯 All results saved under:\n  {results_dir}\n")
    print("-" * 65)
