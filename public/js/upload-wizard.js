const db = firebase.firestore();
const auth = firebase.auth();

auth.onAuthStateChanged(async (user) => {
    if (!user) {
        window.location.replace('01-landing-page.html');
        return;
    }

    // Real-time listener for credits
    db.collection('users').doc(user.uid).onSnapshot(doc => {
        if (doc.exists) {
            const credits = doc.data().credits || 0;
            const creditEl = document.getElementById('header-credits-count');
            const buyBtn = document.getElementById('header-buy-credits-btn');
            if (creditEl) creditEl.textContent = credits;
            if (buyBtn) {
                // Show buy button if credits are low (e.g., 2 or less)
                if (credits <= 2) buyBtn.classList.remove('hidden');
                else buyBtn.classList.add('hidden');
            }
        }
    }, err => console.error("Credit listener error:", err));

    try {
        const doc = await db.collection('users').doc(user.uid).get();
        if (doc.exists && doc.data().isAdmin) {
            const adminLink = document.getElementById('admin-link-container');
            if (adminLink) adminLink.classList.remove('hidden');
        }
    } catch (e) {
        console.error("Admin check error:", e);
    }

    // Load dynamic prices
    fetchPrices();

    const token = await user.getIdToken();
    localStorage.setItem('rr_token', token);
    document.documentElement.classList.add('auth-checked');
});

function getAuthHeaders() {
    const token = localStorage.getItem('rr_token');
    return token ? { 'Authorization': `Bearer ${token}` } : {};
}

// ─── Disclaimer Modal ──────────────────────────────────────────────────────────
const disclaimerModal = document.getElementById('disclaimer-modal');
const disclaimerCheck = document.getElementById('disclaimer-check');
const disclaimerConfirm = document.getElementById('disclaimer-confirm');

if (disclaimerModal) {
    if (!sessionStorage.getItem('disclaimer_accepted')) {
        disclaimerModal.style.display = 'flex';
    } else {
        disclaimerModal.style.display = 'none';
    }
}

if (disclaimerCheck && disclaimerConfirm) {
    disclaimerCheck.addEventListener('change', () => {
        if (disclaimerCheck.checked) {
            disclaimerConfirm.disabled = false;
            disclaimerConfirm.classList.remove('bg-primary/30','text-primary/50','cursor-not-allowed');
            disclaimerConfirm.classList.add('bg-primary','text-background-dark','hover:bg-primary/90','cursor-pointer');
        } else {
            disclaimerConfirm.disabled = true;
            disclaimerConfirm.classList.add('bg-primary/30','text-primary/50','cursor-not-allowed');
            disclaimerConfirm.classList.remove('bg-primary','text-background-dark','hover:bg-primary/90','cursor-pointer');
        }
    });
}
function acceptDisclaimer() {
    sessionStorage.setItem('disclaimer_accepted', '1');
    if (disclaimerModal) disclaimerModal.style.display = 'none';
}

// ÔöÇÔöÇ State ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
let state = {
    imagesBase64: [], // Store up to 3 images
    primaryIndex: 0,  // Index of the main photo for the render
    roomData: null,   // Store JSON analysis
    selectedStyle: null,
    selectedQuality: 'normal',
    prices: {
        normal: 2.50,
        high: 5.00
    },
    currentStep: 1,
};

async function fetchPrices() {
    try {
        const res = await fetch('/api/admin/pricing');
        const data = await res.json();
        if (data.render_normal) state.prices.normal = data.render_normal.price;
        if (data.render_high) state.prices.high = data.render_high.price;
        
        // Update UI
        const pNormal = document.getElementById('price-display-normal');
        const pHigh = document.getElementById('price-display-high');
        if (pNormal) pNormal.textContent = `${state.prices.normal.toFixed(2).replace('.', ',')}€`;
        if (pHigh) pHigh.textContent = `${state.prices.high.toFixed(2).replace('.', ',')}€`;
    } catch (e) {
        console.error("Error fetching prices:", e);
    }
}

