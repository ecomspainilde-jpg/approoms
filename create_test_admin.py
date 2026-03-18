import firebase_admin
from firebase_admin import credentials, firestore, auth
import sys
import os
from dotenv import load_dotenv

load_dotenv()

project_id = os.environ.get("GCP_PROJECT_ID", "gen-lang-client-0426824151")

if not firebase_admin._apps:
    firebase_admin.initialize_app(options={"projectId": project_id})

db = firestore.client()

def create_admin(email):
    print(f"Buscando usuario con email: {email}...")
    try:
        user = auth.get_user_by_email(email)
        uid = user.uid
        print(f"Usuario encontrado. UID: {uid}")
        
        # Actualizar en Firestore
        user_ref = db.collection('users').doc(uid)
        user_ref.set({
            'isAdmin': True,
            'email': email,
            'updatedAt': firestore.SERVER_TIMESTAMP
        }, merge=True)
        
        print(f"¡Éxito! El usuario {email} ahora tiene permisos de administrador en Firestore.")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python create_test_admin.py <email>")
    else:
        create_admin(sys.argv[1])
