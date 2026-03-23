// Variables db and auth are already declared in firebase-config.js

const state = {
    currentStep: 1,
    imagesBase64: [],
    primaryIndex: 0,
    roomData: null,
    selectedStyle: 'moderno',
    selectedQuality: 'normal',
    prices: {
        normal: 2.50,
        high: 5.00
    },
    isGenerating: false,
    lastRenderId: null
};

// Global DOM elements (initialized in DOMContentLoaded)
let nextBtn, backBtn, disclaimerModal, dropzone, fileInput, dropzoneContent, imagePreview, analysisPanel;

document.addEventListener('DOMContentLoaded', () => {
    console.log("Upload Wizard Initializing (v2 Logic)...");
    
    // Initialize UI Elements
    nextBtn = document.getElementById('next-btn');
    backBtn = document.getElementById('back-btn');
    disclaimerModal = document.getElementById('disclaimer-modal');
    dropzone = document.getElementById('dropzone');
    fileInput = document.getElementById('file-input');
    fileInput.multiple = true;
    fileInput.accept = 'image/*';
    dropzoneContent = document.getElementById('dropzone-content');
    imagePreview = document.getElementById('image-preview');
    analysisPanel = document.getElementById('analysis-panel');

    if (!nextBtn || !dropzone || !fileInput) {
        console.error("Critical DOM elements missing for Upload Wizard!");
    }

    // Attach Event Listeners
    if (dropzone) {
        dropzone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropzone.classList.add('border-primary', 'bg-white/60');
        });

        dropzone.addEventListener('dragleave', () => {
            dropzone.classList.remove('border-primary', 'bg-white/60');
        });

        dropzone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropzone.classList.remove('border-primary', 'bg-white/60');
            const remaining = 3 - state.imagesBase64.length;
            const files = Array.from(e.dataTransfer.files).slice(0, remaining);
            if (files.length > 0) handleFiles(files);
        });

        dropzone.addEventListener('click', () => {
             if (fileInput) fileInput.click();
        });
    }

    if (fileInput) {
        fileInput.addEventListener('change', () => {
            const remaining = 3 - state.imagesBase64.length;
            const files = Array.from(fileInput.files).slice(0, remaining);
            if (files.length > 0) handleFiles(files);
            fileInput.value = '';
        });
    }

    const disclaimerCheck = document.getElementById('disclaimer-check');
    const disclaimerConfirm = document.getElementById('disclaimer-confirm');
    if (disclaimerCheck && disclaimerConfirm) {
        disclaimerCheck.addEventListener('change', () => {
            if (disclaimerCheck.checked) {
                disclaimerConfirm.classList.remove('opacity-50', 'cursor-not-allowed');
                disclaimerConfirm.disabled = false;
            } else {
                disclaimerConfirm.classList.add('opacity-50', 'cursor-not-allowed');
                disclaimerConfirm.disabled = true;
            }
        });
    }

    const changePhotoBtn = document.getElementById('change-photo-btn');
    if (changePhotoBtn) {
        changePhotoBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            resetUpload();
            if (fileInput) fileInput.click();
        });
    }

    // Disclaimer Visibility Logic
    if (disclaimerModal) {
        if (!sessionStorage.getItem('disclaimer_accepted')) {
            disclaimerModal.style.display = 'flex';
        } else {
            disclaimerModal.style.display = 'none';
        }
    }

    // Pre-select style from URL param
    const urlStyle = new URLSearchParams(location.search).get('style');
    if (urlStyle) {
        const preCard = document.querySelector(`.style-card[data-style="${urlStyle}"]`);
        if (preCard) selectStyle(preCard);
    }

    // Start Step 1
    goToStep1();
});

