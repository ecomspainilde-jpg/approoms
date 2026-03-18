// ── Firebase Config ─────────────────────────────
const firebaseConfig = {
    projectId: "gen-lang-client-0426824151",
    appId: "1:124806819551:web:1c90d1154b458fa064036a",
    storageBucket: "gen-lang-client-0426824151.firebasestorage.app",
    apiKey: "AIzaSyDj99qdmDt4GiVeRkvCSfTOSDw3uqD-_Ew",
    authDomain: "gen-lang-client-0426824151.firebaseapp.com",
    messagingSenderId: "124806819551"
};

// Initialize Firebase
if (!firebase.apps.length) {
    firebase.initializeApp(firebaseConfig);
}

const db = firebase.firestore();
const auth = firebase.auth();
const storage = firebase.storage();
