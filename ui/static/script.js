const fileDropArea = document.getElementById('fileDropArea');
const fileInput = document.getElementById('referencePdfs');
const fileMsg = document.querySelector('.file-msg');

let currentSpec = null;

let selectedFiles = [];

function updateFileMsg() {
    if (selectedFiles.length === 0) {
        fileMsg.innerHTML = "Drag & Drop PDFs or Click to Browse<br><small>(You can click again to add more files!)</small>";
    } else {
        let fileListHtml = selectedFiles.map((f, index) => 
            `<div class="file-item">
                <span>${f.name}</span>
                <span class="remove-file" data-index="${index}" title="Remove file">❌</span>
            </div>`
        ).join('');
        fileMsg.innerHTML = `<strong>${selectedFiles.length} files added:</strong><div class="file-list">${fileListHtml}</div><small>(Click box to add more)</small>`;
        
        // Add event listeners to remove buttons
        document.querySelectorAll('.remove-file').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                e.stopPropagation(); 
                const index = parseInt(e.target.getAttribute('data-index'));
                selectedFiles.splice(index, 1);
                updateFileMsg();
            });
        });
    }
}

// File Drag & Drop UI
fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        for (let i = 0; i < fileInput.files.length; i++) {
            selectedFiles.push(fileInput.files[i]);
        }
        updateFileMsg();
        // Reset the input so the same files can be selected again if needed
        fileInput.value = ""; 
    }
});

fileDropArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileDropArea.classList.add('is-active');
});

fileDropArea.addEventListener('dragleave', () => {
    fileDropArea.classList.remove('is-active');
});

fileDropArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileDropArea.classList.remove('is-active');
    if (e.dataTransfer.files.length > 0) {
        for (let i = 0; i < e.dataTransfer.files.length; i++) {
            selectedFiles.push(e.dataTransfer.files[i]);
        }
        updateFileMsg();
    }
});

// Form Submission (Generate)
const form = document.getElementById('generateForm');
const generateBtn = document.getElementById('generateBtn');
const btnText = document.querySelector('.btn-text');
const spinner = document.querySelector('.spinner');
const errorBox = document.getElementById('errorBox');

const emptyState = document.getElementById('emptyState');
const previewContainer = document.getElementById('previewContainer');
const previewContent = document.getElementById('previewContent');
const docTypeTag = document.getElementById('docTypeTag');
const paperTag = document.getElementById('paperTag');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // UI Loading state
    btnText.textContent = "Analyzing & Generating...";
    spinner.classList.remove('hidden');
    generateBtn.disabled = true;
    errorBox.classList.add('hidden');
    
    const formData = new FormData();
    formData.append('instruction', document.getElementById('instruction').value);
    
    const ragTopic = document.getElementById('ragTopic').value;
    if (ragTopic) formData.append('rag_topic', ragTopic);
    
    if (selectedFiles.length > 0) {
        for (let i = 0; i < selectedFiles.length; i++) {
            formData.append('reference_pdfs', selectedFiles[i]);
        }
    }

    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.error || "Failed to generate document spec");
        }
        
        currentSpec = data;
        renderPreview(data);
        
        // Show preview
        emptyState.classList.add('hidden');
        previewContainer.classList.remove('hidden');
        
    } catch (err) {
        errorBox.textContent = err.message;
        errorBox.classList.remove('hidden');
    } finally {
        // Reset UI state
        btnText.textContent = "Generate Layout";
        spinner.classList.add('hidden');
        generateBtn.disabled = false;
    }
});

function renderPreview(spec) {
    docTypeTag.textContent = spec.document_type || "Document";
    paperTag.textContent = spec.page?.size || "A4";
    
    let html = `
        <div style="font-family: '${spec.theme?.body?.font_family}', sans-serif; font-size: ${spec.theme?.body?.size_pt}pt;">
    `;
    
    spec.sections.forEach(section => {
        html += `<div class="preview-section">`;
        if (section.title) {
            html += `<h2>${section.title}</h2>`;
        }
        
        section.elements.forEach(el => {
            if (el.element_type === 'text') {
                let textHtml = `<div style="text-align: ${el.alignment || 'left'}">${el.content}</div>`;
                if (el.is_heading) {
                    textHtml = `<h${el.heading_level} style="text-align: ${el.alignment || 'left'}">${el.content}</h${el.heading_level}>`;
                }
                html += `<div class="preview-element">${textHtml}</div>`;
            } else if (el.element_type === 'list') {
                let listTag = el.list_type === 'bullet' ? 'ul' : 'ol';
                let listStyle = '';
                if (el.list_type === 'lettered') {
                    listStyle = 'type="A"';
                }
                html += `
                <div class="preview-element">
                    <${listTag} ${listStyle} style="margin-left: 20px;">
                        ${el.items.map(item => `<li>${item.content}</li>`).join('')}
                    </${listTag}>
                </div>`;
            } else if (el.element_type === 'spacer') {
                let linesHtml = "";
                for(let i=0; i<el.space_lines; i++) {
                    linesHtml += `<div style="border-bottom: 1px solid #eee; height: 30px; margin-top: 10px;"></div>`;
                }
                html += `<div class="preview-element">${linesHtml}</div>`;
            } else if (el.element_type === 'table') {
                html += `
                <div class="preview-element">
                    <table style="width: 100%; border-collapse: collapse; ${el.has_borders ? 'border: 1px solid #ddd;' : ''}">
                        <tbody>
                            ${el.rows.map(row => `
                                <tr>
                                    ${row.map(cell => `
                                        <td style="${el.has_borders ? 'border: 1px solid #ddd;' : ''} padding: 8px; ${cell.is_header ? 'font-weight: bold; background-color: #f5f5f5;' : ''}">
                                            ${cell.content}
                                        </td>
                                    `).join('')}
                                </tr>
                            `).join('')}
                        </tbody>
                    </table>
                </div>`;
            }
        });
        
        html += `</div>`;
    });
    
    html += `</div>`;
    previewContent.innerHTML = html;
}

// Render to DOCX
const renderBtn = document.getElementById('renderBtn');
renderBtn.addEventListener('click', async () => {
    if (!currentSpec) return;
    
    const originalText = renderBtn.textContent;
    renderBtn.textContent = "Rendering...";
    renderBtn.disabled = true;
    
    try {
        const response = await fetch('/api/render', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ spec: currentSpec })
        });
        
        if (!response.ok) {
            const data = await response.json();
            throw new Error(data.error || "Failed to render DOCX");
        }
        
        // Trigger file download
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'DocTree_Generated.docx';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        
    } catch (err) {
        alert("Render Error: " + err.message);
    } finally {
        renderBtn.textContent = originalText;
        renderBtn.disabled = false;
    }
});