function selectQuality(q) {
    state.selectedQuality = q;
    document.querySelectorAll('.quality-card').forEach(c => {
        c.classList.remove('selected');
        // Handle nested internal elements if they exist
        const check = c.querySelector('.material-symbols-outlined');
        if (check) check.classList.add('opacity-0');
        const checkBg = c.querySelector('div.rounded-full');
        if (checkBg) checkBg.classList.remove('border-primary', 'bg-primary');
    });
    
    const selectedCard = document.querySelector(`.quality-card[data-quality="${q}"]`);
    if (selectedCard) {
        selectedCard.classList.add('selected');
        const check = selectedCard.querySelector('.material-symbols-outlined');
        if (check) check.classList.remove('opacity-0');
        const checkBg = selectedCard.querySelector('div.rounded-full');
        if (checkBg) checkBg.classList.add('border-primary', 'bg-primary');
    }
}

// ————— Upload Zone ————————————————————————————————————————————————————————————
const dropzone = document.getElementById('dropzone');
const fileInput = document.getElementById('file-input');
const dropzoneContent = document.getElementById('dropzone-content');
const imagePreview = document.getElementById('image-preview');
const nextBtn = document.getElementById('next-btn');
const backBtn = document.getElementById('back-btn');
const analysisPanel = document.getElementById('analysis-panel');

const changePhotoBtn = document.getElementById('change-photo-btn');
if (changePhotoBtn) {
    changePhotoBtn.addEventListener('click', () => {
        resetUpload();
        fileInput.click();
    });
}

dropzone.addEventListener('dragover', (e) => { e.preventDefault(); dropzone.classList.add('border-primary'); });
dropzone.addEventListener('dragleave', () => dropzone.classList.remove('border-primary'));
dropzone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('border-primary');
    const files = Array.from(e.dataTransfer.files).slice(0, 1);
    if (files.length > 0) handleFiles(files);
});

fileInput.addEventListener('change', () => {
    const files = Array.from(fileInput.files).slice(0, 1);
    if (files.length > 0) handleFiles(files);
});

function resetUpload() {
    state.imagesBase64 = [];
    state.primaryIndex = 0;
    state.roomData = null;
    dropzoneContent.classList.remove('hidden');
    imagePreview.classList.add('hidden');
    analysisPanel.classList.add('hidden');
    setBtnEnabled(nextBtn, false);
    fileInput.value = '';
}

async function handleFiles(files) {
    if (files.length === 0) return;
    
    state.imagesBase64 = [];
    state.primaryIndex = 0;
    
    const file = files[0];
    const reader = new FileReader();
    
    reader.onload = async (e) => {
        const base64 = e.target.result.split(',')[1];
        state.imagesBase64 = [base64];
        
        // Update Preview
        const previewImg = document.getElementById('preview-img');
        if (previewImg) {
            previewImg.src = e.target.result;
            document.getElementById('image-preview').classList.remove('hidden');
            document.getElementById('dropzone-content').classList.add('hidden');
        }
        
        await analyzeImage();
    };
    reader.readAsDataURL(file);
}

function setPrimaryPhoto(idx) {
    state.primaryIndex = idx;
    document.querySelectorAll('.photo-thumb').forEach(t => t.classList.remove('primary'));
    const selected = previewGrid.querySelector(`.photo-thumb[data-idx="${idx}"]`);
    if (selected) selected.classList.add('primary');
    
    // RE-ANALIZAR para que la geometr├¡a coincida con la nueva foto principal
    analyzeImage();
}

