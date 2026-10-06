/* Markdown mínimo y seguro: se escapa primero y luego se formatea.
   Soporta negritas, cursivas, encabezados, listas con una sublista y detalle indentado bajo un ítem. */

const TITLE_PATTERN = /^\s*\*\*[^*]+\*\*:?\s*$/;

const inlineMd = text => text
    .replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>")
    .replace(/(^|[\s(])_(.+?)_(?=[\s).,]|$)/g, "$1<em>$2</em>");

function classifyLine(line) {
    const heading = line.match(/^\s*#{1,6}\s*(.*)$/);
    if (heading) return { type: "heading", text: heading[1].trim() };

    const item = line.match(/^(\s*)[-*]\s+(.*)$/);
    if (item) return { type: "item", depth: item[1].length >= 2 ? 1 : 0, text: item[2].trimEnd() };

    if (!line.trim()) return { type: "blank" };
    if (/^\s{2,}\S/.test(line)) return { type: "indented", text: line.trim() };
    return { type: "text", text: line };
}

function addItem(items, token) {
    if (token.depth === 1 && items.length) items[items.length - 1].children.push(token.text);
    else items.push({ title: token.text, details: [], children: [] });
}

function itemHTML(item) {
    const details = item.details.map(d => `<span class="item-detail">${inlineMd(d)}</span>`).join("");
    const children = item.children.map(c => `<li>${inlineMd(c)}</li>`).join("");
    const sublist = children ? `<ul class="sub">${children}</ul>` : "";
    return `<li>${inlineMd(item.title)}${details}${sublist}</li>`;
}

function listHTML(items) {
    return `<ul>${items.map(itemHTML).join("")}</ul>`;
}

function paragraphHTML(text) {
    const cls = TITLE_PATTERN.test(text) ? ' class="section-title"' : "";
    return `<p${cls}>${inlineMd(text)}</p>`;
}

function headingHTML(text) {
    return `<p class="section-title"><strong>${inlineMd(text)}</strong></p>`;
}

function blockHTML(token) {
    if (token.type === "heading") return token.text ? headingHTML(token.text) : "";
    if (token.type === "blank") return "";
    return paragraphHTML(token.text);
}

/* Una línea en blanco no corta la lista si el siguiente bloque sigue siendo un ítem. */
function continuesList(tokens, index) {
    const next = tokens.slice(index + 1).find(token => token.type !== "blank");
    return next?.type === "item";
}

function renderMarkdown(text) {
    const tokens = escapeHTML(text).split("\n").map(classifyLine);
    const out = [];
    let items = null;

    const flushList = () => {
        if (items) out.push(listHTML(items));
        items = null;
    };

    tokens.forEach((token, index) => {
        if (token.type === "item") {
            items = items ?? [];
            addItem(items, token);
        } else if (items && token.type === "indented") {
            items[items.length - 1].details.push(token.text);
        } else if (!(items && token.type === "blank" && continuesList(tokens, index))) {
            flushList();
            out.push(blockHTML(token));
        }
    });

    flushList();
    return out.join("");
}
