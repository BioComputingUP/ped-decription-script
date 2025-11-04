# construct.py
import os
import json
from Bio.PDB import PDBParser, PPBuilder

def get_chain_sequences_and_last_residues(pdb_path):
    """
    Devuelve diccionario {chain_id: {"sequence": str, "end": int}} 
    usando la secuencia y último residuo de cada cadena en el PDB.
    """
    parser = PDBParser(QUIET=True)
    structure = parser.get_structure("struct", pdb_path)
    ppb = PPBuilder()
    chain_info = {}

    # Tomamos solo el primer modelo
    model = next(structure.get_models())
    for chain in model:
        polypeptides = ppb.build_peptides(chain)
        seq = "".join([str(pp.get_sequence()) for pp in polypeptides])
        residues = [res for res in chain if res.id[0] == " "]
        if residues:
            last_resnum = residues[-1].id[1]
            chain_info[chain.id] = {"sequence": seq, "end": last_resnum}
    return chain_info

def create_construct_json(chain_info, uniprot_id, protein_name):
    """
    Devuelve lista de construct_info en formato JSON-ready
    """
    construct_info = []
    for chain, info in chain_info.items():
        fragment = {
            "description": protein_name,
            "source_sequence": info["sequence"],
            "start_position": 1,
            "end_position": info["end"],
            "uniprot_acc": uniprot_id,
            "definition_type": "Uniprot ACC"
        }
        construct_info.append({"chain_name": chain, "fragments": [fragment]})
    return construct_info
