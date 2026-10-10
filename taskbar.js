(() => {
  const nav = document.querySelector("#taskbar-nav");
  const highlight = document.querySelector("#table-highlight");
  const cells = nav ? nav.querySelectorAll("#taskbar-table td") : [];

  if (!nav || !highlight || !cells.length) return;

  function moveHighlight(cell) {
    const navRect = nav.getBoundingClientRect();
    const cellRect = cell.getBoundingClientRect();

    highlight.style.left = `${cellRect.left - navRect.left}px`;
    highlight.style.top = `${cellRect.top - navRect.top}px`;
    highlight.style.width = `${cellRect.width}px`;
    highlight.style.height = `${cellRect.height}px`;
    highlight.style.opacity = "1";
  }

  cells.forEach((cell) => {
    cell.addEventListener("mouseenter", () => moveHighlight(cell));
    cell.addEventListener("focusin", () => moveHighlight(cell));
  });

  nav.addEventListener("mouseleave", () => {
    highlight.style.opacity = "0";
  });

  window.addEventListener("resize", () => {
    const focused = nav.querySelector("a:focus");
    if (focused) moveHighlight(focused.closest("td"));
  });
})();