async function analyzeImage() {
    const loading = document.getElementById('analysis-loading');
    const resultPanel = document.getElementById('analysis-result');
    const errorPanel = document.getElementById('analysis-error');
    const panel = document.getElementById('analysis-panel');

    if (panel) panel.classList.remove('hidden');
    if (loading) loading.classList.remove('hidden');
    if (resultPanel) resultPanel.classList.add('hidden');
    if (errorPanel) errorPanel.classList.add('hidden');

    try {
        // REORDENAR: Ponemos la foto principal al principio de la lista para el servidor
        const orderedImages = [...state.imagesBase64];
        if (state.primaryIndex > 0) {
            const primary = orderedImages.splice(state.primaryIndex, 1)[0];
            orderedImages.unshift(primary);
        }

        const res = await fetch('/api/analyze-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({ images_base64: orderedImages })
        });
        const data = await res.json();
        if (loading) loading.classList.add('hidden');
        
        if (res.ok && data.detailed_description_es) {
            state.roomData = data;
            const analysisHtml = `
                <div class="grid grid-cols-2 gap-4 mb-4">
                    <div class="bg-primary/5 p-4 rounded-2xl border border-primary/10">
                        <p class="text-[10px] text-text-secondary uppercase font-black tracking-widest mb-1">Tipo de Habitación</p>
                        <p class="text-sm font-black text-text-primary capitalize">${data.room_type || 'Detectando...'}</p>
                    </div>
                    <div class="bg-primary/5 p-4 rounded-2xl border border-primary/10">
                        <p class="text-[10px] text-text-secondary uppercase font-black tracking-widest mb-1">Tamaño Estimado</p>
                        <p class="text-sm font-black text-text-primary capitalize">${data.approx_size || data.dimensions_est || 'Detectando...'}</p>
                    </div>
                </div>
                <p class="text-text-secondary text-sm leading-relaxed">${data.detailed_description_es}</p>
            `;
            document.getElementById('analysis-text').innerHTML = analysisHtml;
            document.getElementById('analysis-panel').classList.remove('hidden');

            // ── Image Validation UI ──────────────────────────────────────────────────────────
            const v = data.image_validation;
            if (v) {
                const score = v.viability_score ?? 100;
                const ok = v.viability_ok !== false; // default allow if field missing
                const issues = v.viability_issues_es || [];

                // Badge color
                const badge = document.getElementById('validation-badge');
                const icon = document.getElementById('validation-icon');
                const label = document.getElementById('validation-label');
                const scoreEl = document.getElementById('validation-score');

                badge.className = 'flex items-center gap-2 px-3 py-1.5 rounded-xl text-[10px] font-black uppercase tracking-widest';
                if (score >= 90) {
                    badge.classList.add('bg-green-500/10', 'text-green-600', 'border', 'border-green-500/20');
                    icon.textContent = 'check_circle';
                    label.textContent = 'Perfecta para render';
                } else if (score >= 70) {
                    badge.classList.add('bg-primary/10', 'text-primary', 'border', 'border-primary/20');
                    icon.textContent = 'warning';
                    label.textContent = 'Válida con advertencias';
                } else if (score >= 40) {
                    badge.classList.add('bg-orange-500/10', 'text-orange-600', 'border', 'border-orange-500/20');
                    icon.textContent = 'report_problem';
                    label.textContent = 'Calidad baja';
                } else {
                    badge.classList.add('bg-red-500/10', 'text-red-600', 'border', 'border-red-500/20');
                    icon.textContent = 'cancel';
                    label.textContent = 'No apta para render';
                }
                scoreEl.textContent = `${score}%`;

                // Issues list
                const issuesEl = document.getElementById('validation-issues');
                if (issuesEl) {
                    if (issues.length > 0) {
                        issuesEl.innerHTML = issues.map(i =>
                            `<div class="flex items-start gap-2 text-[11px] font-bold text-orange-600 bg-orange-500/5 px-3 py-2 rounded-lg border border-orange-500/10">
                                <span class="material-symbols-outlined text-sm mt-0.5 flex-shrink-0">info</span>
                                <span>${i}</span>
                            </div>`
                        ).join('');
                        issuesEl.classList.remove('hidden');
                    } else {
                        issuesEl.innerHTML = '';
                        issuesEl.classList.add('hidden');
                    }
                }

                document.getElementById('image-validation-panel').classList.remove('hidden');

                // Block or allow advancing
                if (!ok) {
                    setBtnEnabled(nextBtn, false);
                    const errorEl = document.getElementById('analysis-error');
                    const errorText = document.getElementById('analysis-error-text');
                    errorText.textContent = 'La imagen no es apta para generar un render. Por favor, sube una foto diferente siguiendo los consejos de abajo.';
                    errorEl.classList.remove('hidden');
                    return;
                }
            }
            setBtnEnabled(nextBtn, true);
        } else {
            if (loading) loading.classList.add('hidden');
            document.getElementById('analysis-error-text').textContent = data.error || 'Error del servicio';
            document.getElementById('analysis-error').classList.remove('hidden');
            setBtnEnabled(nextBtn, false);
        }
    } catch (err) {
        document.getElementById('analysis-loading').classList.add('hidden');
        document.getElementById('analysis-error-text').textContent = 'Sin conexi├│n al servidor';
        document.getElementById('analysis-error').classList.remove('hidden');
    }
    setBtnEnabled(nextBtn, true);
}

