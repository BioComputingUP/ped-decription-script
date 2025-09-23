import requests
import json
import os
import pandas as pd

url = "http://127.0.0.1:4205/v1"
log_file = "job_tracking_log.csv"
construct_folder = "const_files"

# Load the job tracking log
df_log = pd.read_csv(log_file)

for idx, row in df_log.iterrows():
    pdb_filename = row["filename"]
    draft_id = row["draft_id"]
    base_name = os.path.splitext(pdb_filename)[0]
    construct_filename = f"{base_name}_const.json"
    construct_path = os.path.join(construct_folder, construct_filename)

    if not os.path.exists(construct_path):
        print(f"❌ Construct file not found for {pdb_filename}: {construct_path}")
        continue

    with open(construct_path, "r") as f:
        construct_info = json.load(f)

    # POST construct info to the draft's chains endpoint
    try:
        response = requests.post(
            f"{url}/drafts/{draft_id}/chains",
            json=construct_info
        )
        response.raise_for_status()
        print(f"✅ Posted construct for {pdb_filename} (draft {draft_id})")
        print(response.json())
    except requests.RequestException as e:
        print(f"❌ Error posting construct for {pdb_filename}: {e}")


