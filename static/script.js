document.addEventListener('DOMContentLoaded', function() {
    // Get DOM elements
    const uploadForm = document.getElementById('uploadForm');
    const fileInput = document.getElementById('fileInput');
    const uploadBtn = document.querySelector('.upload-btn');
    const loading = document.getElementById('loading');
    const resultsSection = document.getElementById('resultsSection');
    const fileDropArea = document.querySelector('.file-drop-area');
    const chatInput = document.getElementById('chatInput');
    const sendMessage = document.getElementById('sendMessage');
    const chatMessages = document.getElementById('chatMessages');

    // File Upload Handling
    fileInput.addEventListener('change', function() {
        uploadBtn.disabled = !this.files.length;
        if (this.files.length) {
            const fileName = this.files[0].name;
            document.querySelector('.file-label span').textContent = fileName;
        }
    });

    // Drag and Drop
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, preventDefaults, false);
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    ['dragenter', 'dragover'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, highlight, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        fileDropArea.addEventListener(eventName, unhighlight, false);
    });

    function highlight() {
        fileDropArea.classList.add('highlight');
    }

    function unhighlight() {
        fileDropArea.classList.remove('highlight');
    }

    fileDropArea.addEventListener('drop', handleDrop, false);

    function handleDrop(e) {
        const dt = e.dataTransfer;
        const files = dt.files;
        fileInput.files = files;
        uploadBtn.disabled = !files.length;
        if (files.length) {
            document.querySelector('.file-label span').textContent = files[0].name;
        }
    }

    // Form Submission
    uploadForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        
        const formData = new FormData();
        formData.append('file', fileInput.files[0]);
        
        loading.classList.remove('hidden');
        uploadBtn.disabled = true;
        
        try {
            const response = await fetch('/upload', {
                method: 'POST',
                body: formData
            });
            
            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }
            
            displayResults(data);
            resultsSection.classList.remove('hidden');
            
        } catch (error) {
            alert('Error: ' + error.message);
        } finally {
            loading.classList.add('hidden');
            uploadBtn.disabled = false;
        }
    });

    // Tab Switching
    const tabBtns = document.querySelectorAll('.tab-btn');
    const tabPanes = document.querySelectorAll('.tab-pane');

    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabId = btn.getAttribute('data-tab');
            
            tabBtns.forEach(b => b.classList.remove('active'));
            tabPanes.forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            document.getElementById(tabId).classList.add('active');
        });
    });

    // Display Results
    function displayResults(data) {
        displayPatientInfo(data.patient_info);
        displayLabInfo(data.lab_info);
        displayTestResults(data.lab_results);
        displayPlots(data.lab_results);
    }

    function displayPatientInfo(info) {
        const container = document.getElementById('patientInfo');
        container.innerHTML = Object.entries(info)
            .map(([key, value]) => `
                <div class="info-item">
                    <strong>${formatKey(key)}:</strong>
                    <span>${value}</span>
                </div>
            `).join('');
    }

    function displayLabInfo(info) {
        const container = document.getElementById('labInfo');
        container.innerHTML = Object.entries(info)
            .map(([key, value]) => `
                <div class="info-item">
                    <strong>${formatKey(key)}:</strong>
                    <span>${value}</span>
                </div>
            `).join('');
    }

    function displayTestResults(results) {
        const container = document.getElementById('testResults');
        container.innerHTML = `
            <table class="results-table">
                <thead>
                    <tr>
                        <th>Parameter</th>
                        <th>Value</th>
                        <th>Unit</th>
                        <th>Reference Range</th>
                        <th>Status</th>
                    </tr>
                </thead>
                <tbody>
                    ${Object.entries(results).map(([param, data]) => `
                        <tr class="${data.status.toLowerCase()}">
                            <td>${param}</td>
                            <td>${data.value}</td>
                            <td>${data.unit}</td>
                            <td>${data.reference_range}</td>
                            <td>${data.status}</td>
                        </tr>
                    `).join('')}
                </tbody>
            </table>
        `;
    }

    function displayPlots(results) {
        const container = document.getElementById('plotsGrid');
        container.innerHTML = '';
        
        Object.keys(results).forEach(param => {
            if (results[param].status !== 'Normal') {
                const plotDiv = document.createElement('div');
                plotDiv.className = 'plot-item';
                
                const img = document.createElement('img');
                const paramFileName = param.replace(/[^a-zA-Z0-9]/g, '_');
                img.src = `/static/plots/${paramFileName}.png`;
                img.alt = `${param} Plot`;
                img.onerror = () => {
                    console.error(`Failed to load plot for ${param}`);
                    plotDiv.remove();
                };
                
                plotDiv.appendChild(img);
                container.appendChild(plotDiv);
            }
        });
    }

    // Chat Functionality
    sendMessage.addEventListener('click', handleChatMessage);
    chatInput.addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            handleChatMessage();
        }
    });

    async function handleChatMessage() {
        const message = chatInput.value.trim();
        if (!message) return;

        const role = document.getElementById('userRole').value;
        
        addMessage(message, 'user');
        chatInput.value = '';

        try {
            const response = await fetch('/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message, role }),
            });

            const data = await response.json();
            
            if (data.error) {
                throw new Error(data.error);
            }

            addMessage(data.response, 'bot');
            
        } catch (error) {
            addMessage('Sorry, there was an error processing your message.', 'bot');
            console.error('Chat error:', error);
        }
    }

    function addMessage(message, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${sender}-message`;
        messageDiv.textContent = message;
        chatMessages.appendChild(messageDiv);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    // Helper Functions
    function formatKey(key) {
        return key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
    }
});