// ÔöÇÔöÇ Style selector ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
function selectStyle(card) {
    document.querySelectorAll('.style-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    state.selectedStyle = card.dataset.style;
    showRecommendations();
    setBtnEnabled(nextBtn, true);
}

function showRecommendations() {
    if (!state.roomData || !state.roomData.recommendations) return;
    
    document.getElementById('rec-style-name').textContent = state.selectedStyle;
    document.getElementById('recommendations-section').classList.remove('hidden');
    
    const addList = document.getElementById('rec-add-list');
    const removeList = document.getElementById('rec-remove-list');
    
    addList.innerHTML = '';
    removeList.innerHTML = '';
    
    state.roomData.recommendations.add_es.forEach((item, i) => {
        const div = document.createElement('label');
        div.className = 'flex items-center gap-3 p-3 bg-background-dark/20 border border-white/5 rounded-xl cursor-pointer hover:bg-white/5 transition-all group';
        div.innerHTML = `
            <div class="relative flex items-center justify-center">
                <input type="checkbox" class="peer appearance-none size-5 rounded-md border border-white/20 bg-transparent checked:bg-green-500 checked:border-green-500 transition-all cursor-pointer" data-type="add" data-item="${item}" checked>
                <span class="material-symbols-outlined text-[14px] text-white absolute opacity-0 peer-checked:opacity-100 transition-opacity pointer-events-none">check</span>
            </div>
            <span class="text-sm text-slate-300 group-hover:text-white transition-colors capitalize">${item}</span>
        `;
        addList.appendChild(div);
    });
    
    state.roomData.recommendations.remove_es.forEach((item, i) => {
        const div = document.createElement('label');
        div.className = 'flex items-center gap-3 p-3 bg-background-dark/20 border border-white/5 rounded-xl cursor-pointer hover:bg-white/5 transition-all group';
        div.innerHTML = `
            <div class="relative flex items-center justify-center">
                <input type="checkbox" class="peer appearance-none size-5 rounded-md border border-white/20 bg-transparent checked:bg-orange-500 checked:border-orange-500 transition-all cursor-pointer" data-type="remove" data-item="${item}" checked>
                <span class="material-symbols-outlined text-[14px] text-white absolute opacity-0 peer-checked:opacity-100 transition-opacity pointer-events-none">close</span>
            </div>
            <span class="text-sm text-slate-300 group-hover:text-white transition-colors capitalize">${item}</span>
        `;
        removeList.appendChild(div);
    });
}

// Pre-select style from URL param
const urlStyle = new URLSearchParams(location.search).get('style');
if (urlStyle) {
    const preCard = document.querySelector(`.style-card[data-style="${urlStyle}"]`);
    if (preCard) selectStyle(preCard);
}

// ÔöÇÔöÇ Navigation ÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇÔöÇ
function setBtnEnabled(btn, on) {
    if (on) {
        btn.disabled = false;
        btn.classList.remove('bg-primary/30','text-primary/50','cursor-not-allowed');
        btn.classList.add('bg-primary','text-background-dark','hover:bg-primary/90','cursor-pointer');
    } else {
        btn.disabled = true;
        btn.classList.add('bg-primary/30','text-primary/50','cursor-not-allowed');
        btn.classList.remove('bg-primary','text-background-dark','hover:bg-primary/90','cursor-pointer');
    }
}

function nextStep() {
    if (state.currentStep === 1) {
        goToStep2();
    } else if (state.currentStep === 2) {
        goToStep3();
    }
}

function prevStep() {
    if (state.currentStep === 2) {
        goToStep1();
    } else if (state.currentStep === 3) {
        goToStep2();
    }
}

function goToStep1() {
    showSection('section-upload');
    setActiveStep(1);
    setBtnEnabled(nextBtn, state.imagesBase64.length > 0);
    backBtn.classList.add('invisible');
}

function goToStep2() {
    if (state.imagesBase64.length === 0) { alert('Por favor, sube al menos una foto.'); return; }
    showSection('section-style');
    setActiveStep(2);
    setBtnEnabled(nextBtn, !!state.selectedStyle);
    backBtn.classList.remove('invisible');
    nextBtn.classList.remove('hidden');
}

function goToStep3() {
    if (!state.selectedStyle) { alert('Por favor, elige un estilo.'); return; }
    // Update summary preview
    const summaryPreview = document.getElementById('summary-preview');
    if (summaryPreview && state.imagesBase64.length > 0) {
        summaryPreview.src = `data:image/jpeg;base64,${state.imagesBase64[state.primaryIndex]}`;
    }

    document.getElementById('summary-style').textContent = state.selectedStyle.charAt(0).toUpperCase() + state.selectedStyle.slice(1);
    const roomInfo = state.roomData ? `${state.roomData.room_type} (${state.roomData.approx_size})` : '';
    document.getElementById('summary-style').innerHTML = `${state.selectedStyle.charAt(0).toUpperCase() + state.selectedStyle.slice(1)} <span class="text-xs text-text-secondary ml-2">${roomInfo}</span>`;
    document.getElementById('summary-prompt').textContent = document.getElementById('prompt-input').value || '(sin descripción adicional)';
    
    showSection('section-generate');
    setActiveStep(3);
    nextBtn.classList.add('hidden'); // Use the main generate button instead
    backBtn.classList.remove('invisible');
}

function updateStepper() {
    for (let i = 1; i <= 3; i++) {
        const indicator = document.getElementById(`step-indicator-${i}`);
        const text = indicator.nextElementSibling;
        
        indicator.classList.remove('step-active', 'step-done', 'step-inactive');
        
        if (i < state.currentStep) {
            indicator.classList.add('step-done');
            indicator.innerHTML = '<span class="material-symbols-outlined text-sm">check</span>';
        } else if (i === state.currentStep) {
            indicator.classList.add('step-active');
            indicator.innerHTML = i;
        } else {
            indicator.classList.add('step-inactive');
            indicator.innerHTML = i;
        }
    }
}

function showSection(id) {
    // Current IDs are section-upload, section-style, section-generate, result-panel
    const sections = ['section-upload', 'section-style', 'section-generate', 'result-panel'];
    sections.forEach(sid => {
        const el = document.getElementById(sid);
        if (el) {
            if (sid === id) el.classList.remove('hidden');
            else el.classList.add('hidden');
        }
    });
    window.scrollTo({ top: 0, behavior: 'smooth' });
}

function setActiveStep(n) {
    state.currentStep = n;
    [1,2,3].forEach(i => {
        const el = document.getElementById(`step-indicator-${i}`);
        if (!el) return;
        el.classList.remove('step-active','step-done','step-inactive');
        if (i < n) {
            el.classList.add('step-done');
            el.closest('.flex')?.classList.remove('opacity-40');
            el.innerHTML = '<span class="material-symbols-outlined text-sm">check</span>';
        } else if (i === n) {
            el.classList.add('step-active');
            el.closest('.flex')?.classList.remove('opacity-40');
            el.innerHTML = i;
        } else {
            el.classList.add('step-inactive');
            el.closest('.flex')?.classList.add('opacity-40');
            el.innerHTML = i;
        }
    });
}

// Generate
async function generateRender() {
    const btn = document.getElementById('btn-generate');
    btn.disabled = true;
    btn.innerHTML = '<svg class="spin size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg> Procesando…';

    const prompt = document.getElementById('prompt-input').value || 'Una habitación bella y acogedora';
    const primaryImageB64 = state.imagesBase64[state.primaryIndex] || state.imagesBase64[0] || null;

    const progressPanel = document.getElementById('gen-progress');
    progressPanel.classList.remove('hidden');
    const errBoxOld = document.getElementById('gen-error-box');
    if (errBoxOld) errBoxOld.remove();

    // Reset progress UI
    document.getElementById('check-pay').classList.add('hidden');
    document.getElementById('spin-pay').classList.remove('hidden');
    document.getElementById('label-pay').classList.add('text-primary');
    document.getElementById('label-pay').classList.remove('text-green-500');
    
    document.getElementById('check-ai').classList.add('hidden');
    document.getElementById('spin-ai').classList.add('hidden');
    document.getElementById('label-ai').classList.remove('text-primary','text-green-500');

    // Gather checked recommendations
    const selectedAdd = Array.from(document.querySelectorAll('#rec-add-list input:checked')).map(i => i.dataset.item);
    const selectedRemove = Array.from(document.querySelectorAll('#rec-remove-list input:checked')).map(i => i.dataset.item);
    
    let enhancedPrompt = prompt;
    if (selectedAdd.length > 0) enhancedPrompt += ". PLEASE ADD: " + selectedAdd.join(", ");
    if (selectedRemove.length > 0) enhancedPrompt += ". PLEASE REMOVE/REPLACE: " + selectedRemove.join(", ");

    try {
        // Step 1: Real credit check via generation attempt
        const currentUser = firebase.auth().currentUser;
        if (currentUser) {
            const freshToken = await currentUser.getIdToken(true);
            localStorage.setItem('rr_token', freshToken);
        }

        const res = await fetch('/api/generate-image', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                ...getAuthHeaders()
            },
            body: JSON.stringify({
                prompt: enhancedPrompt,
                room_data: state.roomData,
                style: state.selectedStyle,
                quality: state.selectedQuality,
                image_base64: primaryImageB64
            })
        });
        
        const data = await res.json();

        if (res.status === 402) {
            // Out of credits
            document.getElementById('spin-pay').classList.add('hidden');
            document.getElementById('label-pay').textContent = 'Pago Requerido';
            document.getElementById('label-pay').classList.replace('text-primary', 'text-amber-500');
            
            btn.disabled = false;
            btn.innerHTML = '<span class="material-symbols-outlined">payments</span> Comprar Créditos';
            btn.onclick = () => window.open('modal-compra.html?error=insufficient_credits', 'Purchase', 'width=1000,height=800');
            
            const errBox = document.createElement('div');
            errBox.id = 'gen-error-box';
            errBox.className = 'mt-4 bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 text-amber-400 text-sm flex items-start gap-2 fade-in';
            errBox.innerHTML = `<span class="material-symbols-outlined text-sm mt-0.5 flex-shrink-0">toll</span><div><strong>No tienes créditos suficientes:</strong><br>Necesitas al menos 1 crédito para generar este render. <a href="modal-compra.html?error=insufficient_credits" target="_blank" class="underline font-bold">Haz clic aquí para añadir créditos.</a></div>`;
            progressPanel.after(errBox);
            return;
        }

        if (!res.ok) throw new Error(data.error || 'Error generando imagen');

        // Success flow
        document.getElementById('spin-pay').classList.add('hidden');
        document.getElementById('check-pay').classList.remove('hidden');
        document.getElementById('label-pay').classList.replace('text-primary', 'text-green-500');
        
        document.getElementById('spin-ai').classList.remove('hidden');
        document.getElementById('label-ai').classList.add('text-primary');

        // In a real app, the AI part is already done by the time /api/generate-image returns.
        // We just simulate the feeling of it finishing for the UI steps.
        setTimeout(() => {
            document.getElementById('spin-ai').classList.add('hidden');
            document.getElementById('check-ai').classList.remove('hidden');
            document.getElementById('label-ai').classList.replace('text-primary', 'text-green-500');
            showResult(data, prompt);
            btn.disabled = false;
            btn.innerHTML = '<span class="material-symbols-outlined">auto_awesome</span> Generar Otro';
        }, 1500);

    } catch(err) {
        document.getElementById('spin-pay').classList.add('hidden');
        document.getElementById('spin-ai').classList.add('hidden');
        btn.disabled = false;
        btn.innerHTML = '<span class="material-symbols-outlined">auto_awesome</span> Reintentar';
        const errBox = document.createElement('div');
        errBox.id = 'gen-error-box';
        errBox.className = 'mt-4 bg-red-500/10 border border-red-500/30 rounded-xl p-4 text-red-400 text-sm flex items-start gap-2 fade-in';
        errBox.innerHTML = `<span class="material-symbols-outlined text-sm mt-0.5 flex-shrink-0">error</span><div><strong>Error al generar:</strong><br>${err.message}</div>`;
        progressPanel.after(errBox);
    }
}

