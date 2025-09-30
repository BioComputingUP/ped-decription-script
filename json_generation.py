# json_generation.py
import os
import json
from description import create_description_json, get_uniprot_name, get_disprot_id
from construct import get_chain_sequences_and_last_residues, create_construct_json

# folder with PDBs
pdb_folder = "pdb_files"

# separated out folders 
desc_folder = "json_description"
construct_folder = "json_construct"
os.makedirs(desc_folder, exist_ok=True)
os.makedirs(construct_folder, exist_ok=True)

for pdb_file in os.listdir(pdb_folder):
    if pdb_file.endswith(".pdb"):
        pdb_base = os.path.splitext(pdb_file)[0]  # name without extension
        uniprot_id = pdb_base.split("_")[0]  # uniprot id from filename

        # Obtains the protein name from UniProt
        protein_name = get_uniprot_name(uniprot_id)

        # Obtains DisProt ID
        disprot_id = get_disprot_id(uniprot_id)

        print(f"\nProcesando PDB: {pdb_file} → UniProt {uniprot_id} - {protein_name} - (DisProt ID: {disprot_id})")

        # Generates JSON description file
        data_desc = create_description_json(uniprot_id)
        data_desc["title"] = f"Structural ensemble of {protein_name}"
        if disprot_id:
            data_desc["entry_cross_reference"] = [{
                "database": "disprot",
                "identifier": disprot_id
            }]

        # Generates JSON construct file
        pdb_path = os.path.join(pdb_folder, pdb_file)
        chain_info = get_chain_sequences_and_last_residues(pdb_path)
        data_construct = create_construct_json(chain_info, uniprot_id, protein_name)

        # Save both JSON files in separate folders
        desc_path = os.path.join(desc_folder, f"{pdb_base}.json")
        with open(desc_path, "w", encoding="utf-8") as f:
            json.dump(data_desc, f, indent=4, ensure_ascii=False)

        construct_path = os.path.join(construct_folder, f"{pdb_base}_const.json")
        with open(construct_path, "w", encoding="utf-8") as f:
            json.dump(data_construct, f, indent=4, ensure_ascii=False)

        print(f"✅ JSON generated: {os.path.basename(desc_path)} and {os.path.basename(construct_path)}")

print("\n✅ All JSON generated in folders:", desc_folder, "and", construct_folder)
