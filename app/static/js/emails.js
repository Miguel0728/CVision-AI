/* Envío (simulado) de los correos redactados por el agente.
   El agente solo crea borradores: el envío ocurre únicamente cuando el usuario pulsa el botón. */

function findEmailCard(emailId) {
    for (const message of history) {
        const card = (message.cards ?? []).find(c => c.kind === "email_draft" && c.data.id === emailId);
        if (card) return card;
    }
    return null;
}

/* Habilita o deshabilita los botones de envío (mientras el agente responde no se puede enviar). */
function syncEmailButtons() {
    document.querySelectorAll("[data-send-email]").forEach(button => {
        button.disabled = isBusy;
    });
}

async function requestSend(emailId) {
    const response = await fetch(`/api/emails/${encodeURIComponent(emailId)}/send`, { method: "POST" });
    const body = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(typeof body.detail === "string" ? body.detail : "No se pudo enviar el correo.");
    return body;
}

function showEmailError(button, message) {
    const hint = button.closest(".email-actions").querySelector(".email-hint");
    hint.textContent = message;
    hint.classList.add("error");
}

function announceSent(notice) {
    const text = notice.content;
    history.push({ role: "assistant", content: text, sig: notice.sig });
    addMessage("assistant", `<div class="answer"><p>${escapeHTML(text)}</p></div>`);
}

function applySent(button, card, sent) {
    card.data = { ...card.data, status: sent.status, sent_at: sent.sent_at };
    button.closest(".card").outerHTML = renderCard(card);
    announceSent(sent.notice);
    saveCurrentChat();
}

async function handleSendClick(button) {
    const card = findEmailCard(button.dataset.sendEmail);
    if (!card || isBusy) return;

    button.disabled = true;
    button.textContent = "Enviando…";
    try {
        applySent(button, card, await requestSend(card.data.id));
    } catch (error) {
        button.disabled = false;
        button.textContent = "Enviar correo";
        showEmailError(button, error.message);
    }
}

document.getElementById("messages").addEventListener("click", event => {
    const button = event.target.closest("[data-send-email]");
    if (button) handleSendClick(button);
});
