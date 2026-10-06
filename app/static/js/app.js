const STORAGE_KEY = "cvision.chats";
const SIDEBAR_KEY = "cvision.sidebar";
const MOBILE_QUERY = window.matchMedia("(max-width: 860px)");

const history = [];
let isBusy = false;
let currentChatId = null;

const els = {
    messages: document.getElementById("messages"),
    welcome: document.getElementById("welcome"),
    form: document.getElementById("composer"),
    prompt: document.getElementById("prompt"),
    send: document.getElementById("btn-send"),
    newChat: document.getElementById("btn-new-chat"),
    scrim: document.getElementById("scrim"),
    openSidebar: document.getElementById("btn-sidebar-open"),
    closeSidebar: document.getElementById("btn-sidebar-close"),
    historyList: document.getElementById("history-list"),
    historyEmpty: document.getElementById("history-empty"),
};
const WELCOME_HTML = els.welcome.outerHTML;

function scrollToBottom() {
    window.scrollTo({ top: document.body.scrollHeight });
}

function addMessage(role, html) {
    els.welcome?.remove();
    els.welcome = null;

    const row = document.createElement("div");
    row.className = `message ${role}`;
    row.innerHTML = `<div class="bubble">${html}</div>`;
    els.messages.appendChild(row);
    scrollToBottom();
    return row;
}

const STEP_ICONS = {
    running: '<span class="spinner" aria-hidden="true"></span>',
    done: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M5 12l5 5L20 7"/></svg>',
    error: '<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg>',
};
const STEP_STATUS_TEXT = { running: "en curso", done: "completado", error: "con error" };

function upsertStep(box, { id, label, status }) {
    const list = box.querySelector(".steps-inner");
    box.hidden = false;
    box.classList.remove("collapsed");
    let step = [...list.children].find(el => el.dataset.id === id);
    if (!step) {
        step = document.createElement("div");
        step.dataset.id = id;
        list.appendChild(step);
    }
    step.className = `step ${status}`;
    step.innerHTML = `${STEP_ICONS[status]}<span>${escapeHTML(label)}</span><span class="sr-only">${STEP_STATUS_TEXT[status]}</span>`;
    scrollToBottom();
}

/* Al terminar, los pasos se pliegan en un resumen que se puede reabrir. */
function collapseSteps(box) {
    if (!box || box.hidden || box.querySelector(".steps-toggle")) return;
    const total = box.querySelectorAll(".step").length;
    const toggle = document.createElement("button");
    toggle.type = "button";
    toggle.className = "steps-toggle";
    toggle.setAttribute("aria-expanded", "false");
    toggle.textContent = `${total} ${total === 1 ? "paso" : "pasos"}`;
    toggle.addEventListener("click", () => {
        const collapsed = box.classList.toggle("collapsed");
        toggle.setAttribute("aria-expanded", String(!collapsed));
    });
    box.prepend(toggle);
    box.classList.add("collapsed");
}

function dismissWelcome() {
    const welcome = els.welcome;
    if (!welcome) return Promise.resolve();
    els.welcome = null;
    welcome.classList.add("leaving");
    return new Promise(resolve => setTimeout(() => {
        welcome.remove();
        resolve();
    }, 180));
}

function setBusy(busy) {
    isBusy = busy;
    els.send.disabled = busy;
    els.newChat.disabled = busy;
    syncEmailButtons();
    els.form.setAttribute("aria-busy", String(busy));
}

const ASSISTANT_TEMPLATE = `
    <div class="steps" hidden><div class="steps-list"><div class="steps-inner"></div></div></div>
    <div class="cards"></div>
    <div class="answer"><span class="typing" aria-label="Escribiendo"><i></i><i></i><i></i></span></div>`;

function createAssistantMessage() {
    const row = addMessage("assistant", ASSISTANT_TEMPLATE);
    return {
        steps: row.querySelector(".steps"),
        cards: row.querySelector(".cards"),
        answer: row.querySelector(".answer"),
        text: "",
        sig: null,
        cardsData: [],
        failed: false,
    };
}

function showError(box, message) {
    box.innerHTML = `<p class="error-message" role="alert">${escapeHTML(message)}</p>`;
}

async function requestChat() {
    const messages = history.map(({ role, content, sig }) => ({ role, content, ...(sig ? { sig } : {}) }));
    const response = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages }),
    });
    if (response.ok && response.body) return response;

    const body = await response.json().catch(() => ({}));
    const error = new Error(`HTTP ${response.status}`);
    if (response.status === 429 && typeof body.detail === "string") error.userMessage = body.detail;
    throw error;
}

