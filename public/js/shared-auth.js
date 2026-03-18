/**
 * ── Shared Auth Logic ─────────────────────────────────
 * Handles global authentication state, redirection for private pages,
 * and common UI updates like the navbar user profile.
 */

const PRIVATE_PAGES = [
    '02-upload-wizard.html',
    '03-dashboard.html',
    '06-perfil-usuario.html',
    'creditos.html',
    '04-pago-bizum.html',
    '05-gracias.html',
    'admin-dashboard.html'
];

const PUBLIC_PAGES = [
    '01-landing-page.html',
    'index.html'
];

// Initialize Auth Listener
auth.onAuthStateChanged((user) => {
    const currentPage = window.location.pathname.split('/').pop() || 'index.html';
    
    if (user) {
        console.log('User signed in:', user.email);
        updateNavbar(user);
        
        // Setup Firestore listener for credits
        db.collection('users').doc(user.uid).onSnapshot(doc => {
            if (doc.exists) {
                const data = doc.data();
                const countEls = document.querySelectorAll('#header-credits-count');
                const displayEls = document.querySelectorAll('#header-credits-display');
                
                countEls.forEach(el => el.textContent = data.credits || 0);
                displayEls.forEach(el => el.classList.remove('hidden'));
            } else {
                // Initial user document creation
                db.collection('users').doc(user.uid).set({
                    displayName: user.displayName,
                    email: user.email,
                    credits: 1, // Welcome credit
                    createdAt: firebase.firestore.FieldValue.serverTimestamp()
                }, { merge: true });
            }
        });

        // Redirect start button if it exists
        const startBtn = document.getElementById('start-btn');
        if (startBtn && PUBLIC_PAGES.includes(currentPage)) {
            startBtn.innerHTML = '<span class="material-symbols-outlined font-bold">dashboard</span> Ir a mi Panel';
            startBtn.onclick = () => window.location.href = '03-dashboard.html';
        }
    } else {
        console.log('No user signed in.');
        
        // Redirect if on a private page
        if (PRIVATE_PAGES.includes(currentPage)) {
            window.location.href = '01-landing-page.html?auth=required';
        }
        
        updateNavbar(null);
    }
});

/**
 * Updates the navigation bar based on auth state
 */
function updateNavbar(user) {
    const loggedOutEl = document.getElementById('user-logged-out') || document.getElementById('nav-login-btn');
    const loggedInEl = document.getElementById('user-logged-in') || document.getElementById('nav-user-dropdown');
    const userNameEl = document.getElementById('nav-user-name') || document.getElementById('user-name-display');
    const userAvatarEl = document.getElementById('user-avatar');

    if (user) {
        if (loggedOutEl) loggedOutEl.classList.add('hidden');
        if (loggedInEl) loggedInEl.classList.remove('hidden', 'md:hidden');
        if (loggedInEl) loggedInEl.style.display = 'flex'; // Ensure flex layout
        
        if (userNameEl) userNameEl.innerText = user.displayName || 'Usuario';
        if (userAvatarEl && user.photoURL) userAvatarEl.src = user.photoURL;
    } else {
        if (loggedOutEl) loggedOutEl.classList.remove('hidden');
        if (loggedInEl) loggedInEl.classList.add('hidden');
        if (loggedInEl) loggedInEl.style.display = 'none';
    }
}

/**
 * Common sign out function
 */
async function handleSignOut() {
    try {
        await auth.signOut();
        window.location.href = '01-landing-page.html';
    } catch (error) {
        console.error('Logout error:', error);
    }
}

/**
 * Helper to show messages in UI
 */
function showMsg(el, text, type) {
    if (!el) return;
    el.innerText = text;
    el.className = `text-sm font-bold mt-2 ${type === 'error' ? 'text-red-500' : 'text-green-500'}`;
    setTimeout(() => { el.innerText = ''; }, 5000);
}
