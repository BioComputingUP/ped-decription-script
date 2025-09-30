## `Job-description-PED.py`

This script automates the creation of **drafts** in the **PED database** from local PDB files and links them to their corresponding description information.

### Description
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

### 📂 Expected folder name 

- `pdb_files/` — Contains `.pdb` files  
- `jsonFiles/` — Contains description `.json` files (same basename as PDB)


## `construct-post-PED.py`

This script is used to upload construct information to existing drafts in the PED database.

### Description

After draft creation and JSON description files have been uploaded using `Job-description-PED.py`, this script will:

1. Read the `job_tracking_log.csv` file to get all previously created drafts and their corresponding PDB filenames.
2. For each PDB file, look for a corresponding construct JSON file in the `const_files/` folder. Construct JSON filenames must match the PDB filename with the suffix `_const.json`.
3. Post the construct JSON to the PED API.
4. Report success or errors for each submission.

### 📂 Expected folder/archives

- `const_files/` — Contains construct JSON files (same prefix as PDB + "_const.json")
- `job_tracking_log.csv` — Automatically created by Job-description-PED.py

