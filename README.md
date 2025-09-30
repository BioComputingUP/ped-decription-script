# **Upload IDPs ensambles to PED database - automated**
This repository contains Python scripts to automate the preparation and submission of IDRs ensambles generated with [IDPforge](https://arxiv.org/abs/2502.11326) to the PED server.  
It provides tools to generate JSON files with protein descriptions and chain construct information from PDB files, and to post these data to the PED database.

## **1. Description**

The workflow includes:

1. **Generating description and construct JSON files** (`description.py` + `construct.py` + `json_generation.py`)

3. **Submitting data to the PED database** (`Job-description-PED.py` and `construct-post-PED.py`)  
   Uses the generated JSON files to create drafts and upload constructs in PED (this is ultimately when drafts are already created).

This setup allows easy batch processing of multiple PDB files and ensures reproducible, consistent submissions to PED.

## **2. Scripts Overview**

### **2.1. `description.py`**

This script provides helper functions to generate JSON description files for PDB entries in the PED database.

#### Description 
`description.py` contains three main functions:

1. **`get_uniprot_name(uniprot_id)`**  
   - Queries the UniProt API to retrieve the full protein name for a given UniProt ID.

2. **`get_disprot_id(uniprot_id)`**  
   - Queries the DisProt API to get the corresponding DisProt ID for a given UniProt ID.  

3. **`create_description_json(uniprot_id)`**  
   - Generates a JSON dictionary template for a PDB file description.  
   - The returned dictionary includes fields such as:
     - `title`
     - `authors`
     - `publication_status`
     - `entry_cross_reference`
     - `experimental_cross_reference`
     - `experimental_procedure`
     - `structural_ensembles_calculation`
     - `ontology_terms`
    
### **2.2. `construct.py`**

This script provides helper functions to generate JSON construct files for drafts already generated in the PED database.

#### Description 

`construct.py` contains two main functions:

1. **`get_chain_sequences_and_last_residues(pdb_path)`**  
   - Extracts the amino acid sequence and last residue number for each chain in a PDB file.

2. **`create_construct_json(chain_info, uniprot_id, protein_name)`** 
   - Generates a JSON dictionary template for a PDB file construct.
   - The returned dictionary includes fields such as:
      - `chain_name`
      - `fragments`:
          - `description` (protein name from UniProt)
          - `source_sequence` (sequence)
          - `start_position` (always 1)
          - `end_position`
          - `uniprot_acc` (Uniprot ID)
          - `definition_type` ("Uniprot ACC")


### **2.3 `json_generation.py`**

#### Description:  
Main script to generate JSON files from PDB structures. For each PDB file, it creates:  
- **Description JSON:** Metadata about the protein (title, authors, publication info, cross-references) using `description.py`. These files are used later in **`Job-description-PED.py`** to create drafts in the PED database.  
- **Construct JSON:** Chain and fragment information (sequence, start/end positions, UniProt ID) using `construct.py`. These files are used later in **`construct-post-PED.py`** to post constructs to the PED database.  

#### Expected folder name / file 
- `pdb_files/` — Contains input PDB files

#### Created folders 
- `jsonFiles/` — Contains description JSON files of the PDBs in `pdb_files/`. The file names are the same as PDB now with .json
- `const_files/` — Contains construct JSON files of the PDBS in `pdb_files/`. The file names are the same as PDB now with _const.json
  
### **2.4 `Job-description-PED.py`**

This script automates the creation of **drafts** in the **PED database** from local PDB files and links them to their corresponding description information.

#### Description:
- Iterates through the `pdb_files` folder looking for `.pdb` files.  
- For each PDB file:
  - Finds the corresponding description JSON file in the `jsonFiles` folder.  
  - Creates a new **draft** in the PED server.  
  - Updates the draft with the description.  
  - Uploads the PDB file to create an **ensemble job**.  
- Maintains a **tracking log** (`job_tracking_log.csv`) containing:
  - Processed filename  
  - `draft_id` and `job_id` assigned by PED  
  - Job status  
  - PDB file size and start time

#### Expected folder name 

- `pdb_files/` — Contains input PDB files  
- `jsonFiles/` — Contains description `.json` files (same basename as PDB) 


### **2.5. `construct-post-PED.py`**

This script is used to upload construct information to existing drafts in the PED database.

#### Description:

After draft creation and JSON description files have been uploaded using `Job-description-PED.py`, this script will:

- Read the `job_tracking_log.csv` file to get all previously created drafts and their corresponding PDB filenames.
- For each PDB file, look for a corresponding construct JSON file in the `const_files/` folder. Construct JSON filenames must match the PDB filename with the suffix `_const.json`.
- Post the construct JSON to the PED API.
- Report success or errors for each submission.

#### Expected folder/archives

- `const_files/` — Contains construct JSON files (same prefix as PDB + "_const.json") 
- `job_tracking_log.csv` — Automatically created by Job-description-PED.py

## **3. Usage Example**

1. Place all PDB files in `pdb_sample/`.
2. Run the JSON generation script:
   ```bash
   python json_generation.py
   ```
3. Run `Job-description-PED.py`
   ```bash
   python Job-description-PED.py
   ```
4. Once drafts are created, run `construct-post-PED.py`
   ```bash
   python construct-post-PED.py
   ```
