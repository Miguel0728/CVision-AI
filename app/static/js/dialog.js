/* Diálogo de confirmación propio, en lugar del confirm() del navegador.
   Uso: if (await confirmDialog({ title, message, detail, confirmLabel })) { ... } */

const CLOSE_DELAY_MS = 150;

const dialogEls = {
    dialog: document.getElementById("confirm-dialog"),
    title: document.getElementById("confirm-title"),
    message: document.getElementById("confirm-message"),
    detail: document.getElementById("confirm-detail"),
    confirm: document.getElementById("confirm-accept"),
    cancel: document.getElementById("confirm-cancel"),
};

let resolveDialog = null;

/* Cierra con una breve animación de salida y devuelve la respuesta a quien preguntó. */
function closeDialog(accepted) {
    if (!resolveDialog) return;
    const resolve = resolveDialog;
    resolveDialog = null;
    dialogEls.dialog.classList.add("closing");
    setTimeout(() => {
        dialogEls.dialog.close();
        dialogEls.dialog.classList.remove("closing");
        resolve(accepted);
    }, CLOSE_DELAY_MS);
}

function fillDialog({ title, message, detail = "", confirmLabel = "Confirmar" }) {
    dialogEls.title.textContent = title;
    dialogEls.message.textContent = message;
    dialogEls.detail.textContent = detail;
    dialogEls.detail.hidden = !detail;
    dialogEls.confirm.textContent = confirmLabel;
}

function confirmDialog(options) {
    fillDialog(options);
    dialogEls.dialog.showModal();
    dialogEls.cancel.focus();
    return new Promise(resolve => {
        resolveDialog = resolve;
    });
}

function initDialog() {
    dialogEls.confirm.addEventListener("click", () => closeDialog(true));
    dialogEls.cancel.addEventListener("click", () => closeDialog(false));
    dialogEls.dialog.addEventListener("cancel", event => {
        event.preventDefault();
        closeDialog(false);
    });
    dialogEls.dialog.addEventListener("click", event => {
        if (event.target === dialogEls.dialog) closeDialog(false);
    });
}

initDialog();
