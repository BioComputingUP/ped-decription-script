import os
import json
import requests

# Folder with PDBs
pdb_folder = "pdb_sample"
# Output folder of JSON files
output_folder = "json_output"
os.makedirs(output_folder, exist_ok=True)

# Base for JSON file


def crear_json_base():
    return {
        "title": [],
        "authors": [
            {"name": "Probando Probando", "corresponding_author": False}
        ],
        "publication_status": "Publication status",
        "publication_source": "Publication source",
        "publication_identifier": "Number of publication identifier",
        "publication_html": "publication html",
        "entry_cross_reference": [],  # Disprot reference
        "experimental_procedure": "Experimental procedure",
        "structural_ensembles_calculation": "Structural ensemble calculation",
        "ontology_terms": "ontology terms",
    }


def get_uniprot_name(uniprot_id):
    """
    Consults UniProt to obtain the name of the protein from Uniprot ID
    """
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"  # URL from Uniprot API
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        try:
            # Extract the protein name
            return data['proteinDescription']['recommendedName']['fullName']['value']
        except KeyError:
            return uniprot_id
    else:
        print(f"Error consulting Uniprot for {uniprot_id}")  # mensaje de error
        return uniprot_id


def get_disprot_id(uniprot_id):
    """
    Consults Disprot to obtain the ID of the protein from Uniprot ID
    """
    url = f"https://disprot.org/api/{uniprot_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get("disprot_id")
        else:
            print(
                f"Error consulting DisProt for {uniprot_id}: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error consulting DisProt for {uniprot_id}: {e}")
        return None


for pdb_file in os.listdir(pdb_folder):
    if pdb_file.endswith(".pdb"):
        pdb_base = os.path.splitext(pdb_file)[0]  # takes out .pdb
        uniprot_id = pdb_base.split("_")[0]  # Uniprot ID

        # Protein name from Uniprot
        protein_name = get_uniprot_name(uniprot_id)

        # DisProt ID desde DisProt
        disprot_id = get_disprot_id(uniprot_id)

        print(
            f"Processing PDB: {uniprot_id} - {protein_name} - (DisProt ID: {disprot_id})")

        # Creation of JSON with base function
        data = crear_json_base()
        data["title"] = f"Structural ensemble of {protein_name}"
        if disprot_id:
            data["entry_cross_reference"] = ({
                "database": "disprot",
                "identifier": disprot_id
            })
        else:
            del data["entry_cross_reference"]

        # Save JSON
        output_path = os.path.join(output_folder, f"{pdb_base}.json")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

print("✅ Archivos JSON generated in:", output_folder)
