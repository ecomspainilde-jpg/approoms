import os
import datetime
from google.cloud import firestore
import firebase_admin
from firebase_admin import credentials, firestore as firebase_firestore

# Mock or real project ID
project_id = "gen-lang-client-0426824151"

def setup_packages():
    # Initialize Firebase Admin if not already initialized
    if not firebase_admin._apps:
        firebase_admin.initialize_app(options={
            "projectId": project_id,
        })
    
    db = firebase_firestore.client()
    
    packages = [
        {
            "id": "package_5",
            "name": "Inicial",
            "price": 500,  # cents
            "creditsAmount": 5,
            "stripePriceId": "price_1T90E2KRXxBbG1iCL7WXo467",
            "isActive": True,
            "currency": "eur"
        },
        {
            "id": "package_10",
            "name": "Estándar",
            "price": 1000,
            "creditsAmount": 12,
            "stripePriceId": "price_1T96UZKRXxBbG1iCGEt3nYhw",
            "isActive": True,
            "currency": "eur"
        },
        {
            "id": "package_15",
            "name": "Profesional",
            "price": 1500,
            "creditsAmount": 20,
            "stripePriceId": "price_1T90EyKRXxBbG1iCQ26rHDav",
            "isActive": True,
            "currency": "eur"
        },
        {
            "id": "package_25",
            "name": "Premium",
            "price": 2500,
            "creditsAmount": 40,
            "stripePriceId": "price_1TBf6OKRXxBbG1iCqvm9pqpp",
            "isActive": True,
            "currency": "eur"
        }
    ]
    
    print(f"Setting up {len(packages)} packages in Firestore...")
    
    for pkg in packages:
        pkg_id = pkg.pop("id")
        pkg["updatedAt"] = datetime.datetime.now(datetime.timezone.utc)
        db.collection("packages").document(pkg_id).set(pkg)
        print(f"Updated package: {pkg_id}")

    # Also ensure render prices are set
    renders = [
        {"id": "render_normal", "price": 2.50},
        {"id": "render_high", "price": 5.00}
    ]
    for r in renders:
        rid = r.pop("id")
        db.collection("pricing").document(rid).set({
            "price": r["price"],
            "updatedAt": datetime.datetime.now(datetime.timezone.utc)
        })
        print(f"Updated pricing: {rid}")

if __name__ == "__main__":
    setup_packages()
