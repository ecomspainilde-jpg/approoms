// profile.js — Gestión completa del perfil de usuario

document.addEventListener('DOMContentLoaded', () => {
    // Esperamos a que shared-auth.js inicialice auth
    // El listener de onAuthStateChanged en shared-auth.js se encargará del acceso
});

// ── Inicialización cuando Auth está listo ─────────────────────────────
// Usamos el listener nativo de Firebase ya que shared-auth.js no siempre
// expone un callback. Escuchamos directamente desde aquí.
auth.onAuthStateChanged(async (user) => {
    if (!user) return; // shared-auth.js ya redirige si no hay sesión

    // Poblar datos básicos de Auth (email, nombre)
    populateAuthData(user);

    // Cargar datos extendidos de Firestore
    await loadFirestoreProfile(user);

    // Cargar estadísticas
    loadStats(user.uid);

    // Configurar botón de foto
    setupPhotoUpload(user);
});

// ── Poblar datos de Firebase Auth ──────────────────────────────────────
function populateAuthData(user) {
    // Header principal y sidebar (IDs únicos)
    setValue('header-name-display', user.displayName || 'Usuario de RenderRoom');
    setValue('header-email-display', user.email);
    setValue('sidebar-name-display', user.displayName || 'Usuario de RenderRoom');
    setValue('sidebar-email-display', user.email);

    // Inputs del formulario
    setValue('input-name', user.displayName || '');
    setValue('input-email', user.email);

    // Foto de perfil (si proviene de Auth, ej. Google)
    if (user.photoURL) {
        setProfilePhoto(user.photoURL);
    }
}

// ── Cargar perfil extendido desde Firestore ────────────────────────────
async function loadFirestoreProfile(user) {
    try {
        const db = firebase.firestore();
        const doc = await db.collection('users').doc(user.uid).get();

        if (doc.exists) {
            const data = doc.data();

            // Campos del formulario
            setValue('input-name', data.name || data.displayName || user.displayName || '');
            setValue('input-phone', data.phone || '');
            setValue('input-location', data.location || '');

            // Nombre en header y sidebar
            const displayName = data.name || data.displayName || '';
            if (displayName) {
                setValue('header-name-display', displayName);
                setValue('sidebar-name-display', displayName);
            }

            // Créditos
            setValue('stat-credits', data.credits ?? 0);

            // Año de registro
            if (data.createdAt && data.createdAt.toDate) {
                const year = data.createdAt.toDate().getFullYear();
                setValue('stat-year', year);
            }

            // Foto de perfil almacenada en Firestore (URL de Storage)
            if (data.photoURL) {
                setProfilePhoto(data.photoURL);
            }
        } else {
            // Primera vez: crear documento con datos básicos de Auth
            await db.collection('users').doc(user.uid).set({
                name: user.displayName || '',
                email: user.email,
                phone: '',
                location: '',
                photoURL: user.photoURL || '',
                credits: 1,
                createdAt: firebase.firestore.FieldValue.serverTimestamp(),
                updatedAt: firebase.firestore.FieldValue.serverTimestamp()
            }, { merge: true });
        }
    } catch (err) {
        console.error('Error cargando perfil de Firestore:', err);
    }
}

// ── Cargar estadísticas de renders ─────────────────────────────────────
async function loadStats(uid) {
    try {
        const db = firebase.firestore();
        const snapshot = await db.collection('renders').where('userId', '==', uid).get();
        setValue('stat-renders', snapshot.size);
    } catch (err) {
        console.error('Error cargando estadísticas:', err);
    }
}

