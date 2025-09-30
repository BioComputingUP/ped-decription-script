## `Job-description-PED.py`

This script automates the creation of **drafts** in the **PED database** from local PDB files and links them to their corresponding description information.

### 📌 Functionality
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
