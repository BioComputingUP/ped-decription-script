#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === Configuration ===
folders = [
    "/home/balbio/unipd/ped_deposition/AlphaFlex-IDPCG_cat2/completed_mediumF",
    "/home/balbio/unipd/ped_deposition/AlphaFlex-IDPCG_cat3/completed_hardF_idpcg",
    "/home/balbio/unipd/ped_deposition/AlphaFlex-IDPForge_cat3/completed_hardF_idpforge"
]

# Sequence length bins
seq_bins = list(range(0, 2551, 50))  # 0-50, 51-100, ..., 2501+
seq_labels = [f"{i+1}-{i+50}" for i in seq_bins[:-1]]
seq_labels.append(">2500")

def analyze_pdb(path):
    """Calcula tamaño del archivo y longitud de proteína (primer modelo)."""
    size_mb = os.path.getsize(path) / (1024**2)
    first_model_residues = set()
    model_detected = False
    with open(path, "r") as f:
        for line in f:
            if line.startswith("MODEL") and not model_detected:
                model_detected = True
            elif line.startswith("ATOM") and not first_model_residues is None:
                # Identificador único de residuo: cadena + residuo
                res_id = line[21:22].strip() + line[22:26].strip()
                first_model_residues.add(res_id)
            elif line.startswith("ENDMDL") and model_detected:
                break
    # Si no hay modelos, leer todos los ATOM
    if not model_detected:
        with open(path, "r") as f:
            first_model_residues = {line[21:22].strip() + line[22:26].strip() 
                                    for line in f if line.startswith("ATOM")}
    avg_len = len(first_model_residues)
    return size_mb, avg_len

# === Process each folder ===
for folder in folders:
    main_folder = os.path.dirname(folder)
    main_name = os.path.basename(main_folder)
    
    pdb_files = [f for f in os.listdir(folder) if f.endswith(".pdb")]
    print(f"\nProcessing folder: {folder} ({len(pdb_files)} PDB files)")
    
    results_dir = os.path.join(main_folder, "results")
    os.makedirs(results_dir, exist_ok=True)
    
    # === Analyze PDBs ===
    data = []
    for f in pdb_files:
        path = os.path.join(folder, f)
        try:
            size_mb, avg_len = analyze_pdb(path)
            data.append({"file": f, "size_MB": size_mb, "avg_length": avg_len})
        except Exception as e:
            print(f"Error analyzing {f}: {e}")
    
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(results_dir, f"{main_name}_ensemble_analysis.tsv"), sep="\t", index=False)
    
    # === Sequence length distribution ===
    bins_edges = seq_bins + [np.inf]
    df['seq_bin'] = pd.cut(df['avg_length'], bins=bins_edges, labels=seq_labels, right=True)
    seq_dist = df['seq_bin'].value_counts().reindex(seq_labels, fill_value=0)
    
    # === Summary statistics ===
    summary_stats = {
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
    
    summary_df = pd.DataFrame([summary_stats])
    summary_df.to_csv(os.path.join(results_dir, f"{main_name}_ensemble_summary_stats.tsv"), sep="\t", index=False)
    
    # === Text report simplified ===
    report_path = os.path.join(results_dir, f"{main_name}_summary_report.txt")
    with open(report_path, "w") as report:
        report.write(f"=== Ensemble Analysis Report: {main_name} ===\n\n")
        report.write(f"Total ensembles analyzed: {summary_stats['Total ensembles']}\n\n")
        
        report.write("File size statistics (MB):\n")
        report.write(f"  Min: {summary_stats['Min size (MB)']:.2f}\n")
        report.write(f"  25th percentile: {summary_stats['25th percentile size (MB)']:.2f}\n")
        report.write(f"  Median: {summary_stats['Median size (MB)']:.2f}\n")
        report.write(f"  75th percentile: {summary_stats['75th percentile size (MB)']:.2f}\n")
        report.write(f"  Max: {summary_stats['Max size (MB)']:.2f}\n")
        report.write(f"  Mean: {summary_stats['Mean size (MB)']:.2f}\n\n")
        
        report.write("Protein length statistics (residues):\n")
        report.write(f"  Min: {int(summary_stats['Min protein length'])}\n")
        report.write(f"  25th percentile: {int(summary_stats['25th percentile length'])}\n")
        report.write(f"  Median: {int(summary_stats['Median protein length'])}\n")
        report.write(f"  75th percentile: {int(summary_stats['75th percentile length'])}\n")
        report.write(f"  Max: {int(summary_stats['Max protein length'])}\n")
        report.write(f"  Mean: {int(summary_stats['Mean protein length'])}\n\n")
        
        report.write("Sequence length distribution (50 residue bins):\n")
        for label, count in seq_dist.items():
            report.write(f"  {label}: {count}\n")
    
    # === Plots ===
    plt.figure(figsize=(10,6))
    seq_dist.plot(kind='bar', color='skyblue')
    plt.xlabel("Sequence length (residues)")
    plt.ylabel("Number of ensembles")
    plt.title(f"Sequence length distribution - {main_name}")
    plt.xticks(rotation=90)
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, f"{main_name}_plot_sequence_length_distribution.png"), dpi=200)
    plt.close()
    
    plt.figure(figsize=(10,6))
    plt.hist(df['size_MB'], bins=30, color='salmon')
    plt.xlabel("File size (MB)")
    plt.ylabel("Number of ensembles")
    plt.title(f"Ensemble file size distribution - {main_name}")
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, f"{main_name}_plot_file_size_distribution.png"), dpi=200)
    plt.close()
    
    plt.figure(figsize=(10,6))
    plt.scatter(df['avg_length'], df['size_MB'], alpha=0.6, color='green')
    plt.xlabel("Average protein length (residues)")
    plt.ylabel("File size (MB)")
    plt.title(f"Sequence length vs File size - {main_name}")
    plt.tight_layout()
    plt.savefig(os.path.join(results_dir, f"{main_name}_plot_seq_length_vs_size.png"), dpi=200)
    plt.close()
    
    print(f"✅ Results saved in {results_dir}\n")