// PDF & Sharing
async function generatePDF() {
    const btn = document.getElementById('btn-pdf');
    const originalText = btn.innerHTML;
    btn.disabled = true;
    btn.innerHTML = '<span class="material-symbols-outlined spin text-sm">sync</span> Generando propuesta...';
    
    try {
        // Build inline render data as fallback when render wasn't saved to Firestore
        const inlineRenderData = {
            room_type: state.roomData ? state.roomData.room_type : 'Habitación',
            approx_size: state.roomData ? state.roomData.approx_size : '',
            style: state.selectedStyle || 'moderno',
            roomData: state.roomData || {},
            createdAt: new Date().toISOString()
        };

        const payload = {
            renderId: state.lastRenderId || null,
            // Always send renderData as fallback (used when render is not found in Firestore)
            renderData: inlineRenderData
        };

        const res = await fetch('/api/generate-pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', ...getAuthHeaders() },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (data.success) {
            if (data.pdfUrl) {
                window.open(data.pdfUrl, '_blank');
            } else if (data.pdfBase64) {
                // Fallback: open from base64 when Storage is unavailable
                const byteChars = atob(data.pdfBase64);
                const byteArr = new Uint8Array(byteChars.length);
                for (let i = 0; i < byteChars.length; i++) byteArr[i] = byteChars.charCodeAt(i);
                const blob = new Blob([byteArr], { type: 'application/pdf' });
                const url = URL.createObjectURL(blob);
                window.open(url, '_blank');
                setTimeout(() => URL.revokeObjectURL(url), 60000);
            }
        } else {
            alert("Error al generar PDF: " + data.error);
        }
    } catch (e) {
        console.error(e);
        alert("Fallo de conexión al generar PDF");
    } finally {
        btn.disabled = false;
        btn.innerHTML = originalText;
    }
}

