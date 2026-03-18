import os
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()

project_id = os.environ.get("GCP_PROJECT_ID")
storage_bucket = os.environ.get("FIREBASE_STORAGE_BUCKET")

try:
    if not firebase_admin._apps:
        firebase_admin.initialize_app(options={
            "projectId": project_id,
            "storageBucket": storage_bucket
        })
    db = firestore.client()
    print(f"Connected to Firebase Project: {project_id}")
    
    collections = ["pricing", "users", "renders", "purchases", "packages", "transactions"]
    for coll in collections:
        docs = db.collection(coll).limit(1).get()
        print(f"Collection '{coll}': {'Found' if len(docs) > 0 else 'Empty or Not Found'}")
        
except Exception as e:
    print(f"Error: {e}")