// ── Guardar perfil ─────────────────────────────────────────────────────
async function saveProfile() {
    const user = firebase.auth().currentUser;
    if (!user) return alert('No has iniciado sesión.');

    const btn = document.getElementById('btn-save');
    const originalHTML = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="material-symbols-outlined animate-spin">autorenew</span> Guardando...';

    const name     = document.getElementById('input-name')?.value?.trim() || '';
    const phone    = document.getElementById('input-phone')?.value?.trim() || '';
    const location = document.getElementById('input-location')?.value?.trim() || '';

    try {
        // 1. Actualizar nombre en Firebase Auth
        if (name) {
            await user.updateProfile({ displayName: name });
        }

        // 2. Actualizar Firestore
        const db = firebase.firestore();
        await db.collection('users').doc(user.uid).set({
            name:      name,
            phone:     phone,
            location:  location,
            email:     user.email,
            updatedAt: firebase.firestore.FieldValue.serverTimestamp()
        }, { merge: true });

        // 3. Refrescar UI
        setValue('header-name-display', name || 'Usuario de RenderRoom');
        setValue('sidebar-name-display', name || 'Usuario de RenderRoom');

        showToast('✅ Perfil actualizado con éxito', 'success');

    } catch (err) {
        console.error('Error guardando perfil:', err);
        showToast('❌ Error al guardar. Intenta de nuevo.', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalHTML;
    }
}

// ── Subida de foto de perfil ───────────────────────────────────────────
function setupPhotoUpload(user) {
    const cameraBtn = document.getElementById('btn-photo-upload');
    const fileInput = document.getElementById('input-photo-file');

    if (!cameraBtn || !fileInput) return;

    cameraBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', async (e) => {
        const file = e.target.files[0];
        if (!file) return;

        // Validar tipo y tamaño (máx 5MB)
        if (!file.type.startsWith('image/')) {
            return showToast('❌ Solo se permiten imágenes.', 'error');
        }
        if (file.size > 5 * 1024 * 1024) {
            return showToast('❌ La imagen no puede superar 5MB.', 'error');
        }

        cameraBtn.innerHTML = '<span class="material-symbols-outlined text-xl animate-spin">autorenew</span>';
        cameraBtn.disabled = true;

        try {
            // Subir a Firebase Storage
            const storageRef = firebase.storage().ref(`user-avatars/${user.uid}/avatar.jpg`);
            await storageRef.put(file);
            const downloadURL = await storageRef.getDownloadURL();

            // Actualizar Firebase Auth
            await user.updateProfile({ photoURL: downloadURL });

            // Actualizar Firestore
            await firebase.firestore().collection('users').doc(user.uid).set({
                photoURL: downloadURL,
                updatedAt: firebase.firestore.FieldValue.serverTimestamp()
            }, { merge: true });

            // Refrescar UI
            setProfilePhoto(downloadURL);
            showToast('✅ Foto actualizada con éxito', 'success');

        } catch (err) {
            console.error('Error subiendo foto:', err);
            showToast('❌ Error al subir la foto. Intenta de nuevo.', 'error');
        } finally {
            cameraBtn.innerHTML = '<span class="material-symbols-outlined text-xl">photo_camera</span>';
            cameraBtn.disabled = false;
            fileInput.value = '';
        }
    });
}

// ── Utilidades DOM ────────────────────────────────────────────────────

/** Establece el texto/valor en TODOS los elementos con ese ID (para duplicados en header/sidebar) */
function setAllById(id, value) {
    document.querySelectorAll(`#${id}`).forEach(el => {
        if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
            el.value = value;
        } else {
            el.innerText = value;
        }
    });
}

/** Establece valor en un único elemento por ID */
function setValue(id, value) {
    const el = document.getElementById(id);
    if (!el) return;
    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
        el.value = value;
    } else {
        el.innerText = value;
    }
}

/** Muestra la foto de perfil y oculta el placeholder */
function setProfilePhoto(url) {
    const img = document.getElementById('profile-picture');
    const placeholder = document.getElementById('profile-picture-placeholder');
    const sidebarAvatar = document.getElementById('sidebar-avatar-placeholder');

    if (img) {
        img.src = url;
        img.classList.remove('hidden');
    }
    if (placeholder) placeholder.classList.add('hidden');

    // Sidebar: reemplazar ícono con imagen
    if (sidebarAvatar) {
        sidebarAvatar.innerHTML = `<img src="${url}" class="size-full object-cover rounded-full" alt="Avatar">`;
        sidebarAvatar.classList.remove('bg-amber-500/10', 'text-amber-500');
    }
}

/** Toast de notificación (no usa alert nativo) */
function showToast(message, type = 'success') {
    let toast = document.getElementById('profile-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'profile-toast';
        toast.className = 'fixed bottom-6 right-6 z-[9999] px-6 py-4 rounded-2xl font-bold text-sm shadow-2xl transition-all duration-300 translate-y-20 opacity-0';
        document.body.appendChild(toast);
    }

    toast.innerText = message;
    toast.className = toast.className.replace(/bg-\S+/g, '');
    toast.classList.add(type === 'success' ? 'bg-green-500' : 'bg-red-500', 'text-white');

    // Animar entrada
    requestAnimationFrame(() => {
        toast.style.transform = 'translateY(0)';
        toast.style.opacity = '1';
    });

    // Animar salida
    setTimeout(() => {
        toast.style.transform = 'translateY(5rem)';
        toast.style.opacity = '0';
    }, 3500);
}

// ── Logout ────────────────────────────────────────────────────────────
async function handleLogout() {
    if (!confirm('¿Estás seguro de que quieres cerrar sesión?')) return;
    try {
        await firebase.auth().signOut();
        window.location.href = '01-landing-page.html';
    } catch (err) {
        console.error('Error al cerrar sesión:', err);
    }
}
