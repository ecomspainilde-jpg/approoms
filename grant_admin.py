import firebase_admin
from firebase_admin import auth, firestore
import sys
import os

# Initialize Firebase Admin
project_id = os.environ.get("GCP_PROJECT_ID", "gen-lang-client-0426824151")
if not firebase_admin._apps:
    try:
        firebase_admin.initialize_app(options={'projectId': project_id})
        print(f"Initialized Firebase Admin for project: {project_id}")
    except Exception as e:
        print(f"Error initializing: {e}")
        sys.exit(1)

db = firestore.client()

def grant_admin(email):
    try:
        # 1. Get user by email
        user = auth.get_user_by_email(email)
        uid = user.uid
        print(f"Found user: {email} (UID: {uid})")

        # 2. Set Custom Claim (for backend API security)
        auth.set_custom_user_claims(uid, {'admin': True})
        print(f"✓ Custom claim 'admin: true' set for {email}")

        # 3. Update Firestore (for frontend UI checks)
        user_ref = db.collection('users').document(uid)
        user_doc = user_ref.get()
        
        if user_doc.exists:
            user_ref.update({'isAdmin': True})
        else:
            user_ref.set({
                'email': email,
                'isAdmin': True,
                'createdAt': firestore.SERVER_TIMESTAMP
            })
        print(f"✓ Firestore 'isAdmin: true' set for {email}")
        
        print(f"\nSUCCESS: {email} is now a full Administrator.")
        print("Note: The user may need to sign out and sign back in for the changes to take effect.")

    except auth.UserNotFoundError:
        print(f"Error: User with email {email} not found.")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python grant_admin.py user@example.com")
    else:
        grant_admin(sys.argv[1])
