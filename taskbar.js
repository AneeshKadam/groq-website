const highlight = document.querySelector(".table-highlight");
const cells = document.querySelectorAll("td");

cells.forEach(cell => {
  cell.addEventListener("mouseenter", () => {
    highlight.style.left = `${cell.offsetLeft + 4}px`;
    highlight.style.width = `${cell.offsetWidth}px`;
  });
});
