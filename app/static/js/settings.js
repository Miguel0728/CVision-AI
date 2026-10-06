/* Tarjeta de usuario del sidebar: panel de configuración con tema y uso de la demostración. */

const settingsEls = {
    button: document.getElementById("btn-settings"),
    panel: document.getElementById("settings-panel"),
    wrap: document.querySelector(".user-wrap"),
    themeButtons: document.querySelectorAll("[data-theme-option]"),
};

const numberFormat = new Intl.NumberFormat("es");

function isSettingsOpen() {
    return settingsEls.panel.dataset.open === "true";
}

function setSettingsOpen(open) {
    settingsEls.panel.dataset.open = String(open);
    settingsEls.button.setAttribute("aria-expanded", String(open));
    if (open) refreshUsage();
}

function markActiveTheme() {
    const current = getStoredTheme();
    settingsEls.themeButtons.forEach(button => {
        button.setAttribute("aria-checked", String(button.dataset.themeOption === current));
    });
}

function chooseTheme(theme) {
    setTheme(theme);
    markActiveTheme();
}

/* Un medidor: texto, barra proporcional y estado (alto / lleno) según el consumo. */
function renderMeter(name, used, total, text) {
    const meter = document.querySelector(`[data-meter="${name}"]`);
    const ratio = total > 0 ? Math.min(used / total, 1) : 0;
    meter.querySelector(".meter-value").textContent = text;
    meter.querySelector(".meter-fill").style.transform = `scaleX(${ratio})`;
    meter.classList.toggle("high", ratio >= 0.8 && ratio < 1);
    meter.classList.toggle("full", ratio >= 1);
}

function renderUsage(usage) {
    const left = Math.max(usage.requests_limit - usage.requests_used, 0);
    const percent = Math.round((usage.tokens_used / usage.tokens_budget) * 100);
    renderMeter("requests", usage.requests_used, usage.requests_limit, `${left} libres`);
    document.getElementById("usage-requests-caption").textContent = `Límite: ${usage.requests_limit} preguntas por hora`;
    renderMeter("budget", usage.tokens_used, usage.tokens_budget, `${percent} % usado`);
    document.getElementById("usage-tokens").textContent =
        `${numberFormat.format(usage.tokens_used)} de ${numberFormat.format(usage.tokens_budget)} tokens hoy`;
}

async function refreshUsage() {
    try {
        const response = await fetch("/api/usage");
        if (response.ok) renderUsage(await response.json());
    } catch {
        /* el panel conserva los últimos valores si no hay conexión */
    }
}

function closeOnOutsideClick(event) {
    if (isSettingsOpen() && !settingsEls.wrap.contains(event.target)) setSettingsOpen(false);
}

function closeOnEscape(event) {
    if (event.key === "Escape" && isSettingsOpen()) {
        setSettingsOpen(false);
        settingsEls.button.focus();
    }
}

function initSettings() {
    markActiveTheme();
    refreshUsage();
    settingsEls.button.addEventListener("click", () => setSettingsOpen(!isSettingsOpen()));
    settingsEls.themeButtons.forEach(button =>
        button.addEventListener("click", () => chooseTheme(button.dataset.themeOption))
    );
    document.addEventListener("click", closeOnOutsideClick);
    document.addEventListener("keydown", closeOnEscape);
}

initSettings();