function shareResult(platform) {
    const url = encodeURIComponent(window.location.origin);
    const text = encodeURIComponent("¡Mira el nuevo diseño de mi habitación con RenderRoom AI! ✨ #InteriorDesign #AI");
    let shareUrl = "";
    
    switch(platform) {
        case 'twitter': shareUrl = `https://twitter.com/intent/tweet?text=${text}&url=${url}`; break;
        case 'facebook': shareUrl = `https://www.facebook.com/sharer/sharer.php?u=${url}`; break;
        case 'whatsapp': shareUrl = `https://api.whatsapp.com/send?text=${text}%20${url}`; break;
        case 'pinterest': shareUrl = `https://pinterest.com/pin/create/button/?url=${url}&description=${text}`; break;
    }
    
    if (shareUrl) window.open(shareUrl, '_blank', 'width=600,height=400');
}

function showResult(data, userPrompt) {
    state.lastRenderId = data.image_id;
    const errBoxOld = document.getElementById('gen-error-box');
    if (errBoxOld) errBoxOld.remove();

    const imgSrc = `data:image/png;base64,${data.image_base64}`;
    document.getElementById('result-image').src = imgSrc;
    document.getElementById('download-btn').href = imgSrc;
    document.getElementById('result-panel').classList.remove('hidden');
    nextBtn.classList.add('hidden');
    backBtn.classList.add('hidden');
    
    // Smooth progress update
    let progress = 0;
    const interval = setInterval(() => {
        progress += Math.random() * 5;
        if (progress > 95) progress = 95;
        document.getElementById('render-progress').style.width = `${progress}%`;
    }, 1000);

    // Proposal panel
    const desc = state.roomData ? state.roomData.detailed_description_es : '';
    if (desc) {
        document.getElementById('prop-analysis').textContent = desc;
        document.getElementById('prop-analysis-wrap').classList.remove('hidden');
    } else {
        document.getElementById('prop-analysis-wrap').classList.add('hidden');
    }

    const styleName = state.selectedStyle || 'moderno';
    document.getElementById('prop-style-name').textContent = styleName;
    document.getElementById('prop-style-desc').textContent = data.style_description || '';

    // Build proposed changes list
    const changesList = document.getElementById('prop-changes');
    changesList.innerHTML = '';
    const changes = buildChangesList(state.selectedStyle, desc, userPrompt);
    changes.forEach(c => {
        const li = document.createElement('li');
        li.className = 'flex items-start gap-2';
        li.innerHTML = `<span class="material-symbols-outlined text-primary text-sm mt-0.5">arrow_forward</span><span>${c}</span>`;
        changesList.appendChild(li);
    });

    document.getElementById('prop-prompt').textContent = data.full_prompt || '';

    // Scroll to result
    setTimeout(() => document.getElementById('result-panel').scrollIntoView({ behavior: 'smooth' }), 200);
}

