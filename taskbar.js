const container = document.querySelector(".table-container");
const highlight = document.querySelector("#table-highlight");
const cells = document.querySelectorAll(".table-container td");

cells.forEach(cell => {
    cell.addEventListener("mouseenter", () => {
        const cellRect = cell.getBoundingClientRect();
        const containerRect = container.getBoundingClientRect();

        highlight.style.left = `${cellRect.left - containerRect.left}px`;
        highlight.style.top = `${cellRect.top - containerRect.top}px`;
        highlight.style.width = `${cellRect.width}px`;
        highlight.style.height = `${cellRect.height}px`;
    });
});