async function readEvents(response, onEvent) {
    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";
    while (true) {
        const { value, done } = await reader.read();
        if (done) return;
        buffer += decoder.decode(value, { stream: true });
        const frames = buffer.split("\n\n");
        buffer = frames.pop();
        frames.filter(frame => frame.startsWith("data: ")).forEach(frame => onEvent(JSON.parse(frame.slice(6))));
    }
}

function addCard(turn, event) {
    turn.cardsData.push(event);
    turn.cards.insertAdjacentHTML("beforeend", renderCard(event));
    syncEmailButtons();
    scrollToBottom();
}

function appendToken(turn, text) {
    turn.text += text;
    turn.answer.innerHTML = renderMarkdown(turn.text);
    scrollToBottom();
}

function handleChatEvent(turn, event) {
    if (event.type === "step") upsertStep(turn.steps, event);
    else if (event.type === "card") addCard(turn, event);
    else if (event.type === "token") appendToken(turn, event.text);
    else if (event.type === "done") turn.sig = event.sig;
    else if (event.type === "error") {
        turn.failed = true;
        showError(turn.answer, event.message);
    }
}

function finishTurn(turn) {
    if (turn.failed || !turn.text) {
        history.pop();
        if (!turn.failed) showError(turn.answer, "El modelo no devolvió respuesta.");
        return;
    }
    history.push({ role: "assistant", content: turn.text, sig: turn.sig, cards: turn.cardsData });
    saveCurrentChat();
}

async function sendMessage(text) {
    const content = text.trim();
    if (!content || isBusy) return;

    setBusy(true);
    hideDiscovery();
    els.prompt.value = "";
    autoGrow();
    await dismissWelcome();

    history.push({ role: "user", content });
    addMessage("user", `<p>${escapeHTML(content)}</p>`);
    const turn = createAssistantMessage();

    try {
        await readEvents(await requestChat(), event => handleChatEvent(turn, event));
        finishTurn(turn);
    } catch (error) {
        console.error("Error en el chat:", error);
        history.pop();
        showError(turn.answer, error.userMessage || "No se pudo obtener respuesta. Inténtalo de nuevo.");
    } finally {
        collapseSteps(turn.steps);
        refreshUsage();
        setBusy(false);
        scrollToBottom();
        els.prompt.focus();
    }
}

function autoGrow() {
    els.prompt.style.height = "auto";
    els.prompt.style.height = `${Math.min(els.prompt.scrollHeight, 180)}px`;
}

/* ---------- Historial de conversaciones (localStorage) ---------- */

function readChats() {
    try {
        const data = JSON.parse(localStorage.getItem(STORAGE_KEY) || "[]");
        return Array.isArray(data) ? data : [];
    } catch {
        return [];
    }
}

function writeChats(chats) {
    try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(chats.slice(0, 50)));
    } catch {
        /* sin almacenamiento: el chat sigue funcionando, solo no se guarda */
    }
}

function saveCurrentChat() {
    if (!history.length) return;
    const chats = readChats();
    if (!currentChatId) {
        currentChatId = `c${Date.now()}`;
    }
    const title = history[0].content.trim().slice(0, 60);
    const entry = { id: currentChatId, title, messages: [...history], updated: Date.now() };
    const rest = chats.filter(c => c.id !== currentChatId);
    writeChats([entry, ...rest]);
    renderHistory();
}

function createHistoryItem(chat, index) {
    const li = document.createElement("li");
    li.className = "history-item enter";
    li.dataset.id = chat.id;
    li.style.setProperty("--i", index);
    li.innerHTML = `
        <div class="history-row">
            <button type="button" class="history-open" data-id="${escapeHTML(chat.id)}" title="${escapeHTML(chat.title)}">${escapeHTML(chat.title)}</button>
            <button type="button" class="icon-btn history-delete" data-delete="${escapeHTML(chat.id)}" aria-label="Eliminar conversación: ${escapeHTML(chat.title)}">
                <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3"/></svg>
            </button>
        </div>`;
    li.addEventListener("animationend", () => li.classList.remove("enter"), { once: true });
    return li;
}

function removeHistoryItem(li) {
    li.classList.add("leaving");
    li.addEventListener("transitionend", event => {
        if (event.target === li) li.remove();
    });
    setTimeout(() => li.remove(), 400);
}

