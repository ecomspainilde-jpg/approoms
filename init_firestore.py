import firebase_admin
from firebase_admin import credentials, firestore
import os

# Initialize Firebase if not already initialized
if not firebase_admin._apps:
    cred = credentials.ApplicationDefault()
    firebase_admin.initialize_app(cred, {
        'projectId': 'gen-lang-client-0426824151',
    })

db = firestore.client()

def initialize_packages():
    packages = [
        {
            "id": "package_5",
            "name": "5 EUROS DE SALDO",
            "price": 500,  # in cents
            "creditsAmount": 5,
            "stripePriceId": "price_1T90E2KRXxBbG1iCL7WXo467",
            "isActive": True,
            "order": 1
        },
        {
            "id": "package_10",
            "name": "10 EUROS DE SALDO",
            "price": 1000,
            "creditsAmount": 12, # Bonus credits
            "stripePriceId": "price_1T96UZKRXxBbG1iCGEt3nYhw",
            "isActive": True,
            "order": 2
        },
        {
            "id": "package_15",
            "name": "15 EUROS DE SALDO",
            "price": 1500,
            "creditsAmount": 20, # Bonus credits
            "stripePriceId": "price_1T90EyKRXxBbG1iCQ26rHDav",
            "isActive": True,
            "order": 3
        },
        {
            "id": "package_25",
            "name": "25 EUROS DE SALDO",
            "price": 2500,
            "creditsAmount": 40, # High bonus
            "stripePriceId": "price_1TBf6OKRXxBbG1iCqvm9pqpp",
            "isActive": True,
            "order": 4
        }
    ]

    print("Initializing packages...")
    for pkg in packages:
        pkg_id = pkg.pop("id")
        db.collection("packages").document(pkg_id).set(pkg)
        print(f"Set package: {pkg_id}")

def initialize_pricing():
    pricing = [
        {
            "id": "render_normal",
            "name": "Calidad Normal",
            "price": 250, # 2.50 EUR
            "description": "Renderizado estándar"
        },
        {
            "id": "render_high",
            "name": "Alta Calidad",
            "price": 500, # 5.00 EUR
            "description": "Renderizado fotorrealista premium"
        }
    ]

    print("Initializing render pricing...")
    for item in pricing:
        item_id = item.pop("id")
        db.collection("pricing").document(item_id).set(item)
        print(f"Set pricing: {item_id}")

if __name__ == "__main__":
    initialize_packages()
    initialize_pricing()
    print("Done!")