// Auth Listener
auth.onAuthStateChanged(async (user) => {
    if (!user) {
        console.log("No user session, redirecting to landing...");
        window.location.replace('01-landing-page.html');
        return;
    }
    console.log("User session active:", user.email);

    // Real-time listener for credits
    db.collection('users').doc(user.uid).onSnapshot(doc => {
        if (doc.exists) {
            const credits = doc.data().credits || 0;
            const creditEl = document.getElementById('header-credits-count');
            const buyBtn = document.getElementById('header-buy-credits-btn');
            if (creditEl) creditEl.textContent = credits;
            if (buyBtn) {
                if (credits <= 2) buyBtn.classList.remove('hidden');
                else buyBtn.classList.add('hidden');
            }
        }
    });

    // Check Admin
    try {
        const doc = await db.collection('users').doc(user.uid).get();
        if (doc.exists && doc.data().isAdmin) {
            const adminLink = document.getElementById('admin-link-container');
            if (adminLink) adminLink.classList.remove('hidden');
        }
    } catch (e) {}

    // Load Prices
    fetchPrices();

    const token = await user.getIdToken();
    localStorage.setItem('rr_token', token);
    document.documentElement.classList.add('auth-checked');
});

// ÔöÇÔöÇ Utility Functions ÔöÇÔöÇÔöÇÔöÇÔöÇ
function getAuthHeaders() {
    const token = localStorage.getItem('rr_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

async function fetchPrices() {
    try {
        const res = await fetch('/api/admin/pricing');
        const data = await res.json();
        if (data.render_normal) state.prices.normal = data.render_normal.price;
        if (data.render_high) state.prices.high = data.render_high.price;
        
        const pNormal = document.getElementById('price-display-normal');
        const pHigh = document.getElementById('price-display-high');
        if (pNormal) pNormal.textContent = `${state.prices.normal.toFixed(2).replace('.', ',')}€`;
        if (pHigh) pHigh.textContent = `${state.prices.high.toFixed(2).replace('.', ',')}€`;
    } catch (e) {
        console.warn("Fallo cargando precios din├ímicos, usando defaults.");
    }
}

// ÔöÇÔöÇ Core Wizard Flow ÔöÇÔöÇÔöÇÔöÇÔöÇ
async function handleFiles(files) {
    if (files.length === 0) return;
    
    // Limit total to 3
    const available = 3 - state.imagesBase64.length;
    const toProcess = Array.from(files).slice(0, available);
    if (toProcess.length === 0) return;
    
    const readFile = (file) => new Promise((resolve) => {
        const reader = new FileReader();
        reader.onload = (e) => resolve({ src: e.target.result, b64: e.target.result.split(',')[1] });
        reader.readAsDataURL(file);
    });
    
    try {
        const results = await Promise.all(toProcess.map(readFile));
        results.forEach(r => {
            state.imagesBase64.push(r.b64);
        });
        
        // Set primary to first image if not set
        if (state.primaryIndex >= state.imagesBase64.length) state.primaryIndex = 0;
        
        renderImageGrid();
        
        // Analyze using the primary image
        await analyzeImage();
    } catch (err) {
        console.error('handleFiles ERROR:', err);
        alert('Error al procesar la imagen.');
    }
}

function renderImageGrid() {
    if (!imagePreview || !dropzoneContent) return;
    
    if (state.imagesBase64.length === 0) {
        imagePreview.classList.add('hidden');
        dropzoneContent.classList.remove('hidden');
        return;
    }
    
    // Build HTML for the image grid
    const canAddMore = state.imagesBase64.length < 3;
    
    imagePreview.innerHTML = `
        <div class="space-y-4 w-full">
            <p class="text-xs font-bold text-stone-500 uppercase tracking-widest">
                ${state.imagesBase64.length} de 3 fotos · Tap para seleccionar la principal
            </p>
            <div class="grid grid-cols-3 gap-3">
                ${state.imagesBase64.map((b64, i) => `
                    <div 
                        class="relative aspect-square rounded-2xl overflow-hidden cursor-pointer border-4 transition-all ${
                            i === state.primaryIndex 
                            ? 'border-amber-500 shadow-lg shadow-amber-500/30' 
                            : 'border-transparent hover:border-amber-300'
                        }"
                        onclick="setPrimary(${i})"
                    >
                        <img src="data:image/jpeg;base64,${b64}" class="w-full h-full object-cover">
                        ${i === state.primaryIndex ? `
                            <div class="absolute top-2 left-2 bg-amber-500 text-white text-[10px] font-black px-2 py-0.5 rounded-full uppercase tracking-wider">
                                Principal
                            </div>
                        ` : ''}
                        <button 
                            onclick="removeImage(event, ${i})" 
                            class="absolute top-2 right-2 w-6 h-6 rounded-full bg-stone-900/80 text-white flex items-center justify-center hover:bg-red-500 transition-all pointer-events-auto"
                        >
                            <span class="material-symbols-outlined text-[14px]">close</span>
                        </button>
                    </div>
                `).join('')}
                ${canAddMore ? `
                    <button 
                        onclick="addMoreImages()" 
                        class="aspect-square rounded-2xl border-2 border-dashed border-stone-300 flex flex-col items-center justify-center gap-2 text-stone-400 hover:border-amber-400 hover:text-amber-500 transition-all cursor-pointer"
                    >
                        <span class="material-symbols-outlined text-3xl">add_photo_alternate</span>
                        <span class="text-[10px] font-bold">Añadir</span>
                    </button>
                ` : ''}
            </div>
        </div>
    `;
    
    imagePreview.classList.remove('hidden');
    dropzoneContent.classList.add('hidden');
}

window.setPrimary = function(idx) {
    state.primaryIndex = idx;
    renderImageGrid();
    analyzeImage(); // Re-analyze with the new primary
};

window.removeImage = function(e, idx) {
    e.stopPropagation();
    state.imagesBase64.splice(idx, 1);
    if (state.primaryIndex >= state.imagesBase64.length) {
        state.primaryIndex = Math.max(0, state.imagesBase64.length - 1);
    }
    if (state.imagesBase64.length === 0) {
        resetUpload();
    } else {
        renderImageGrid();
        analyzeImage();
    }
};

window.addMoreImages = function() {
    if (fileInput) fileInput.click();
};

async function analyzeImage() {
    const loading = document.getElementById('analysis-loading');
    const resultPanel = document.getElementById('analysis-result');
    const errorPanel = document.getElementById('analysis-error');

    if (analysisPanel) analysisPanel.classList.remove('hidden');
    if (loading) loading.classList.remove('hidden');
    if (resultPanel) resultPanel.classList.add('hidden');
    if (errorPanel) errorPanel.classList.add('hidden');

    try {
        const imageToAnalyze = state.imagesBase64[state.primaryIndex] || state.imagesBase64[0];
        const res = await fetch('/api/analyze-image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify({ images_base64: [imageToAnalyze] })
        });
        
        const data = await res.json();
        if (loading) loading.classList.add('hidden');
        
        if (res.ok && data.detailed_description_es) {
            state.roomData = data;
            const analysisHtml = `
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="bg-primary/5 p-4 rounded-2xl border border-primary/10">
                        <p class="text-[10px] text-text-secondary uppercase font-black tracking-widest mb-1">Tipo de Habitación</p>
                        <p class="text-sm font-black text-text-primary capitalize">${data.room_type || 'Habitación'}</p>
                    </div>
                    <div class="bg-primary/5 p-4 rounded-2xl border border-primary/10">
                        <p class="text-[10px] text-text-secondary uppercase font-black tracking-widest mb-1">Tamaño Estimado</p>
                        <p class="text-sm font-black text-text-primary capitalize">${data.approx_size || 'Estándar'}</p>
                    </div>
                </div>
                <p class="text-text-secondary text-sm leading-relaxed">${data.detailed_description_es}</p>
            `;
            document.getElementById('analysis-text').innerHTML = analysisHtml;
            
            // Validation badges
            const v = data.image_validation;
            if (v) {
                const score = v.viability_score || 100;
                const badge = document.getElementById('validation-badge');
                if (badge) {
                     document.getElementById('validation-score').textContent = score + '%';
                     document.getElementById('image-validation-panel').classList.remove('hidden');
                }
            }
            
            setBtnEnabled(nextBtn, true);
        } else {
            document.getElementById('analysis-error-text').textContent = data.error || 'Error del servicio';
            errorPanel.classList.remove('hidden');
        }
    } catch (err) {
        if (loading) loading.classList.add('hidden');
        errorPanel.classList.remove('hidden');
        console.error("analyzeImage error:", err);
    }
}

