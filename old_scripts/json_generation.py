import os
import json
from datetime import datetime
from description import create_description_json, get_uniprot_name, get_disprot_id
from construct import get_chain_sequences_and_last_residues, create_construct_json

# Lista de carpetas con PDBs de entrada
pdb_folders = [
    "/home/balbio/unipd/ped_deposition/idpforgeeee",
    "/home/balbio/unipd/ped_deposition/pdb_sample",
#   "/home/balbio/unipd/ped_deposition/AlphaFlex-IDPCG_cat3/completed_hardF_idpcg",
#   "/home/balbio/unipd/ped_deposition/AlphaFlex-IDPForge_cat3/completed_hardF_idpforge"
]

# Carpetas base de salida
base_desc_folder = "json_description"
base_construct_folder = "json_construct"
summary_path = "summary_json_generation.txt"

summary_lines = []
summary_lines.append("=== JSON Generation Summary ===\n")
summary_lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
summary_lines.append(f"Base folders: {base_desc_folder} | {base_construct_folder}\n\n")

total_pdbs = 0
total_processed = 0

for pdb_folder in pdb_folders:
    if not os.path.exists(pdb_folder):
        warning = f"⚠️  Carpeta no encontrada: {pdb_folder}\n"
        print(warning)
        summary_lines.append(warning)
        continue

    # Obtener la parte del path después de "ped_deposition/"
    parts = pdb_folder.split("ped_deposition/")
    if len(parts) > 1:
        subpath = parts[1].strip("/")
    else:
        subpath = os.path.basename(pdb_folder)
    subfolder_name = subpath.replace("/", "_")

    # Crear subcarpetas específicas
    desc_folder = os.path.join(base_desc_folder, subfolder_name)
    construct_folder = os.path.join(base_construct_folder, subfolder_name)
    os.makedirs(desc_folder, exist_ok=True)
    os.makedirs(construct_folder, exist_ok=True)

    print(f"\n📂 Procesando carpeta: {pdb_folder}")
    print(f"   → JSONs se guardarán en '{subfolder_name}'")

    pdb_files = [f for f in os.listdir(pdb_folder) if f.endswith(".pdb")]
    n_found = len(pdb_files)
    n_success = 0
    failed_files = []

    summary_lines.append(f"[{subfolder_name}]\n")
    summary_lines.append(f"  Ruta: {pdb_folder}\n")
    summary_lines.append(f"  PDBs encontrados: {n_found}\n")

    total_pdbs += n_found

    for pdb_file in pdb_files:
        try:
            pdb_base = os.path.splitext(pdb_file)[0]
            uniprot_id = pdb_base.split("_")[0]

            # Determinar tipo (IDPCG, Forge, etc.)
            if "_idpcg_" in pdb_file.lower():
                title_prefix = "AF-IDPCG"
                workflow = "IDPConformerGenerator"
            elif "forge_" in pdb_file.lower():
                title_prefix = "AF-IDPForge"
                workflow = "IDPForge"
            else:
                title_prefix = "AF-Ensemble"
                workflow = "Unknown"

            protein_name = get_uniprot_name(uniprot_id)
            disprot_id = get_disprot_id(uniprot_id)

            print(f"  🧩 {pdb_file} → {uniprot_id} ({title_prefix})")

            # JSON description
            data_desc = create_description_json(uniprot_id)
            data_desc["title"] = f"{title_prefix} Ensemble Prediction of {protein_name}"
            data_desc["structural_ensembles_calculation"] = (
                f"AlphaFlex with {workflow} workflow based on the AlphaFold 2 prediction of {uniprot_id}"
            )
            if disprot_id:
                data_desc["entry_cross_reference"] = [{"db": "disprot", "id": disprot_id}]

            # JSON construct
            pdb_path = os.path.join(pdb_folder, pdb_file)
            chain_info = get_chain_sequences_and_last_residues(pdb_path)
            data_construct = create_construct_json(chain_info, uniprot_id, protein_name)

            # Guardar JSONs
            desc_path = os.path.join(desc_folder, f"{pdb_base}.json")
            construct_path = os.path.join(construct_folder, f"{pdb_base}_const.json")

            with open(desc_path, "w", encoding="utf-8") as f:
                json.dump(data_desc, f, indent=4, ensure_ascii=False)
            with open(construct_path, "w", encoding="utf-8") as f:
                json.dump(data_construct, f, indent=4, ensure_ascii=False)

            print(f"     ✅ {os.path.basename(desc_path)} y {os.path.basename(construct_path)} generados.")
            n_success += 1
            total_processed += 1

        except Exception as e:
            error_msg = f"     ❌ Error procesando {pdb_file}: {e}"
            print(error_msg)
            failed_files.append(f"{pdb_file} → {e}")

    summary_lines.append(f"  Procesados correctamente: {n_success}\n")
    if failed_files:
        summary_lines.append("  Errores:\n")
        for f in failed_files:
            summary_lines.append(f"    - {f}\n")
    summary_lines.append("\n")

summary_lines.append("=== Resumen General ===\n")
summary_lines.append(f"Total carpetas procesadas: {len(pdb_folders)}\n")
summary_lines.append(f"Total PDBs encontrados: {total_pdbs}\n")
summary_lines.append(f"Total JSONs generados correctamente: {total_processed}\n")
summary_lines.append(f"Total con errores: {total_pdbs - total_processed}\n")

with open(summary_path, "w", encoding="utf-8") as f:
    f.writelines(summary_lines)

print(f"\n📜 Resumen guardado en '{summary_path}'")
print("\n🎯 JSONs generados en carpetas:", base_desc_folder, "y", base_construct_folder)
