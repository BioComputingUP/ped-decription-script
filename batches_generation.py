#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ============================================================
# CONFIGURATION
# ============================================================

parent_folders = [
#    "/home/balbio/unipd/ped_deposition/AlphaFlex-IDPCG_cat2",
    "/home/balbio/unipd/ped_deposition/AlphaFlex-IDPCG_cat3",
#   "/home/balbio/unipd/ped_deposition/AlphaFlex-IDPForge_cat3"
]

MAX_PDBS_PER_BATCH = 90
BIN_STEP = 50

# Sequence-length bins (50 aa increments)
seq_bins = list(range(0, 2551, BIN_STEP))
seq_labels = [f"{i+1}-{i+BIN_STEP}" for i in seq_bins[:-1]]
seq_labels.append(">2500")
bins_edges = seq_bins + [np.inf]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def print_header(title):
    print("\n" + "=" * 70)
    print(f" {title}")
    print("=" * 70)

def print_subheader(title):
    print(f"\n--- {title} ---")

def move_batch_files(df_part, batch_dir, log_path):
    """Move PDBs of a sub-batch with progress reporting."""
    os.makedirs(batch_dir, exist_ok=True)
    total = len(df_part)

    with open(log_path, "a") as log:
        for idx, (_, row) in enumerate(df_part.iterrows(), start=1):
            src = os.path.join(row["source_pdb_folder"], row["file"])
            dst = os.path.join(batch_dir, row["file"])
            try:
                shutil.move(src, dst)
            except Exception as e:
                log.write(f"[ERROR] Moving {src} -> {dst}: {e}\n")
            # Inline progress
            print(f"    Moving file {idx}/{total}", end="\r")
    print()  # newline after move loop


# ============================================================
# MAIN PROCESSING LOOP
# ============================================================

for parent in parent_folders:
    print_header(f"Processing parent folder: {parent}")

    results_dir = os.path.join(parent, "results")
    os.makedirs(results_dir, exist_ok=True)

    # Detect PDB folder
    completed_dirs = [os.path.join(parent, d) for d in os.listdir(parent) if d.startswith("completed_")]
    if not completed_dirs:
        print(f"⚠️  No completed_* folder found. Skipping {parent}.")
        continue
    completed_folder = completed_dirs[0]

    # Find TSV
    main_name = os.path.basename(parent)
    tsv_path = os.path.join(results_dir, f"{main_name}_ensemble_analysis.tsv")
    if not os.path.exists(tsv_path):
        print(f"⚠️  Missing TSV file: {tsv_path}. Skipping.")
        continue

    print(f"📄  Ensemble TSV: {tsv_path}")
    print(f"📂  PDB source:  {completed_folder}")

    # Load TSV
    df = pd.read_csv(tsv_path, sep="\t")
    df["source_pdb_folder"] = completed_folder
    df["seq_bin"] = pd.cut(df["avg_length"], bins=bins_edges, labels=seq_labels, right=True)

    output_base = os.path.join(results_dir, "batches_by_length")
    os.makedirs(output_base, exist_ok=True)
    log_path = os.path.join(output_base, "move_log.txt")

    batch_records = []
    summary_records = []

    # ============================================================
    # PROCESS EACH SEQUENCE BIN
    # ============================================================
    for bin_label in seq_labels:
        df_bin = df[df["seq_bin"] == bin_label]
        if df_bin.empty:
            continue

        print_subheader(f"Sequence bin: {bin_label}")
        print(f"  → Total PDBs in bin: {len(df_bin)}")

        n_chunks = int(np.ceil(len(df_bin) / MAX_PDBS_PER_BATCH))
        df_chunks = [df_bin.iloc[i*MAX_PDBS_PER_BATCH:(i+1)*MAX_PDBS_PER_BATCH] for i in range(n_chunks)]

        for i, df_part in enumerate(df_chunks, start=1):
            safe_label = bin_label.replace(">", "gt").replace(" ", "")
            part_name = f"batch_{safe_label}_part{i:02}" if n_chunks > 1 else f"batch_{safe_label}"
            batch_dir = os.path.join(output_base, part_name)

            print(f"  🧩 Creating sub-batch {i}/{n_chunks}: {part_name}")
            print(f"     Files in this sub-batch: {len(df_part)}")
            move_batch_files(df_part, batch_dir, log_path)

            batch_folder_rel = os.path.relpath(batch_dir, start=parent)

            summary_records.append({
                "seq_bin": bin_label,
                "sub_batch": i,
                "n_files": len(df_part),
                "total_size_MB": df_part["size_MB"].sum(),
                "avg_length": df_part["avg_length"].mean(),
                "batch_folder": batch_folder_rel
            })

            for _, row in df_part.iterrows():
                batch_records.append({
                    "seq_bin": bin_label,
                    "sub_batch": i,
                    "file": row["file"],
                    "source_pdb_folder": row["source_pdb_folder"]
                })

    # ============================================================
    # SAVE RESULTS
    # ============================================================
    assignment_tsv = os.path.join(output_base, "batch_assignment_by_length.tsv")
    summary_tsv = os.path.join(output_base, "batch_summary_by_length.tsv")
    report_txt = os.path.join(output_base, "batch_report_by_length.txt")

    pd.DataFrame(batch_records).to_csv(assignment_tsv, sep="\t", index=False)
    pd.DataFrame(summary_records).to_csv(summary_tsv, sep="\t", index=False)

    with open(report_txt, "w") as rpt:
        rpt.write(f"Batch generation report (bins: 50 aa, max {MAX_PDBS_PER_BATCH} per batch)\n")
        rpt.write(f"Parent: {parent}\n\n")
        for s in summary_records:
            rpt.write(f"  Bin {s['seq_bin']} - part {s['sub_batch']:02}: {s['n_files']} files | "
                      f"{s['total_size_MB']:.2f} MB | Avg len {s['avg_length']:.1f} aa | "
                      f"{s['batch_folder']}\n")

    # ============================================================
    # PLOTS
    # ============================================================
    if summary_records:
        df_summary = pd.DataFrame(summary_records)

        # ✅ Clean X labels
        df_summary["x_label"] = df_summary.apply(
            lambda x: f"batch_{x['seq_bin']}_{x['sub_batch']}" if len(df_summary[df_summary['seq_bin'] == x['seq_bin']]) > 1 
                      else f"batch_{x['seq_bin']}", axis=1
        )

        plt.figure(figsize=(12, 5))
        plt.bar(df_summary["x_label"], df_summary["total_size_MB"])
        plt.xticks(rotation=90, fontsize=7)
        plt.ylabel("Total size (MB)")
        plt.title("Total batch size per sequence-length bin")
        plt.tight_layout()
        plt.savefig(os.path.join(output_base, "batch_sizes_by_length.png"), dpi=200)
        plt.close()

        plt.figure(figsize=(12, 5))
        plt.bar(df_summary["x_label"], df_summary["n_files"])
        plt.xticks(rotation=90, fontsize=7)
        plt.ylabel("# of PDBs")
        plt.title("Number of PDBs per batch")
        plt.tight_layout()
        plt.savefig(os.path.join(output_base, "batch_counts_by_length.png"), dpi=200)
        plt.close()

    print(f"\n✅ Done! Output saved in: {output_base}")

print("\n🎉 All parent folders processed successfully.")