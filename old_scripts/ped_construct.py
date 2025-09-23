import os
import json
import requests
from Bio.PDB import PDBParser, PPBuilder

pdb_folder = "pdb_sample"
output_folder = "construct_json"
os.makedirs(output_folder, exist_ok=True)

def get_uniprot_name(uniprot_id):
    """
    Consulta UniProt para obtener el nombre de la proteína a partir del UniProt ID.
    """
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        try:
            return data["proteinDescription"]["recommendedName"]["fullName"]["value"]
        except KeyError:
            return uniprot_id  # fallback
    else:
        print(f"⚠️ Error consultando UniProt para {uniprot_id}")
        return uniprot_id

def get_chain_sequences_and_last_residues(pdb_path):
    """
    Devuelve diccionario con {chain_id: {"sequence": str, "end": int}}
    usando la secuencia y último residuo de cada cadena en el PRIMER modelo del PDB
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("struct", pdb_path)

    ppb = PPBuilder()
    chain_info = {}

    # Solo el primer modelo
    model = next(structure.get_models())
    for chain in model:
        polypeptides = ppb.build_peptides(chain)
        seq = "".join([str(pp.get_sequence()) for pp in polypeptides])

        residues = [res for res in chain if res.id[0] == " "]  # excluir heteroátomos
        if residues:
            last_resnum = residues[-1].id[1]
            chain_info[chain.id] = {"sequence": seq, "end": last_resnum}
    return chain_info

def make_construct_info(chain_info, uniprot_id, protein_name):
    """
    Devuelve lista con construct_info en formato JSON-ready
    """
    construct_info = []
    for chain, info in chain_info.items():
        fragment = {
            "description": protein_name,   # ahora el nombre de la proteína de UniProt
            "source_sequence": info["sequence"],
            "start_position": 1,
            "end_position": info["end"],
            "uniprot_acc": uniprot_id,
            "definition_type": "Uniprot ACC"
        }
        construct_info.append({"chain_name": chain, "fragments": [fragment]})
    return construct_info


for pdb_file in os.listdir(pdb_folder):
    if pdb_file.endswith(".pdb"):
        pdb_base = os.path.splitext(pdb_file)[0]
        uniprot_id = pdb_base.split("_")[0]
        pdb_path = os.path.join(pdb_folder, pdb_file)

        print(f"\nProcesando {pdb_file} → UniProt {uniprot_id}")

        protein_name = get_uniprot_name(uniprot_id)  # consulta a UniProt
        chain_info = get_chain_sequences_and_last_residues(pdb_path)
        construct_info = make_construct_info(chain_info, uniprot_id, protein_name)

        output_path = os.path.join(output_folder, f"{pdb_base}_construct.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(construct_info, f, indent=4, ensure_ascii=False)

        print(f"✅ JSON generado: {output_path}")
