// upload-wizard.js

let currentStep = 1;
let selectedStyle = null;
let selectedQuality = 'normal';
let uploadedImageUrl = null;
let analysisData = null;

// Initialize when page loads
document.addEventListener('DOMContentLoaded', () => {
    initAuth();
    setupDropzone();
    updateStepper();
});

function setupDropzone() {
    const dropzone = document.getElementById('dropzone');
    const fileInput = document.getElementById('file-input');
    const selectBtn = document.getElementById('select-btn');

    if (!dropzone || !fileInput) return;

    selectBtn.onclick = () => fileInput.click();

    dropzone.ondragover = (e) => {
        e.preventDefault();
        dropzone.classList.add('border-primary');
    };

    dropzone.ondragleave = () => {
        dropzone.classList.remove('border-primary');
    };

    dropzone.ondrop = (e) => {
        e.preventDefault();
        dropzone.classList.remove('border-primary');
        const file = e.dataTransfer.files[0];
        if (file) handleFile(file);
    };

    fileInput.onchange = (e) => {
        const file = e.target.files[0];
        if (file) handleFile(file);
    };
}

async function handleFile(file) {
    if (!file.type.startsWith('image/')) {
        alert('Por favor selecciona una imagen válida.');
        return;
    }

    // Preview
    const reader = new FileReader();
    reader.onload = (e) => {
        const preview = document.getElementById('image-preview');
        const content = document.getElementById('dropzone-content');
        preview.src = e.target.result;
        preview.classList.remove('hidden');
        content.classList.add('opacity-0');
        
        // Update summary preview too
        document.getElementById('summary-preview').src = e.target.result;
    };
    reader.readAsDataURL(file);

    // Show loading analysis
    const analysisPanel = document.getElementById('analysis-panel');
    const loading = document.getElementById('analysis-loading');
    const result = document.getElementById('analysis-result');
    
    analysisPanel.classList.remove('hidden');
    loading.classList.remove('hidden');
    result.classList.add('hidden');

    try {
        // Mock analysis for now (in a real app, send to Vertex/Gemini Vision)
        await new Promise(r => setTimeout(r, 2000));
        
        analysisData = {
            roomType: "Sala de Estar",
            architecture: "Moderna con techos altos",
            elements: ["Sofá gris", "Mesa de centro madera", "Alfombra beige"],
            recommendations: {
                add: ["Lámpara de pie arco", "Plantas altas", "Cojines de acento"],
                remove: ["Alfombra antigua", "Revistero desordenado"]
            },
            score: 85,
            issues: []
        };

        showAnalysis(analysisData);
        
        // Enable next button
        const nextBtn = document.getElementById('next-btn');
        nextBtn.disabled = false;
        nextBtn.classList.remove('bg-primary/10', 'text-primary/50', 'cursor-not-allowed');
        nextBtn.classList.add('bg-primary', 'text-white', 'hover:scale-105', 'shadow-xl');

    } catch (err) {
        console.error("Error analizando imagen:", err);
        alert("Error al analizar la imagen. Por favor intenta de nuevo.");
    }
}

function showAnalysis(data) {
    const loading = document.getElementById('analysis-loading');
    const result = document.getElementById('analysis-result');
    const text = document.getElementById('analysis-text');
    const score = document.getElementById('validation-score');
    const badge = document.getElementById('validation-badge');
    const label = document.getElementById('validation-label');
    const icon = document.getElementById('validation-icon');
    
    loading.classList.add('hidden');
    result.classList.remove('hidden');
    
    text.innerHTML = `<strong>Detección:</strong> ${data.roomType}. <br><strong>Arquitectura:</strong> ${data.architecture}. <br><strong>Elementos clave:</strong> ${data.elements.join(', ')}.`;
    
    score.innerText = `${data.score}%`;
    document.getElementById('image-validation-panel').classList.remove('hidden');
    
    if (data.score > 70) {
        badge.className = "px-4 py-2 rounded-xl text-xs font-black flex items-center gap-2 bg-green-500/10 text-green-600";
        label.innerText = "Imagen Óptima";
        icon.innerText = "check_circle";
    } else {
        badge.className = "px-4 py-2 rounded-xl text-xs font-black flex items-center gap-2 bg-orange-500/10 text-orange-500";
        label.innerText = "Baja Calidad";
        icon.innerText = "warning";
    }
}

function selectStyle(card) {
    // UI selection
    document.querySelectorAll('.style-card').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    
    selectedStyle = card.getAttribute('data-style');
    document.getElementById('summary-style').innerText = selectedStyle;
    
    // Show AI suggestions based on style
    showSuggestions(selectedStyle);
    
    // Check if we can proceed
    checkStep2Complete();
}

function showSuggestions(style) {
    const section = document.getElementById('recommendations-section');
    const styleName = document.getElementById('rec-style-name');
    const addList = document.getElementById('rec-add-list');
    const removeList = document.getElementById('rec-remove-list');
    
    section.classList.remove('hidden');
    styleName.innerText = style.charAt(0).toUpperCase() + style.slice(1);
    
    addList.innerHTML = analysisData.recommendations.add.map(item => `
        <label class="flex items-center gap-3 p-3 bg-white border border-border rounded-xl cursor-pointer hover:border-primary/30 transition-all">
            <input type="checkbox" checked class="rounded-md text-primary focus:ring-primary/20 border-border">
            <span class="text-sm font-bold text-text-secondary">${item}</span>
        </label>
    `).join('');

    removeList.innerHTML = analysisData.recommendations.remove.map(item => `
        <label class="flex items-center gap-3 p-3 bg-white border border-border rounded-xl cursor-pointer hover:border-primary/30 transition-all">
            <input type="checkbox" checked class="rounded-md text-orange-500 focus:ring-orange-500/20 border-border">
            <span class="text-sm font-bold text-text-secondary">${item}</span>
        </label>
    `).join('');
}

