const chatContainer = document.getElementById('chatContainer');
const questionInput = document.getElementById('questionInput');
const sendBtn = document.getElementById('sendBtn');
const chatForm = document.getElementById('chatForm');

// API base URL — resolved by nginx proxy to backend container
const API_BASE = '/api';

const CATEGORY_META = {
    1: { label: 'Legal',    css: 'legal',      icon: '\u2696\uFE0F' },
    2: { label: 'Contable', css: 'accounting',  icon: '\uD83D\uDCCA' },
    3: { label: 'Medico',   css: 'medical',     icon: '\uD83E\uDE7A' },
    4: { label: 'General',  css: 'generic',     icon: '\uD83D\uDCA1' },
};

let firstMessage = true;
let sessionId = localStorage.getItem('qa_session_id') || null;

// Auto-resize textarea
questionInput.addEventListener('input', () => {
    questionInput.style.height = 'auto';
    questionInput.style.height = Math.min(questionInput.scrollHeight, 120) + 'px';
});

// Enter to send, Shift+Enter for newline
questionInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        chatForm.requestSubmit();
    }
});

function useExample(btn) {
    questionInput.value = btn.textContent;
    questionInput.focus();
    questionInput.dispatchEvent(new Event('input'));
}

function scrollToBottom() {
    chatContainer.scrollTop = chatContainer.scrollHeight;
}

function clearWelcome() {
    if (firstMessage) {
        const welcome = chatContainer.querySelector('.welcome-message');
        if (welcome) welcome.remove();
        firstMessage = false;
    }
}

function addUserMessage(text) {
    clearWelcome();
    const row = document.createElement('div');
    row.className = 'message-row user';
    row.innerHTML = `<div class="message-bubble">${escapeHtml(text)}</div>`;
    chatContainer.appendChild(row);
    scrollToBottom();
}

function addTypingIndicator() {
    const row = document.createElement('div');
    row.className = 'message-row agent';
    row.id = 'typingRow';
    row.innerHTML = `
        <div class="agent-avatar">\u2699\uFE0F</div>
        <div class="message-bubble">
            <div class="typing-indicator">
                <span></span><span></span><span></span>
            </div>
        </div>
    `;
    chatContainer.appendChild(row);
    scrollToBottom();
}

function removeTypingIndicator() {
    const el = document.getElementById('typingRow');
    if (el) el.remove();
}

function addAgentMessage(data) {
    removeTypingIndicator();

    const meta = CATEGORY_META[data.category_id] || CATEGORY_META[4];

    const row = document.createElement('div');
    row.className = 'message-row agent';
    row.innerHTML = `
        <div class="agent-avatar">${meta.icon}</div>
        <div class="message-bubble">
            <div class="agent-label ${meta.css}">Agente ${meta.label}</div>
            <div>${formatText(data.answer)}</div>
        </div>
    `;
    chatContainer.appendChild(row);
    scrollToBottom();
}

function addErrorMessage(msg) {
    removeTypingIndicator();

    const row = document.createElement('div');
    row.className = 'message-row agent';
    row.innerHTML = `
        <div class="agent-avatar">\u26A0\uFE0F</div>
        <div class="message-bubble" style="border-color: var(--medical);">
            <div style="color: var(--medical); font-weight: 600; margin-bottom: 4px;">Error</div>
            <div>${escapeHtml(msg)}</div>
        </div>
    `;
    chatContainer.appendChild(row);
    scrollToBottom();
}

async function sendMessage(e) {
    e.preventDefault();
    const text = questionInput.value.trim();
    if (!text) return;

    questionInput.value = '';
    questionInput.style.height = 'auto';
    sendBtn.disabled = true;

    addUserMessage(text);
    addTypingIndicator();

    try {
        const payload = { question: text };
        if (sessionId) payload.session_id = sessionId;

        const res = await fetch(`${API_BASE}/qa`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({ detail: 'Error del servidor' }));
            throw new Error(err.detail || `HTTP ${res.status}`);
        }

        const data = await res.json();

        // Guardar session_id para siguientes mensajes
        sessionId = data.session_id;
        localStorage.setItem('qa_session_id', sessionId);

        addAgentMessage(data);
    } catch (err) {
        addErrorMessage(err.message || 'No se pudo conectar con el servidor.');
    } finally {
        sendBtn.disabled = false;
        questionInput.focus();
    }
}

function newConversation() {
    sessionId = null;
    localStorage.removeItem('qa_session_id');
    firstMessage = true;
    chatContainer.innerHTML = `
        <div class="welcome-message">
            <div class="welcome-icon">&#129302;</div>
            <h2>Bienvenido al Sistema Multiagente</h2>
            <p>Haz una pregunta y el sistema la clasificara automaticamente para dirigirla al agente especializado correcto.</p>
            <div class="example-questions">
                <p class="examples-title">Ejemplos de preguntas:</p>
                <button class="example-btn" onclick="useExample(this)">Que es un amparo en Mexico?</button>
                <button class="example-btn" onclick="useExample(this)">Como se calcula el ISR para personas fisicas?</button>
                <button class="example-btn" onclick="useExample(this)">Cuales son los sintomas de la diabetes tipo 2?</button>
                <button class="example-btn" onclick="useExample(this)">Que es la inteligencia artificial?</button>
            </div>
        </div>
    `;
}

async function loadHistory() {
    if (!sessionId) return;
    try {
        const res = await fetch(`${API_BASE}/history/${sessionId}`);
        if (!res.ok) return;
        const messages = await res.json();
        if (messages.length === 0) return;

        clearWelcome();
        for (const msg of messages) {
            if (msg.role === 'user') {
                addUserMessage(msg.content);
            } else {
                const labelMap = { 'Legal': 1, 'Contable': 2, 'Médica': 3, 'Genérica': 4 };
                const catId = labelMap[msg.category_label] || 4;
                addAgentMessage({
                    category_id: catId,
                    answer: msg.content,
                });
            }
        }
    } catch {
        // Si falla la carga de historial, no bloquear la app
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatText(text) {
    let html = escapeHtml(text);
    // Bold **text**
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Newlines
    html = html.replace(/\n/g, '<br>');
    return html;
}

// Al cargar, restaurar historial si hay sesion previa
loadHistory();