/* Actualiza la lista en sitio: solo los items nuevos se animan y el foco se conserva. */
function renderHistory() {
    const chats = readChats();
    els.historyEmpty.hidden = chats.length > 0;

    const existing = new Map(
        [...els.historyList.children]
            .filter(li => !li.classList.contains("leaving"))
            .map(li => [li.dataset.id, li])
    );

    chats.forEach((chat, index) => {
        const li = existing.get(chat.id) ?? createHistoryItem(chat, index);
        const active = chat.id === currentChatId;
        li.classList.toggle("active", active);
        li.querySelector(".history-open").toggleAttribute("aria-current", active);
        if (els.historyList.children[index] !== li) {
            els.historyList.insertBefore(li, els.historyList.children[index] ?? null);
        }
    });

    existing.forEach((li, id) => {
        if (!chats.some(chat => chat.id === id)) removeHistoryItem(li);
    });
}

function startNewChat() {
    if (isBusy) return;
    history.length = 0;
    currentChatId = null;
    els.messages.innerHTML = WELCOME_HTML;
    els.welcome = document.getElementById("welcome");
    renderHistory();
    if (MOBILE_QUERY.matches) setSidebar(false);
    els.prompt.focus();
}

function renderSavedMessage(message) {
    if (message.role === "user") {
        addMessage("user", `<p>${escapeHTML(message.content)}</p>`);
        return;
    }
    const cards = `<div class="cards">${renderCards(message.cards)}</div>`;
    addMessage("assistant", `${cards}<div class="answer">${renderMarkdown(message.content)}</div>`);
}

function openChat(id) {
    if (isBusy) return;
    const chat = readChats().find(c => c.id === id);
    if (!chat) return;

    history.length = 0;
    history.push(...chat.messages);
    currentChatId = chat.id;
    els.messages.innerHTML = "";
    els.welcome = null;
    chat.messages.forEach(renderSavedMessage);
    renderHistory();
    if (MOBILE_QUERY.matches) setSidebar(false);
    window.scrollTo({ top: document.body.scrollHeight });
}

async function deleteChat(id) {
    if (isBusy) return;
    const chat = readChats().find(c => c.id === id);
    if (!chat) return;

    const accepted = await confirmDialog({
        title: "¿Eliminar conversación?",
        message: "Se borrará de tu historial y no se podrá recuperar.",
        detail: chat.title,
        confirmLabel: "Eliminar",
    });
    if (!accepted) return;

    writeChats(readChats().filter(c => c.id !== id));
    if (id === currentChatId) startNewChat();
    else renderHistory();
}

/* ---------- Sidebar ---------- */

function setSidebar(open) {
    document.body.dataset.sidebar = open ? "open" : "closed";
    els.openSidebar.setAttribute("aria-expanded", String(open));
    if (!MOBILE_QUERY.matches) {
        try { localStorage.setItem(SIDEBAR_KEY, open ? "open" : "closed"); } catch { /* opcional */ }
    }
}

function initSidebar() {
    let saved = null;
    try { saved = localStorage.getItem(SIDEBAR_KEY); } catch { /* opcional */ }
    setSidebar(MOBILE_QUERY.matches ? false : saved !== "closed");
}

els.openSidebar.addEventListener("click", () => setSidebar(true));
els.closeSidebar.addEventListener("click", () => {
    setSidebar(false);
    els.openSidebar.focus();
});
els.scrim.addEventListener("click", () => setSidebar(false));
document.addEventListener("keydown", event => {
    if (event.key === "Escape" && MOBILE_QUERY.matches && document.body.dataset.sidebar === "open") {
        setSidebar(false);
    }
});
MOBILE_QUERY.addEventListener("change", initSidebar);

els.historyList.addEventListener("click", event => {
    const del = event.target.closest("[data-delete]");
    if (del) return deleteChat(del.dataset.delete);
    const open = event.target.closest("[data-id]");
    if (open) openChat(open.dataset.id);
});

els.form.addEventListener("submit", event => {
    event.preventDefault();
    sendMessage(els.prompt.value);
});

els.prompt.addEventListener("keydown", event => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        sendMessage(els.prompt.value);
    }
});

els.prompt.addEventListener("input", autoGrow);
els.newChat.addEventListener("click", startNewChat);
els.messages.addEventListener("click", event => {
    const capability = event.target.closest("[data-prompt]");
    if (capability) sendMessage(capability.dataset.prompt);
});

initSidebar();
renderHistory();
setTimeout(() => document.body.classList.remove("no-anim"), 80);
els.prompt.focus();
