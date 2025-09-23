# description.py
import requests

def get_uniprot_name(uniprot_id):
    """
    Returns protein name from UniProt.
    """
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        try:
            return data['proteinDescription']['recommendedName']['fullName']['value']
        except KeyError:
            return uniprot_id
    else:
        print(f"Error UniProt {uniprot_id}")
        return uniprot_id

def get_disprot_id(uniprot_id):
    """
    Returns DisProt ID based on UniProt ID.
    """
    url = f"https://disprot.org/api/{uniprot_id}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            return data.get("disprot_id")
        else:
            return None
    except:
        return None

def create_description_json(uniprot_id):
    """
    Generates the JSON dictionary template for a PDB file.
    """
    data = {
        "title": [],
        "authors": [{"name": "Nombre Apellido", "corresponding_author": False}],
        "publication_status": "Publication status",
        "publication_source": "Publication source",
        "publication_identifier": "Number of publication identifier",
        "publication_html": "publication html",
        "entry_cross_reference": [],
        "experimental_cross_reference": [],
        "experimental_procedure": [],
        "structural_ensembles_calculation": "Structural ensemble calculation",
        "ontology_terms": [{}],
    }
    return data