function renderImageGrid() {
    if (!imagePreview || !dropzoneContent) return;
    
    if (state.imagesBase64.length === 0) {
        imagePreview.classList.add('hidden');
        dropzoneContent.classList.remove('hidden');
        return;
    }
    
    const canAddMore = state.imagesBase64.length < 3;
    
    // Inject grid HTML
    imagePreview.innerHTML = `
        <div class="space-y-4 w-full">
            <div class="flex items-center justify-between">
                <p class="text-[10px] font-black text-stone-500 uppercase tracking-[0.2em]">
                    ${state.imagesBase64.length} / 3 FOTOS SELECCIONADAS
                </p>
                <button onclick="resetUpload()" class="text-[10px] font-black text-primary uppercase tracking-widest hover:underline">
                    Borrar todas
                </button>
            </div>
            
            <div class="grid grid-cols-3 gap-3">
                ${state.imagesBase64.map((img, i) => `
                    <div onclick="setPrimary(${i})" class="relative group aspect-square rounded-2xl overflow-hidden cursor-pointer border-4 transition-all duration-300 ${i === state.primaryIndex ? 'border-primary shadow-lg shadow-primary/20 scale-[1.02]' : 'border-white/10 hover:border-primary/50'}">
                        <img src="data:image/jpeg;base64,${img}" class="w-full h-full object-cover">
                        ${i === state.primaryIndex ? `
                            <div class="absolute top-2 left-2 bg-primary text-white text-[8px] font-black px-2 py-0.5 rounded-full uppercase tracking-tighter">
                                Principal
                            </div>
                        ` : ''}
                        <button onclick="removeImage(event, ${i})" class="absolute top-2 right-2 size-6 rounded-full bg-stone-900/80 text-white flex items-center justify-center hover:bg-red-500 transition-colors opacity-0 group-hover:opacity-100">
                            <span class="material-symbols-outlined text-sm">close</span>
                        </button>
                    </div>
                `).join('')}
                
                ${canAddMore ? `
                    <button onclick="addMorePhotos()" class="aspect-square rounded-2xl border-2 border-dashed border-stone-300 flex flex-col items-center justify-center gap-1 text-stone-400 hover:border-primary hover:text-primary transition-all group">
                        <span class="material-symbols-outlined text-2xl group-hover:scale-110 transition-transform">add_a_photo</span>
                        <span class="text-[9px] font-black uppercase tracking-tighter">Añadir</span>
                    </button>
                ` : ''}
            </div>
            
            <div class="bg-primary/5 rounded-xl p-3 border border-primary/10">
                <p class="text-[10px] text-primary font-bold leading-tight">
                    <span class="material-symbols-outlined text-xs align-middle mr-1">info</span>
                    Toca una imagen para marcarla como la **principal** para el diseño.
                </p>
            </div>
        </div>
    `;

    imagePreview.classList.remove('hidden');
    dropzoneContent.classList.add('hidden');
}

