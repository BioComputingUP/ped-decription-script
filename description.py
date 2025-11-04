import requests

session = requests.Session()
session.headers.update({"User-Agent": "AlphaFlex JSON Generator/1.1"})

def get_uniprot_name(uniprot_id):
    """
    Returns (protein_name, resolved_id)
    - protein_name: None if not found
    - resolved_id: may differ if the original UniProt ID was merged or updated
    """
    url = f"https://rest.uniprot.org/uniprotkb/{uniprot_id}.json"
    try:
        response = session.get(url, timeout=5)
        if response.status_code == 404:
            print(f"⚠️  UniProt ID not found: {uniprot_id}")
            return None, uniprot_id

        response.raise_for_status()
        data = response.json()

        # Detectar si el ID está obsoleto o combinado
        if "inactiveReason" in data:
            reason = data["inactiveReason"].get("inactiveReasonType", "unknown")
            merged_to = data["inactiveReason"].get("mergedTo", [])
            if merged_to:
                new_id = merged_to[0]
                print(f"↪️  UniProt ID {uniprot_id} was {reason}, merged to {new_id}")
                # Intentamos obtener el nombre del nuevo ID
                return get_uniprot_name(new_id)
            else:
                print(f"⚠️  UniProt ID {uniprot_id} is inactive ({reason})")
                return None, uniprot_id

        # Si es válido, tomamos el nombre
        name = (
            data.get("proteinDescription", {})
                .get("recommendedName", {})
                .get("fullName", {})
                .get("value")
        )
        if not name:
            alt_name = data.get("proteinDescription", {}).get("submissionNames", [])
            if alt_name and isinstance(alt_name, list):
                name = alt_name[0].get("fullName", {}).get("value")

        resolved_id = data.get("primaryAccession", uniprot_id)
        return (name or None, resolved_id)

    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout while querying UniProt for {uniprot_id}")
        return None, uniprot_id
    except requests.exceptions.RequestException as e:
        print(f"❌ Error querying UniProt {uniprot_id}: {e}")
        return None, uniprot_id


def get_disprot_id(uniprot_id):
    """
    Returns DisProt ID based on UniProt ID, or None if not available.
    """
    url = f"https://disprot.org/api/{uniprot_id}"
    try:
        response = session.get(url, timeout=5)
        if response.status_code == 404:
            return None
        response.raise_for_status()
        data = response.json()
        return data.get("disprot_id")
    except requests.exceptions.Timeout:
        print(f"⏱️ Timeout querying DisProt for {uniprot_id}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error querying DisProt {uniprot_id}: {e}")
        return None
    except Exception:
        return None


def create_description_json(uniprot_id):
    """
    Generates the JSON dictionary template for a PDB file.
    """
    data = {
        "title": [],
        "authors": [
            {"name": "Zi Hao Liu", "corresponding_author": False},
            {"name": "Oufan Zhang", "corresponding_author": False},
            {"name": "Stefano De Castro", "corresponding_author": False},
            {"name": "Kunyang Sun", "corresponding_author": False},
            {"name": "Teresa Head-Gordon", "corresponding_author": False},
            {"name": "Julie Forman-Kay", "corresponding_author": False},
        ],
        "publication_status": "Unpublished",
        "publication_source": "",
        "publication_identifier": "",
        "publication_html": "bioRxiv DOI",
        "entry_cross_reference": [],
        "experimental_cross_reference": [],
        "experimental_procedure": "N/A",
        "structural_ensembles_calculation": "",
        "md_calculation": (
            "Fixed backbone energy minimization simulation with the AMBER99sb "
            "force-field through OpenMM at 300 K for a maximum of 2 ns to resolve "
            "any sidechain clashes."
        ),
        "ontology_terms": [
            {
                "name": "Molecular dynamics",
                "namespace": "Molecular dynamics",
                "id": "00219",
                "definition": (
                    "Computational approach that simulates atom motion "
                    "and investigates their location in space"
                ),
                "alias": ["molecular dynamics"],
            }
        ],
    }
    return data
