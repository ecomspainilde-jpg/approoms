import firebase_admin
from firebase_admin import auth, firestore
import os

# Initialize Firebase Admin
project_id = os.environ.get("GCP_PROJECT_ID", "gen-lang-client-0426824151")
if not firebase_admin._apps:
    firebase_admin.initialize_app(options={'projectId': project_id})

db = firestore.client()

def list_users():
    print("📋 Listing current users in Firestore...")
    users_ref = db.collection('users').stream()
    count = 0
    for doc in users_ref:
        u = doc.to_dict()
        email = u.get('email', 'No email')
        is_admin = u.get('isAdmin', False)
        print(f"- {email} (Admin: {is_admin}, UID: {doc.id})")
        count += 1
    
    if count == 0:
        print("No users found in Firestore yet.")

if __name__ == "__main__":
    list_users()
