import { initializeApp } from "firebase/app";
import { getFirestore, doc, getDoc, setDoc } from "firebase/firestore";
import { getAuth } from "firebase/auth";

// Firebase configuration - replace with environment variables or your config
const firebaseConfig = {
  // TODO: add config
};

const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);
export const auth = getAuth(app);

export interface User {
  uid: string;
  name: string;
  email: string;
  avatarUrl?: string;
  address?: string;
  phoneNumber?: string;
  dateOfBirth?: string | null;
  preferences?: Record<string, any>;
}

export async function getUser(uid: string): Promise<User | null> {
  const userDoc = await getDoc(doc(db, "users", uid));
  if (!userDoc.exists()) return null;
  return userDoc.data() as User;
}

export async function setUser(user: User): Promise<void> {
  await setDoc(doc(db, "users", user.uid), user, { merge: true });
}
