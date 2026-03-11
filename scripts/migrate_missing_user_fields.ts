import { getFirestore, collection, getDocs, updateDoc } from "firebase/firestore";
import { initializeApp } from "firebase/app";

// Initialize Firebase app (replace with your config or use env variables)
const firebaseConfig = {
  // TODO: Add your Firebase config here or load from environment variables
};

const app = initializeApp(firebaseConfig);
const db = getFirestore(app);

const missingFields: Record<string, any> = {
  address: "",
  phoneNumber: "",
  dateOfBirth: null,
  preferences: {}
};

async function migrate() {
  const usersSnap = await getDocs(collection(db, "users"));
  for (const doc of usersSnap.docs) {
    const data = doc.data();
    const updates: Record<string, any> = {};
    for (const [key, defaultVal] of Object.entries(missingFields)) {
      if (!(key in data)) {
        updates[key] = defaultVal;
      }
    }
    if (Object.keys(updates).length > 0) {
      await updateDoc(doc.ref, updates);
      console.log(`Updated user ${doc.id} with missing fields`);
    }
  }
  console.log("Migration complete");
}

migrate().catch(console.error);
