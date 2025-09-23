import requests
import json
import time
import os
import pandas as pd
from datetime import datetime

url= "http://127.0.0.1:4205/v1"
log_file = "job_tracking_log.csv"

# Draft creation

if os.path.exists(log_file):
    df_log = pd.read_csv(log_file)
else:
    df_log = pd.DataFrame(columns=[
        "filename", "draft_id", "job_id", "status", 
        "start_time", "pdb_size_bytes"
    ])

for file in os.listdir("pdb_files"):
    if file.endswith(".pdb"):
        print("PDB file found:", file)
        pdb_file_path = os.path.join("pdb_files", file)
        print(f"\n🚀 Processing: {file}")

        # Find matching JSON description file in jsonFiles folder
        desc_filename = os.path.splitext(file)[0] + ".json"
        desc_filepath = os.path.join("jsonFiles", desc_filename)
        if not os.path.exists(desc_filepath):
            print(f"❌ Description file not found for {file}: {desc_filepath}")
            continue

        with open(desc_filepath, "r") as Description_file:
            Description_file_Data = json.load(Description_file)

        if file in df_log['filename'].values:
            print(f"⏭️ Skipping already processed: {file}")
            continue

        start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print("Start time:", start_time)
        pdb_size = os.path.getsize(pdb_file_path)

        try:
            request_draft = requests.post(url + "drafts")
            json_data = request_draft.json()
            draft_id = json_data['draft_id']
            print("Draft ID:", draft_id)
            print('Draft created successfully!')

            request_description = requests.post(url + "drafts/" + draft_id + "/description", json=Description_file_Data)
            print("Description updated successfully!")

            # JOB CREATION 
            with open(pdb_file_path, "rb") as pdb_file:
                file_data = {'pdbfile': pdb_file}
                request_job = requests.post(url + "drafts/" + draft_id + "/ensembles", files=file_data)
                request_job_data = request_job.json()

                job_id = request_job_data['job']['job_id']
                job_status = request_job_data['job']['status']
                print("Job ID:", job_id)
                print("Job created successfully!")

        except requests.exceptions.RequestException as e:
            print(f"❌ Error processing {file}: {e}")
            continue

        df_log = pd.concat([df_log, pd.DataFrame([{
            "filename": file,
            "draft_id": draft_id,
            "job_id": job_id,
            "status": job_status,
            "start_time": start_time,
            "pdb_size_bytes": pdb_size
        }])], ignore_index=True)

        # Save after each iteration (safe for large batches or crashes)
        df_log.to_csv(log_file, index=False)




# while True:
#     try:
#         response = requests.get(url+'drafts/'+draft_id+'/ensembles/e001')
#         response.raise_for_status()  # raise an error for bad responses (4xx or 5xx)

#         data = response.json()
#         status = data.get("job", {}).get("status")

#         print(f"Current status: {status}")

#         if status == "job finished normally":
#             print("✅ Job completed!")
#             break
#         elif status and "deleted" in status.lower():
#             print("⚠️ Job was deleted.")
#             break
#         else:
#             # Wait before polling again (e.g., 5 seconds)
#             time.sleep(10)

#     except requests.RequestException as e:
#         print(f"Request failed: {e}")
#         time.sleep(10)  # optional: retry after a pause






 