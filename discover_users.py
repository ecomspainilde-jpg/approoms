import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from dotenv import load_dotenv

load_dotenv()
project_id = os.environ.get("GCP_PROJECT_ID", "gen-lang-client-0426824151")

if not firebase_admin._apps:
    firebase_admin.initialize_app(options={"projectId": project_id})

db = firestore.client()

def list_some_users():
    print("Listing some users from Firestore...")
    users_ref = db.collection('users').limit(5)
    for doc in users_ref.stream():
        print(f"UID: {doc.id}, Email: {doc.to_dict().get('email')}, isAdmin: {doc.to_dict().get('isAdmin')}")

    print("\nListing some users from Auth...")
    page = auth.list_users()
    for user in page.users:
        print(f"UID: {user.uid}, Email: {user.email}")

if __name__ == "__main__":
    list_some_users()
