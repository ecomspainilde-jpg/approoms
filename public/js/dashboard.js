// dashboard.js

document.addEventListener('DOMContentLoaded', () => {
    initAuth();
});

// This will be called by shared-auth.js when user state is confirmed
window.onAuthStateConfirmed = (user) => {
    loadUserRenders(user.uid);
};

async function loadUserRenders(uid) {
    const grid = document.getElementById('projects-grid');
    const emptyState = document.getElementById('empty-state');
    
    try {
        const db = firebase.firestore();
        const snapshot = await db.collection('renders')
            .where('userId', '==', uid)
            .orderBy('createdAt', 'desc')
            .get();

        if (snapshot.empty) {
            grid.classList.add('hidden');
            emptyState.classList.remove('hidden');
            return;
        }

        grid.classList.remove('hidden');
        emptyState.classList.add('hidden');
        grid.innerHTML = ''; // Clear skeletons

        snapshot.forEach(doc => {
            const render = doc.data();
            const date = render.createdAt?.toDate().toLocaleDateString('es-ES', { day: 'numeric', month: 'short', year: 'numeric' }) || 'Reciente';
            
            const card = document.createElement('div');
            card.className = "premium-card rounded-[2.5rem] overflow-hidden group fade-in";
            
            card.innerHTML = `
                <div class="relative aspect-square overflow-hidden bg-surface">
                    <img src="${render.outputUrl || render.inputUrl}" class="w-full h-full object-cover transition-all duration-1000 group-hover:scale-110" alt="${render.style || 'Habitación'}">
                    
                    <div class="absolute top-6 left-6 flex flex-col gap-3">
                        <div class="bg-white/90 backdrop-blur-md px-4 py-2 rounded-2xl border border-border shadow-sm">
                            <p class="text-[10px] font-black uppercase tracking-widest text-text-primary">${render.style || 'PROYECTO'}</p>
                        </div>
                        ${render.quality === 'high' ? `
                            <div class="bg-primary px-4 py-2 rounded-2xl border border-primary shadow-sm flex items-center gap-2">
                                <span class="material-symbols-outlined text-[14px] text-white font-black">verified</span>
                                <p class="text-[10px] font-black uppercase tracking-widest text-white">4K PREMIUM</p>
                            </div>
                        ` : ''}
                    </div>

                    ${render.status === 'processing' ? `
                        <div class="absolute inset-0 bg-white/80 backdrop-blur-md flex flex-col items-center justify-center p-10 text-center">
                            <div class="size-12 border-4 border-primary/20 border-t-primary rounded-full animate-spin mb-4"></div>
                            <p class="font-black text-xl tracking-tight text-text-primary">PROCESANDO...</p>
                        </div>
                    ` : `
                        <div class="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-4">
                            <a href="${render.outputUrl}" download class="size-12 bg-white rounded-2xl flex items-center justify-center text-text-primary hover:bg-primary hover:text-white transition-all hover:scale-110 shadow-xl">
                                <span class="material-symbols-outlined">download</span>
                            </a>
                            <button onclick="shareRender('${doc.id}')" class="size-12 bg-white rounded-2xl flex items-center justify-center text-text-primary hover:bg-primary hover:text-white transition-all hover:scale-110 shadow-xl">
                                <span class="material-symbols-outlined">share</span>
                            </button>
                        </div>
                    `}
                </div>
                <div class="p-8">
                    <div class="flex items-center justify-between mb-2">
                        <h3 class="text-xl font-black tracking-tight text-text-primary uppercase">${render.roomType || 'Habitación'}</h3>
                        <span class="text-xs font-bold text-text-secondary/50">${date}</span>
                    </div>
                    <p class="text-sm text-text-secondary line-clamp-2">${render.prompt || 'Sin descripción adicional.'}</p>
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (err) {
        console.error("Error loading renders:", err);
        grid.innerHTML = '<div class="col-span-full py-20 bg-red-50 rounded-[3rem] border border-red-100 text-center"><p class="text-red-500 font-bold">Error al cargar la galería. Por favor intenta de nuevo.</p></div>';
    }
}

async function shareRender(id) {
    if (navigator.share) {
        try {
            await navigator.share({
                title: 'RenderRoom AI Design',
                text: '¡Mira este diseño que he creado!',
                url: window.location.origin + '/share.html?id=' + id
            });
        } catch (err) {
            console.log('User cancelled share');
        }
    } else {
        // Fallback: copy to clipboard
        const url = window.location.origin + '/share.html?id=' + id;
        navigator.clipboard.writeText(url);
        alert('Enlace copiado al portapapeles');
    }
}
