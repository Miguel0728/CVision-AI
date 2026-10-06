/* Tarjetas visuales para los resultados de las herramientas del agente.
   Para añadir una: crea su función *CardHTML y regístrala en CARD_RENDERERS. */

const svgIcon = path =>
    `<svg viewBox="0 0 24 24" width="14" height="14" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${path}</svg>`;

const ICONS = {
    ok: svgIcon('<path d="M5 12l5 5L20 7"/>'),
    near: svgIcon('<path d="M12 7v6M12 17h.01"/>'),
    fail: svgIcon('<path d="M6 6l12 12M18 6L6 18"/>'),
};

const LEVELS = {
    cumple: { label: "Cumple", icon: ICONS.ok, state: "ok" },
    parcial: { label: "Cumple parcialmente", icon: ICONS.near, state: "near" },
    no_cumple: { label: "No cumple", icon: ICONS.fail, state: "fail" },
};

function checkState(check) {
    if (check.ok) return "ok";
    return check.near ? "near" : "fail";
}

/* A quien no cumple solo se le muestran los requisitos fallados, para no saturar. */
function visibleChecks(level, checks) {
    return level === "no_cumple" ? checks.filter(check => !check.ok) : checks;
}

function checkChipHTML(check) {
    const state = checkState(check);
    return `<li class="check ${state}">${ICONS[state]}<span><b>${escapeHTML(check.label)}:</b> ${escapeHTML(check.detail)}</span></li>`;
}

function niceToHaveHTML(nice) {
    const total = nice.matched.length + nice.missing.length;
    if (!nice.matched.length) return "";
    return `<p class="nice">Deseables (${nice.matched.length}/${total}): ${escapeHTML(nice.matched.join(", "))}</p>`;
}

function candidateHTML(result, index) {
    const checks = visibleChecks(result.level, result.checks).map(checkChipHTML).join("");
    return `
        <li class="candidate" style="--i: ${index}">
            <p class="candidate-name"><strong>${escapeHTML(result.name)}</strong> <span>${escapeHTML(result.position)}</span></p>
            <ul class="checks">${checks}</ul>
            ${niceToHaveHTML(result.nice)}
        </li>`;
}

function levelHeadingHTML(level, count) {
    const { label, icon, state } = LEVELS[level];
    return `<span class="level-title ${state}">${icon}${label}<em>${count}</em></span>`;
}

function levelGroupHTML(level, results) {
    if (!results.length) return "";
    const list = `<ul class="candidates">${results.map(candidateHTML).join("")}</ul>`;
    const heading = levelHeadingHTML(level, results.length);
    if (level === "no_cumple") {
        return `<details class="level-group"><summary>${heading}</summary>${list}</details>`;
    }
    return `<section class="level-group">${heading}${list}</section>`;
}

function requirementsHTML(requirements) {
    return `<ul class="requirements">${requirements.map(r => `<li>${escapeHTML(r)}</li>`).join("")}</ul>`;
}

function jobMatchCardHTML({ job, results }) {
    const byLevel = level => results.filter(result => result.level === level);
    const groups = Object.keys(LEVELS).map(level => levelGroupHTML(level, byLevel(level))).join("");
    return `
        <article class="card" aria-label="Clasificación de candidatos para ${escapeHTML(job.title)}">
            <header class="card-head">
                <p class="card-eyebrow">Vacante</p>
                <h3>${escapeHTML(job.title)}</h3>
                ${requirementsHTML(job.requirements)}
            </header>
            ${groups}
        </article>`;
}

function jobRowHTML(job) {
    const prompt = `¿Quién califica para la vacante de ${job.title}?`;
    return `
        <li class="job-row">
            <div class="job-info">
                <p class="job-title"><strong>${escapeHTML(job.title)}</strong> <span>${escapeHTML(job.department)}</span></p>
                ${requirementsHTML(job.requirements)}
            </div>
            <button type="button" class="btn-soft" data-prompt="${escapeHTML(prompt)}">Ver candidatos</button>
        </li>`;
}

function jobsListCardHTML(jobs) {
    return `
        <article class="card" aria-label="Vacantes abiertas">
            <header class="card-head">
                <p class="card-eyebrow">Vacantes abiertas</p>
                <h3>${jobs.length} puestos disponibles</h3>
            </header>
            <ul class="jobs">${jobs.map(jobRowHTML).join("")}</ul>
        </article>`;
}

function formatSentAt(iso) {
    return new Date(iso).toLocaleString("es", { dateStyle: "medium", timeStyle: "short" });
}

function emailMetaHTML(label, value) {
    return `<div class="email-row"><dt>${label}</dt><dd>${escapeHTML(value)}</dd></div>`;
}

function emailFooterHTML(data) {
    if (data.status === "sent") {
        return `<p class="email-status">${ICONS.ok}Enviado el ${escapeHTML(formatSentAt(data.sent_at))} (simulado)</p>`;
    }
    return `
        <div class="email-actions">
            <button type="button" class="btn-primary" data-send-email="${escapeHTML(data.id)}">Enviar correo</button>
            <p class="email-hint">Simulación: no se envía ningún correo real.</p>
        </div>`;
}

function emailDraftCardHTML(data) {
    const eyebrow = data.status === "sent" ? "Correo enviado" : "Borrador de correo";
    return `
        <article class="card" aria-label="${eyebrow} para ${escapeHTML(data.to.name)}">
            <header class="card-head">
                <p class="card-eyebrow">${eyebrow}</p>
                <h3>${escapeHTML(data.job_title)}</h3>
            </header>
            <dl class="email-meta">
                ${emailMetaHTML("Para", `${data.to.name} <${data.to.email}>`)}
                ${emailMetaHTML("Asunto", data.subject)}
            </dl>
            <div class="email-body">${escapeHTML(data.body)}</div>
            ${emailFooterHTML(data)}
        </article>`;
}

const CARD_RENDERERS = {
    job_match: jobMatchCardHTML,
    jobs_list: jobsListCardHTML,
    email_draft: emailDraftCardHTML,
};

function renderCard({ kind, data }) {
    const renderer = CARD_RENDERERS[kind];
    return renderer ? renderer(data) : "";
}

function renderCards(cards = []) {
    return cards.map(renderCard).join("");
}
