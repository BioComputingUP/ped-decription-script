#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import shutil
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# === CONFIGURACIÓN ===
# Lista de carpetas principales ("carpeta 1") que contienen:
#   - subcarpeta "completed_*" con los PDBs
#   - subcarpeta "results" con el TSV *_ensemble_analysis.tsv
parent_folders = [
    "/home/balbio/unipd/ped_deposition/AlphaFlex-IDPCG_cat2",
#   "/home/balbio/unipd/ped_deposition/AlphaFlex-IDPCG_cat3",
#   "/home/balbio/unipd/ped_deposition/AlphaFlex-IDPForge_cat3"
]

# === BINS DE LONGITUD DE SECUENCIA (50 aa) ===
seq_bins = list(range(0, 2551, 50))  # 0-50, 51-100, ..., 2501+
seq_labels = [f"{i+1}-{i+50}" for i in seq_bins[:-1]]
seq_labels.append(">2500")
bins_edges = seq_bins + [np.inf]

# === FUNCIÓN PARA COPIAR LOS PDBs DE UN BATCH ===
def copy_batch_files(batch_df, batch_dir, log_path):
    os.makedirs(batch_dir, exist_ok=True)
    with open(log_path, "a") as log:
        for _, row in batch_df.iterrows():
            src = os.path.join(row['source_pdb_folder'], row['file'])
            dst = os.path.join(batch_dir, row['file'])
            try:
                shutil.copy2(src, dst)
            except Exception as e:
                log.write(f"Error copiando {src} -> {dst}: {e}\n")

# === PROCESO PARA CADA CARPETA PADRE ===
for parent in parent_folders:
    print(f"\n=== Procesando {parent} ===")

    results_dir = os.path.join(parent, "results")
    os.makedirs(results_dir, exist_ok=True)

    # buscar subcarpeta "completed_*"
    completed_subdirs = [os.path.join(parent, d) for d in os.listdir(parent) if d.startswith("completed_")]
    if not completed_subdirs:
        print(f"⚠️ No se encontró carpeta completed_* en {parent}, se omite.")
        continue
    completed_folder = completed_subdirs[0]

    # buscar TSV
    main_name = os.path.basename(parent)
    tsv_path = os.path.join(results_dir, f"{main_name}_ensemble_analysis.tsv")
    if not os.path.exists(tsv_path):
        print(f"⚠️ TSV no encontrado en {tsv_path}, se omite.")
        continue

    print(f"  TSV: {tsv_path}")
    print(f"  PDBs: {completed_folder}")

    # leer TSV
    df = pd.read_csv(tsv_path, sep="\t")
    df["source_pdb_folder"] = completed_folder

    # asignar bins
    df['seq_bin'] = pd.cut(df['avg_length'], bins=bins_edges, labels=seq_labels, right=True)

    # carpetas de salida
    output_base_dir = os.path.join(results_dir, "batches_by_length")
    os.makedirs(output_base_dir, exist_ok=True)
    log_path = os.path.join(output_base_dir, "copy_log.txt")

    # crear batches
    batch_records, summary_records = [], []

    for bin_label in seq_labels:
        df_bin = df[df['seq_bin'] == bin_label]
        if df_bin.empty:
            continue

        safe_label = bin_label.replace(">", "gt").replace(" ", "")
        batch_dir = os.path.join(output_base_dir, f"batch_{safe_label}")
        copy_batch_files(df_bin, batch_dir, log_path)

        # asignaciones
        for _, row in df_bin.iterrows():
            batch_records.append({
                "seq_bin": bin_label,
                "file": row["file"],
                "source_pdb_folder": row["source_pdb_folder"]
            })

        total_size = df_bin['size_MB'].sum()
        avg_length = df_bin['avg_length'].mean()
        summary_records.append({
            "seq_bin": bin_label,
            "n_files": int(len(df_bin)),
            "total_size_MB": float(total_size),
            "avg_length": float(avg_length),
            "batch_folder": os.path.relpath(batch_dir, start=parent)
        })

    # guardar TSVs y reporte
    assignment_path = os.path.join(output_base_dir, "batch_assignment_by_length.tsv")
    summary_path = os.path.join(output_base_dir, "batch_summary_by_length.tsv")
    report_path = os.path.join(output_base_dir, "batch_report_by_length.txt")

    pd.DataFrame(batch_records).to_csv(assignment_path, sep="\t", index=False)
    pd.DataFrame(summary_records).to_csv(summary_path, sep="\t", index=False)

    with open(report_path, "w") as rpt:
        rpt.write(f"Batches por longitud de secuencia (50 aa)\n")
        rpt.write(f"Output base: {output_base_dir}\n\n")
        rpt.write("Resumen por bin:\n")
        for s in summary_records:
            rpt.write(f"  Bin {s['seq_bin']}: {s['n_files']} archivos, total {s['total_size_MB']:.2f} MB, avg length {s['avg_length']:.1f} → {s['batch_folder']}\n")

    # === GRÁFICOS ===
    if summary_records:
        df_summary = pd.DataFrame(summary_records)

        # total size
        plt.figure(figsize=(12,5))
        plt.bar(df_summary["seq_bin"], df_summary["total_size_MB"])
        plt.xticks(rotation=90)
        plt.xlabel("Rango de longitud (residuos)")
        plt.ylabel("Tamaño total (MB)")
        plt.title("Tamaño total por batch de longitud")
        plt.tight_layout()
        plt.savefig(os.path.join(output_base_dir, "batch_sizes_by_length.png"), dpi=200)
        plt.close()

        # número de proteínas
        plt.figure(figsize=(12,5))
        plt.bar(df_summary["seq_bin"], df_summary["n_files"])
        plt.xticks(rotation=90)
        plt.xlabel("Rango de longitud (residuos)")
        plt.ylabel("Número de proteínas")
        plt.title("Número de proteínas por batch de longitud")
        plt.tight_layout()
        plt.savefig(os.path.join(output_base_dir, "batch_counts_by_length.png"), dpi=200)
        plt.close()

    print(f"  ✅ Completado: resultados guardados en {output_base_dir}")

print("\n🎉 Todos los conjuntos procesados correctamente.")
