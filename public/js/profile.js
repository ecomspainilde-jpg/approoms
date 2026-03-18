// profile.js

document.addEventListener('DOMContentLoaded', () => {
    initAuth();
});

// This will be called by shared-auth.js when user state is confirmed
window.onAuthStateConfirmed = (user) => {
    displayUserData(user);
    loadStats(user.uid);
};

function displayUserData(user) {
    // Basic Auth Info
    document.getElementById('user-name-display').innerText = user.displayName || 'Usuario de RenderRoom';
    document.getElementById('user-email-display').innerText = user.email;
    document.getElementById('input-name').value = user.displayName || '';
    document.getElementById('input-email').value = user.email;

    // Profile Picture
    const img = document.getElementById('profile-picture');
    const placeholder = document.getElementById('profile-picture-placeholder');
    if (user.photoURL) {
        img.src = user.photoURL;
        img.classList.remove('hidden');
        placeholder.classList.add('hidden');
    }

    // Extended Firestore Info
    const db = firebase.firestore();
    db.collection('users').doc(user.uid).get().then(doc => {
        if (doc.exists) {
            const data = doc.data();
            document.getElementById('input-phone').value = data.phone || '';
            document.getElementById('input-location').value = data.location || '';
            document.getElementById('stat-credits').innerText = data.credits || 0;
        }
    });
}

async function loadStats(uid) {
    const db = firebase.firestore();
    const snapshot = await db.collection('renders').where('userId', '==', uid).get();
    document.getElementById('stat-renders').innerText = snapshot.size;
}

async function saveProfile() {
    const user = firebase.auth().currentUser;
    if (!user) return;

    const btn = document.getElementById('btn-save');
    const originalText = btn.innerText;
    btn.disabled = true;
    btn.innerText = 'Guardando...';

    const name = document.getElementById('input-name').value;
    const phone = document.getElementById('input-phone').value;
    const location = document.getElementById('input-location').value;

    try {
        // Update Auth Profile
        await user.updateProfile({ displayName: name });

        // Update Firestore
        const db = firebase.firestore();
        await db.collection('users').doc(user.uid).set({
            name: name,
            phone: phone,
            location: location,
            updatedAt: firebase.firestore.FieldValue.serverTimestamp()
        }, { merge: true });

        // Refresh UI
        document.getElementById('user-name-display').innerText = name;
        alert('Perfil actualizado con éxito');

    } catch (err) {
        console.error("Error saving profile:", err);
        alert('Error al guardar el perfil. Intenta de nuevo.');
    } finally {
        btn.disabled = false;
        btn.innerText = originalText;
    }
}

async function handleLogout() {
    if (confirm('¿Estás seguro de que quieres cerrar sesión?')) {
        try {
            await firebase.auth().signOut();
            window.location.href = '01-landing-page.html';
        } catch (err) {
            console.error("Error signing out:", err);
        }
    }
}