const STYLE_CHANGES = {
    moderno: ['Paleta de colores neutros: blanco, gris y beige','Muebles de l├¡neas rectas con patas de metal lacado','Iluminaci├│n empotrada + l├ímparas de dise├▒o contempor├íneo','Eliminaci├│n del exceso de ornamentaci├│n','Materiales: hormig├│n pulido, vidrio, acero'],
    nordico: ['Tonos c├ílidos de madera natural en suelo y muebles','Textiles acogedores: cojines de lana, alfombra de pelo','Iluminaci├│n suave y difusa con bombillas c├ílidas','Plantas de interior como elemento decorativo clave','Paleta blanco-beige con toques de gris y madera clara'],
    industrial: ['Paredes de ladrillo visto o efecto hormig├│n','Tuber├¡as y vigas de metal a la vista','Iluminaci├│n con bombillas Edison y pantallas met├ílicas','Mobiliario robusto de madera oscura y metal','Paleta de grises, negros y tonos oxidados'],
    minimalista: ['Reducci├│n dr├ística de elementos decorativos','Un solo color dominante con acentos monocrom├íticos','Almacenaje oculto para mantener superficies despejadas','Muebles de formas simples y funcionales','Protagonismo del vac├¡o y la luz natural'],
    rustico: ['Vigas de madera en el techo','Suelo de piedra natural o tarima envejecida','Muebles artesanales o de madera maciza recuperada','Chimenea o estufa como elemento central','Textiles de lino, yute y lana en tonos terrosos'],
    bohemio: ['Capas de textiles coloridos: tapices, cojines, alfombras','Muebles vintage mezclados con piezas artesanales','Gran cantidad de plantas tropicales','Iluminaci├│n c├ílida con farolillos y guirnaldas','Paleta ecl├®ctica: ocre, terracota, verde esmeralda, ├¡ndigo'],
};

function buildChangesList(style, analysis, prompt) {
    const base = STYLE_CHANGES[style] || STYLE_CHANGES.moderno;
    const extras = [];
    if (analysis) {
        if (/poca luz|oscur/i.test(analysis)) extras.push('Incorporaci├│n de espejos para ampliar luminosidad');
        if (/peque├▒/i.test(analysis)) extras.push('Muebles multifuncionales para optimizar el espacio reducido');
        if (/desordenada|cluttered/i.test(analysis)) extras.push('Sistema de organizaci├│n y almacenaje integrado');
    }
    return [...base, ...extras].slice(0, 7);
}

// Remove redundant selectQuality at end of file

// Initialize
goToStep1();
