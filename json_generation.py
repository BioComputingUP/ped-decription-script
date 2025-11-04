import os
import json
from datetime import datetime
from description import create_description_json, get_uniprot_name, get_disprot_id
from construct import get_chain_sequences_and_last_residues, create_construct_json

# === CONFIGURATION ===
pdb_folders = [
    "/home/balbio/unipd/ped_deposition/pdb_sample",
]

base_desc_folder = "json_description"
base_construct_folder = "json_construct"
summary_path = "summary_json_generation.txt"

# === VARIABLES ===
summary_lines = []
summary_lines.append("=== JSON Generation Summary ===\n")
summary_lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
summary_lines.append(f"Output folders: {base_desc_folder} | {base_construct_folder}\n\n")

total_pdbs = 0
total_processed = 0
merged_entries = []  # merged IDs (skipped)

# === MAIN LOOP ===
for folder_idx, pdb_folder in enumerate(pdb_folders, start=1):
    if not os.path.exists(pdb_folder):
        warning = f"⚠️  Folder not found: {pdb_folder}\n"
        print(warning)
        summary_lines.append(warning)
        continue

    parts = pdb_folder.split("ped_deposition/")
    subpath = parts[1].strip("/") if len(parts) > 1 else os.path.basename(pdb_folder)
    subfolder_name = subpath.replace("/", "_")

    desc_folder = os.path.join(base_desc_folder, subfolder_name)
    construct_folder = os.path.join(base_construct_folder, subfolder_name)
    os.makedirs(desc_folder, exist_ok=True)
    os.makedirs(construct_folder, exist_ok=True)

    print(f"\n📂 [{folder_idx}/{len(pdb_folders)}] Processing folder: {pdb_folder}")
    print(f"   → JSON files will be saved under '{subfolder_name}'")

    pdb_files = [f for f in os.listdir(pdb_folder) if f.endswith(".pdb")]
    n_found = len(pdb_files)
    n_success = 0
    failed_files = []

    summary_lines.append(f"[{subfolder_name}]\n")
    summary_lines.append(f"  Path: {pdb_folder}\n")
    summary_lines.append(f"  PDBs found: {n_found}\n")

    total_pdbs += n_found

    for idx, pdb_file in enumerate(pdb_files, start=1):
        pdb_base = os.path.splitext(pdb_file)[0]
        original_id = pdb_base.split("_")[0]

        print(f"\n  🧩 [{idx}/{n_found}] {pdb_file}")
        print(f"      UniProt ID detected: {original_id}")

        try:
            # Get name and final ID (handles merges and deletions)
            protein_name, final_id = get_uniprot_name(original_id)

            # If merged → SKIP
            if final_id != original_id:
                msg = f"      🔁❌ Merged ID: {original_id} → {final_id} (JSON not generated)"
                print(msg)
                summary_lines.append(f"    {msg}\n")
                merged_entries.append((original_id, final_id))
                continue

            # Identify workflow
            if "_idpcg_" in pdb_file.lower():
                title_prefix = "AF-IDPCG"
                workflow = "IDPConformerGenerator"
            elif "forge_" in pdb_file.lower():
                title_prefix = "AF-IDPForge"
                workflow = "IDPForge"
            else:
                title_prefix = "AF-Ensemble"
                workflow = "Unknown"

            # === Case 1: Inactive or deleted UniProt ID ===
            if protein_name is None:
                msg = f"      ⚠️  ID {original_id} inactive or not found."
                print(msg)
                summary_lines.append(f"    {msg}\n")

                data_desc = create_description_json(original_id)
                data_desc["title"] = f"{title_prefix} Ensemble Prediction of {original_id}"
                data_desc["structural_ensembles_calculation"] = (
                    f"AlphaFlex with {workflow} workflow based on the AlphaFold 2 prediction of {original_id}"
                )

                pdb_path = os.path.join(pdb_folder, pdb_file)
                data_construct = [{
                    "chain_name": chain,
                    "fragments": [{
                        "description": f"{original_id}",
                        "source_sequence": info.get("sequence", ""),
                        "definition_type": "By Sequence"
                    }]
                } for chain, info in get_chain_sequences_and_last_residues(pdb_path).items()]

                desc_path = os.path.join(desc_folder, f"{pdb_base}.json")
                construct_path = os.path.join(construct_folder, f"{pdb_base}_const.json")

                with open(desc_path, "w", encoding="utf-8") as f:
                    json.dump(data_desc, f, indent=4, ensure_ascii=False)
                with open(construct_path, "w", encoding="utf-8") as f:
                    json.dump(data_construct, f, indent=4, ensure_ascii=False)

                print(f"      ✅ JSONs generated: {os.path.basename(desc_path)}, {os.path.basename(construct_path)}")
                n_success += 1
                total_processed += 1
                continue

            # === Case 2: Valid UniProt ID ===
            disprot_id = get_disprot_id(original_id)
            print(f"      Protein: {protein_name}")
            if disprot_id:
                print(f"      DisProt ID: {disprot_id}")

            # Normal JSONs
            data_desc = create_description_json(original_id)
            data_desc["title"] = f"{title_prefix} Ensemble Prediction of {protein_name}"
            data_desc["structural_ensembles_calculation"] = (
                f"AlphaFlex with {workflow} workflow based on the AlphaFold 2 prediction of {original_id}"
            )
            if disprot_id:
                data_desc["entry_cross_reference"] = [{"db": "disprot", "id": disprot_id}]

            pdb_path = os.path.join(pdb_folder, pdb_file)
            chain_info = get_chain_sequences_and_last_residues(pdb_path)
            data_construct = create_construct_json(chain_info, original_id, protein_name)

            desc_path = os.path.join(desc_folder, f"{pdb_base}.json")
            construct_path = os.path.join(construct_folder, f"{pdb_base}_const.json")

            with open(desc_path, "w", encoding="utf-8") as f:
                json.dump(data_desc, f, indent=4, ensure_ascii=False)
            with open(construct_path, "w", encoding="utf-8") as f:
                json.dump(data_construct, f, indent=4, ensure_ascii=False)

            print(f"      ✅ Full JSONs generated: {os.path.basename(desc_path)}, {os.path.basename(construct_path)}")
            summary_lines.append(f"    ✅ {pdb_file} processed successfully.\n")

            n_success += 1
            total_processed += 1

        except Exception as e:
            error_msg = f"      ❌ Error processing {pdb_file}: {e}"
            print(error_msg)
            summary_lines.append(f"    {error_msg}\n")
            failed_files.append(f"{pdb_file} → {e}")

    summary_lines.append(f"  Successfully processed: {n_success}/{n_found}\n")
    if failed_files:
        summary_lines.append("  Errors:\n")
        for f in failed_files:
            summary_lines.append(f"    - {f}\n")
    summary_lines.append("\n")

