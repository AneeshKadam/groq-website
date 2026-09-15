const tabs = document.querySelectorAll('.taskbar-object');
const slider = document.getElementById('slider');

function moveSliderTo(taskbar-object) {
    slider.style.left = taskbar-object.offsetLeft + 'px';
    slider.style.width = taskbar-object.offsetWidth + 'px';
}

tabs.forEach(taskbar-object => {
    taskbar-object.addEventListener('click', () => moveSliderTo(taskbar-object));
});

// Optional: put the slider under the first tab as soon as the page loads
window.addEventListener('load', () => moveSliderTo(tabs[0]));
