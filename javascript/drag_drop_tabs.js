(function () {
    let setupDone = false;

    function setupDragAndDropTabs() {
        if (typeof opts !== 'undefined' && opts.misc_enable_drag_drop_tabs === false) {
            setupDone = true;
            return true;
        }
        if (setupDone) return true;
        const root = typeof gradioApp === 'function' ? gradioApp() : document;

        const tabNav = root.querySelector('.tab-nav');
        if (!tabNav) return false;

        root.addEventListener('dragover', function (e) {
            let target = e.target;

            while (target && target !== root) {
                if (target.tagName === 'BUTTON' && target.parentElement && target.parentElement.classList.contains('tab-nav')) {
                    // Check if the dragged item contains files
                    if (e.dataTransfer && e.dataTransfer.types.includes('Files')) {
                        e.preventDefault();
                        // Click the tab if it's not already selected
                        if (!target.classList.contains('selected')) {
                            target.click();
                        }
                    }
                    break;
                }
                target = target.parentElement;
            }
        });

        setupDone = true;
        return true;
    }

    const interval = setInterval(function () {
        if (setupDragAndDropTabs()) {
            clearInterval(interval);
        }
    }, 500);

    setTimeout(function () { clearInterval(interval); }, 60000);
}());
