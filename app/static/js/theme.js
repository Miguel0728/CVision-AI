/* Tema claro / oscuro / sistema. Se carga en el <head> para aplicarse antes del primer pintado. */

const THEME_KEY = "cvision.theme";
const THEMES = ["light", "dark", "system"];

function getStoredTheme() {
    try {
        const stored = localStorage.getItem(THEME_KEY);
        return THEMES.includes(stored) ? stored : "system";
    } catch {
        return "system";
    }
}

function applyTheme(theme) {
    const root = document.documentElement;
    if (theme === "system") delete root.dataset.theme;
    else root.dataset.theme = theme;
}

/* Suaviza el cambio de color durante un instante, sin dejar transiciones permanentes. */
function animateThemeChange() {
    const root = document.documentElement;
    root.classList.add("theme-anim");
    setTimeout(() => root.classList.remove("theme-anim"), 300);
}

function setTheme(theme) {
    animateThemeChange();
    applyTheme(theme);
    try {
        localStorage.setItem(THEME_KEY, theme);
    } catch {
        /* sin almacenamiento: el tema solo dura esta sesión */
    }
}

applyTheme(getStoredTheme());
