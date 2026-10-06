/* Tarjeta flotante "Cómo funciona": aparece al entrar, se recuerda al cerrarla y se reabre desde la configuración. */

const DISCOVERY_KEY = "cvision.discovery.v2"; // v2: la tarjeta flotante sustituye a la guía anterior
const LEGACY_DISCOVERY_KEY = "cvision.discovery";
const DISCOVERY_EXIT_MS = 180;
const DISCOVERY_PROMPT = "¿Quién califica para la vacante de Ingeniero DevOps?";

const discoveryCard = document.getElementById("discovery");

function isDiscoveryHidden() {
    try {
        return localStorage.getItem(DISCOVERY_KEY) === "hidden";
    } catch {
        return false;
    }
}

function setDiscoveryHidden(hidden) {
    if (hidden) document.documentElement.dataset.discovery = "hidden";
    else delete document.documentElement.dataset.discovery;
    discoveryCard.classList.remove("leaving");
    try {
        localStorage.setItem(DISCOVERY_KEY, hidden ? "hidden" : "visible");
    } catch {
        /* sin almacenamiento: la guía solo se oculta durante esta sesión */
    }
}

function hideDiscovery() {
    if (document.documentElement.dataset.discovery === "hidden") return;
    discoveryCard.classList.add("leaving");
    setTimeout(() => setDiscoveryHidden(true), DISCOVERY_EXIT_MS);
}

function openDiscovery() {
    setDiscoveryHidden(false);
    setSettingsOpen(false);
}

function tryDiscoveryExample() {
    hideDiscovery();
    sendMessage(DISCOVERY_PROMPT);
}

function initDiscovery() {
    try {
        localStorage.removeItem(LEGACY_DISCOVERY_KEY);
    } catch {
        /* sin almacenamiento */
    }
    if (isDiscoveryHidden()) document.documentElement.dataset.discovery = "hidden";

    discoveryCard.addEventListener("animationend", () => discoveryCard.classList.remove("intro"), { once: true });
    discoveryCard.querySelector("[data-discovery-close]").addEventListener("click", hideDiscovery);
    discoveryCard.querySelector("[data-discovery-try]").addEventListener("click", tryDiscoveryExample);
    document.querySelector("[data-discovery-open]").addEventListener("click", openDiscovery);
}

initDiscovery();