function checkStep2Complete() {
    const nextBtn = document.getElementById('next-btn');
    if (selectedStyle) {
        nextBtn.disabled = false;
        nextBtn.classList.remove('opacity-60', 'cursor-not-allowed');
    }
}

function selectQuality(q) {
    selectedQuality = q;
    document.querySelectorAll('.quality-card').forEach(c => {
        c.classList.toggle('selected', c.getAttribute('data-quality') === q);
    });
    
    const cost = q === 'high' ? 2 : 1;
    document.getElementById('final-cost-label').innerText = `${cost} Crédito${cost > 1 ? 's' : ''}`;
}

function updateStepper() {
    const steps = [1, 2, 3];
    steps.forEach(s => {
        const el = document.querySelector(`.lg\\:flex .flex:nth-child(${s * 2 - 1}) .rounded-full`);
        const label = document.querySelector(`.lg\\:flex .flex:nth-child(${s * 2 - 1})`);
        
        if (s < currentStep) {
            el.className = "size-8 rounded-full flex items-center justify-center text-xs font-black step-done";
            el.innerHTML = '<span class="material-symbols-outlined text-sm">check</span>';
            label.classList.remove('opacity-40');
        } else if (s === currentStep) {
            el.className = "size-8 rounded-full flex items-center justify-center text-xs font-black step-active";
            el.innerText = s;
            label.classList.remove('opacity-40');
        } else {
            el.className = "size-8 rounded-full flex items-center justify-center text-xs font-black step-inactive";
            el.innerText = s;
            label.classList.add('opacity-40');
        }
    });

    // Sections
    document.getElementById('section-upload').classList.toggle('hidden', currentStep !== 1);
    document.getElementById('section-style').classList.toggle('hidden', currentStep !== 2);
    document.getElementById('section-generate').classList.toggle('hidden', currentStep !== 3);
    document.getElementById('result-panel').classList.add('hidden');
    
    // Back button
    document.getElementById('back-btn').style.display = currentStep === 1 ? 'none' : 'flex';
    
    // Next Button Label
    const nextBtn = document.getElementById('next-btn');
    if (currentStep === 3) {
        nextBtn.classList.add('hidden'); // We use "Generate" button in the section
    } else {
        nextBtn.classList.remove('hidden');
        nextBtn.innerHTML = `Continuar <span class="material-symbols-outlined group-hover:translate-x-1 transition-transform">arrow_forward</span>`;
    }
}

function nextStep() {
    if (currentStep < 3) {
        currentStep++;
        updateStepper();
        
        // Disable next button until interaction
        if (currentStep === 2 && !selectedStyle) {
            document.getElementById('next-btn').disabled = true;
        }
    }
}

function prevStep() {
    if (currentStep > 1) {
        currentStep--;
        updateStepper();
        document.getElementById('next-btn').disabled = false; // Usually can go back and confirm
    }
}

async function generateRender() {
    const btn = document.getElementById('btn-generate');
    const progress = document.getElementById('gen-progress');
    const progressBar = document.getElementById('gen-progress-bar');
    const statusText = document.getElementById('gen-status-text');
    
    btn.disabled = true;
    btn.classList.add('opacity-50', 'pointer-events-none');
    progress.classList.remove('hidden');
    
    // Simulation
    let p = 0;
    const interval = setInterval(() => {
        p += 2;
        progressBar.style.width = `${p}%`;
        
        if (p < 30) statusText.innerText = "Iniciando Servidores Vertex AI...";
        else if (p < 60) statusText.innerText = "Generando Máscaras de Segmentación...";
        else if (p < 90) statusText.innerText = "Aplicando Estilo " + selectedStyle + "...";
        else statusText.innerText = "Renderizando Escena final...";
        
        if (p >= 100) {
            clearInterval(interval);
            showResult();
        }
    }, 600);
}

function showResult() {
    currentStep = 4; // Result state
    document.getElementById('section-generate').classList.add('hidden');
    document.getElementById('result-panel').classList.remove('hidden');
    document.getElementById('next-btn').classList.add('hidden');
    document.getElementById('back-btn').classList.add('hidden');
    
    // Set results
    document.getElementById('result-image').src = document.getElementById('image-preview').src; // Just for demo
    document.getElementById('prop-analysis').innerText = `Nuestro sistema ha detectado una ${analysisData.roomType} con una tipología ${analysisData.architecture}. \n\nSe han respetado los volúmenes estructurales principales mientras se reimaginaba el mobiliario y la iluminación.`;
    document.getElementById('prop-style-desc').innerText = `Se ha aplicado una paleta de colores y materiales acorde al estilo ${selectedStyle.toUpperCase()}, priorizando la armonía visual y la funcionalidad del espacio.`;
    
    const changesList = document.getElementById('prop-changes');
    const allChanges = [...analysisData.recommendations.add, ...analysisData.recommendations.remove];
    changesList.innerHTML = allChanges.map(change => `
        <li class="flex items-center gap-3 p-3 bg-white rounded-xl border border-border shadow-sm">
            <span class="material-symbols-outlined text-primary text-sm">check</span>
            <span class="text-xs font-bold text-text-secondary">${change}</span>
        </li>
    `).join('');

    // Smooth scroll to top
    window.scrollTo({ top: 0, behavior: 'smooth' });
}