# === FINAL SUMMARY ===
summary_lines.append("=== Overall Summary ===\n")
summary_lines.append(f"Total folders processed: {len(pdb_folders)}\n")
summary_lines.append(f"Total PDBs found: {total_pdbs}\n")
summary_lines.append(f"Total JSONs successfully generated: {total_processed}\n")
summary_lines.append(f"Total merged entries skipped: {len(merged_entries)}\n")
summary_lines.append(f"Total with errors: {total_pdbs - total_processed - len(merged_entries)}\n")

# 🧩 Merged entries section (table)
merged_pdb_files = []
if merged_entries:
    summary_lines.append("\n=== Skipped merged UniProt entries ===\n")
    summary_lines.append("The following input PDBs were skipped because their UniProt IDs have been merged into new entries:\n\n")
    summary_lines.append("PDB File Name".ljust(40) + " | New UniProt ID\n")
    summary_lines.append("-" * 40 + " | " + "-" * 14 + "\n")

    for orig, new in merged_entries:
        pdb_file_name = f"{orig}_idpcg_n100.pdb"
        summary_lines.append(pdb_file_name.ljust(40) + f" | {new}\n")
        merged_pdb_files.append(pdb_file_name)

# Guardar resumen general
with open(summary_path, "w", encoding="utf-8") as f:
    f.writelines(summary_lines)

# Guardar lista de PDBs mergeados (si hay)
if merged_pdb_files:
    merged_list_path = "merged_pdb_list.txt"
    with open(merged_list_path, "w", encoding="utf-8") as f:
        for pdb in merged_pdb_files:
            f.write(f"{pdb}\n")
    print(f"\n📁 Merged PDB file list saved in: {merged_list_path}")

print("\n📜 Summary saved in:", summary_path)
print("🎯 JSONs generated in:", base_desc_folder, "and", base_construct_folder)

if merged_entries:
    print("\n🔁 Skipped merged UniProt entries:")
    print("PDB File Name".ljust(40) + " | New UniProt ID")
    print("-" * 40 + " | " + "-" * 14)
    for orig, new in merged_entries:
        pdb_file_name = f"{orig}_idpcg_n100.pdb"
        print(pdb_file_name.ljust(40) + f" | {new}")
