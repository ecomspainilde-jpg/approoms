import firebase_admin
from firebase_admin import credentials, firestore, auth
import os
from dotenv import load_dotenv

load_dotenv()
project_id = os.environ.get("GCP_PROJECT_ID", "gen-lang-client-0426824151")

if not firebase_admin._apps:
    firebase_admin.initialize_app(options={"projectId": project_id})

db = firestore.client()

def promote_first_user():
    print("Promoting the first user found in Auth to Admin...")
    page = auth.list_users()
    if not page.users:
        print("No users found in Auth.")
        return

    user = page.users[0]
    uid = user.uid
    email = user.email
    print(f"Found user: {email} (UID: {uid})")
    
    # Update Firestore
    db.collection('users').document(uid).set({
        'isAdmin': True,
        'email': email,
        'updatedAt': firestore.SERVER_TIMESTAMP
    }, merge=True)
    
    # Update Custom Claims
    auth.set_custom_user_claims(uid, {"admin": True})
    
    print(f"User {email} is now a FULL ADMIN (Firestore + Custom Claims).")

if __name__ == "__main__":
    promote_first_user()