window.setPrimary = function(index) {
    if (state.primaryIndex === index) return;
    state.primaryIndex = index;
    renderImageGrid();
    analyzeImage(); // Re-analyze with new primary
};

window.removeImage = function(e, index) {
    e.stopPropagation();
    state.imagesBase64.splice(index, 1);
    if (state.primaryIndex >= state.imagesBase64.length) {
        state.primaryIndex = Math.max(0, state.imagesBase64.length - 1);
    }
    renderImageGrid();
    if (state.imagesBase64.length > 0) analyzeImage();
    else resetUpload();
};

window.addMorePhotos = function() {
    if (fileInput) fileInput.click();
};

function selectStyle(card) {
    document.querySelectorAll('.style-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    state.selectedStyle = card.dataset.style;
    
    // Update recommendations UI
    if (state.roomData && state.roomData.recommendations) {
        const recName = document.getElementById('rec-style-name');
        if (recName) recName.textContent = state.selectedStyle;
        document.getElementById('recommendations-section').classList.remove('hidden');
        
        const addList = document.getElementById('rec-add-list');
        const removeList = document.getElementById('rec-remove-list');
        if (addList) {
             addList.innerHTML = state.roomData.recommendations.add_es.map(item => `
                <label class="flex items-center gap-3 p-3 bg-background-dark/20 border border-white/5 rounded-xl cursor-pointer hover:bg-white/5 transition-all group">
                    <input type="checkbox" data-type="add" data-item="${item}" checked class="peer hidden">
                    <div class="size-5 rounded-md border border-white/20 flex items-center justify-center peer-checked:bg-green-500 peer-checked:border-green-500 transition-all">
                        <span class="material-symbols-outlined text-[14px] text-white">check</span>
                    </div>
                    <span class="text-sm text-slate-300 group-hover:text-white transition-colors capitalize">${item}</span>
                </label>
             `).join('');
        }
        if (removeList) {
             removeList.innerHTML = state.roomData.recommendations.remove_es.map(item => `
                <label class="flex items-center gap-3 p-3 bg-background-dark/20 border border-white/5 rounded-xl cursor-pointer hover:bg-white/5 transition-all group">
                    <input type="checkbox" data-type="remove" data-item="${item}" checked class="peer hidden">
                    <div class="size-5 rounded-md border border-white/20 flex items-center justify-center peer-checked:bg-orange-500 peer-checked:border-orange-500 transition-all">
                        <span class="material-symbols-outlined text-[14px] text-white">close</span>
                    </div>
                    <span class="text-sm text-slate-300 group-hover:text-white transition-colors capitalize">${item}</span>
                </label>
             `).join('');
        }
    }
    
    setBtnEnabled(nextBtn, true);
}

function selectQuality(q) {
    state.selectedQuality = q;
    document.querySelectorAll('.quality-card').forEach(c => {
        c.classList.remove('selected');
        const check = c.querySelector('.material-symbols-outlined');
        if (check) check.classList.add('opacity-0');
    });
    const sel = document.querySelector(`.quality-card[data-quality="${q}"]`);
    if (sel) {
        sel.classList.add('selected');
        const check = sel.querySelector('.material-symbols-outlined');
        if (check) check.classList.remove('opacity-0');
    }
}

function nextStep() {
    if (state.currentStep === 1) goToStep2();
    else if (state.currentStep === 2) goToStep3();
}

function prevStep() {
    if (state.currentStep === 2) goToStep1();
    else if (state.currentStep === 3) goToStep2();
}

function goToStep1() {
    state.currentStep = 1;
    showSection('section-upload');
    setActiveStep(1);
    setBtnEnabled(nextBtn, state.imagesBase64.length > 0);
    if (backBtn) backBtn.classList.add('invisible');
}

function goToStep2() {
    if (state.imagesBase64.length === 0) return alert('Sube una foto.');
    state.currentStep = 2;
    showSection('section-style');
    setActiveStep(2);
    setBtnEnabled(nextBtn, !!state.selectedStyle);
    if (backBtn) backBtn.classList.remove('invisible');
    if (nextBtn) nextBtn.classList.remove('hidden');
}

function goToStep3() {
    if (!state.selectedStyle) return alert('Elige un estilo.');
    state.currentStep = 3;
    
    const summaryPreview = document.getElementById('summary-preview');
    if (summaryPreview && state.imagesBase64.length > 0) {
        summaryPreview.src = `data:image/jpeg;base64,${state.imagesBase64[0]}`;
    }
    document.getElementById('summary-style').textContent = state.selectedStyle.toUpperCase();
    document.getElementById('summary-prompt').textContent = document.getElementById('prompt-input').value || '(sin detalles adicionales)';
    
    showSection('section-generate');
    setActiveStep(3);
    if (nextBtn) nextBtn.classList.add('hidden');
    if (backBtn) backBtn.classList.remove('invisible');
}

function setActiveStep(n) {
    [1,2,3].forEach(i => {
        const el = document.getElementById(`step-indicator-${i}`);
        if (!el) return;
        el.classList.remove('step-active','step-done','step-inactive');
        if (i < n) {
            el.classList.add('step-done');
            el.innerHTML = '<span class="material-symbols-outlined text-sm">check</span>';
        } else if (i === n) {
            el.classList.add('step-active');
            el.innerHTML = i;
        } else {
            el.classList.add('step-inactive');
            el.innerHTML = i;
        }
    });
}

function showSection(id) {
    ['section-upload', 'section-style', 'section-generate', 'result-panel'].forEach(sid => {
        const el = document.getElementById(sid);
        if (el) el.classList.toggle('hidden', sid !== id);
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function setBtnEnabled(btn, on) {
    if (!btn) return;
    btn.disabled = !on;
    if (on) {
        btn.classList.remove('opacity-50', 'cursor-not-allowed');
        btn.classList.add('bg-primary', 'hover:scale-[1.02]');
    } else {
        btn.classList.add('opacity-50', 'cursor-not-allowed');
        btn.classList.remove('bg-primary', 'hover:scale-[1.02]');
    }
}

function resetUpload() {
    state.imagesBase64 = [];
    state.primaryIndex = 0;
    state.roomData = null;
    if (dropzoneContent) dropzoneContent.classList.remove('hidden');
    if (imagePreview) {
        imagePreview.classList.add('hidden');
        imagePreview.innerHTML = '';
    }
    if (analysisPanel) analysisPanel.classList.add('hidden');
    setBtnEnabled(nextBtn, false);
    if (fileInput) fileInput.value = '';
}

// ÔöÇÔöÇ Generation Logic ÔöÇÔöÇÔöÇÔöÇÔöÇ
async function generateRender() {
    const btn = document.getElementById('btn-generate');
    if (!btn || state.isGenerating) return;
    
    state.isGenerating = true;
    btn.disabled = true;
    btn.innerHTML = '<span class="material-symbols-outlined spin text-sm">sync</span> Generando...';
    
    const progressPanel = document.getElementById('gen-progress');
    if (progressPanel) progressPanel.classList.remove('hidden');

    // Combine prompt — use a default style prompt if empty
    const promptInputEl = document.getElementById('prompt-input');
    const userPrompt = (promptInputEl ? promptInputEl.value.trim() : '') || `Redecorate this room in ${state.selectedStyle} style with high quality results.`;
    const addChecktips = Array.from(document.querySelectorAll('#rec-add-list input:checked')).map(i => i.dataset.item);
    const removeChecktips = Array.from(document.querySelectorAll('#rec-remove-list input:checked')).map(i => i.dataset.item);
    
    let fullPrompt = userPrompt;
    if (addChecktips.length) fullPrompt += '. Add: ' + addChecktips.join(', ');
    if (removeChecktips.length) fullPrompt += '. Remove: ' + removeChecktips.join(', ');

    const primaryImage = state.imagesBase64[state.primaryIndex] || state.imagesBase64[0];
    try {
        const res = await fetch('/api/generate-image', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify({
                prompt: fullPrompt,
                style: state.selectedStyle,
                quality: state.selectedQuality,
                image_base64: primaryImage
            })
        });
        
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error en generaci├│n');
        
        showResult(data);
    } catch (err) {
        alert(err.message);
        btn.disabled = false;
        btn.innerHTML = '<span class="material-symbols-outlined">auto_awesome</span> Reintentar';
    } finally {
        state.isGenerating = false;
    }
}

function showResult(data) {
    state.lastRenderId = data.image_id;
    const imgSrc = `data:image/png;base64,${data.image_base64}`;
    const resultImg = document.getElementById('result-image');
    if (resultImg) resultImg.src = imgSrc;
    
    const downloadBtn = document.getElementById('download-btn');
    if (downloadBtn) downloadBtn.href = imgSrc;
    
    showSection('result-panel');
}

// Export functions for HTML
window.acceptDisclaimer = function() {
    sessionStorage.setItem('disclaimer_accepted', '1');
    if (disclaimerModal) {
        disclaimerModal.style.opacity = '0';
        setTimeout(() => disclaimerModal.style.display = 'none', 300);
    }
};
window.nextStep = nextStep;
window.prevStep = prevStep;
window.selectStyle = selectStyle;
window.selectQuality = selectQuality;
window.generateRender = generateRender;
window.resetUpload = resetUpload;
window.goToStep1 = goToStep1;
window.goToStep2 = goToStep2;
window.goToStep3 = goToStep3;
