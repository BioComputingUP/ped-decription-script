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
        "authors": [
            {
                "name": "Zi Hao Liu", 
                "corresponding_author": False
            },
            {
                "name": "Oufan Zhang", 
                "corresponding_author": False
            },
            {
                "name": "Stefano De Castro", 
                "corresponding_author": False
            },
            {
                "name": "Kunyang Sun", 
                "corresponding_author": False
            },
            {
                "name": "Teresa Head-Gordon", 
                "corresponding_author": False
            },
            {
                "name": "Julie Forman-Kay", 
                "corresponding_author": False
            },
        ],
        "publication_status": "Unpublished",
        "publication_source": "",
        "publication_identifier": "",
        "publication_html": "bioRxiv DOI",
        "entry_cross_reference": [],
        "experimental_cross_reference": [],
        "experimental_procedure": "N/A",
        "structural_ensembles_calculation": "",
        "md_calculation": "Fixed backbone energy minimization simulation with the AMBER99sb force-field through OpenMM at 300 K for a maximum of 2 ns to resolve any sidechain clashes.",
        "ontology_terms": [
            {
                "name": "Molecular dynamics",
                "namespace": "Molecular dynamics",
                "id": "00219",
                "definition": "computational approach that simulates atom motion and investigates their location in space",
                "alias": [
                    "molecular dynamics"
                ]
                
            }
        ],
    }
    return data
