(function () {
    function addUnloadButton() {
        if (typeof opts !== 'undefined' && opts.misc_enable_unload_models === false) return true;

        const root = typeof gradioApp === 'function' ? gradioApp() : document;

        const links = Array.from(root.querySelectorAll('#footer a'));
        const reloadLink = links.find(a => a.textContent.trim() === 'Reload UI');
        if (!reloadLink) return false;

        if (root.getElementById('unload-models-link')) return true;

        const listLink = document.createElement('a');
        listLink.href = '#';
        listLink.id = 'list-models-link';
        listLink.textContent = 'List all models';
        listLink.addEventListener('click', function (e) {
            e.preventDefault();
            listLink.textContent = 'Listing\u2026';
            fetch('/unload-models/list', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success') {
                        listLink.textContent = 'Listed!';
                    } else {
                        console.error('[unload-models]', data.message);
                        listLink.textContent = 'Error';
                    }
                    setTimeout(() => { listLink.textContent = 'List all models'; }, 2000);
                })
                .catch(err => {
                    console.error('[unload-models]', err);
                    listLink.textContent = 'Error';
                    setTimeout(() => { listLink.textContent = 'List all models'; }, 2000);
                });
        });

        const link = document.createElement('a');
        link.href = '#';
        link.id = 'unload-models-link';
        link.textContent = 'Unload Models';
        link.addEventListener('click', function (e) {
            e.preventDefault();
            link.textContent = 'Unloading\u2026';
            fetch('/unload-models/unload', { method: 'POST' })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success') {
                        link.textContent = 'Unloaded!';
                    } else {
                        console.error('[unload-models]', data.message);
                        link.textContent = 'Error';
                    }
                    setTimeout(() => { link.textContent = 'Unload Models'; }, 2000);
                })
                .catch(err => {
                    console.error('[unload-models]', err);
                    link.textContent = 'Error';
                    setTimeout(() => { link.textContent = 'Unload Models'; }, 2000);
                });
        });

        reloadLink.after('\u2003\u2022\u2003', listLink, '\u2003\u2022\u2003', link);
        return true;
    }

    // Gradio renders dynamically; poll until the footer link is present.
    const interval = setInterval(function () {
        if (addUnloadButton()) {
            clearInterval(interval);
        }
    }, 500);

    // Safety cut-off after 60 seconds.
    setTimeout(function () { clearInterval(interval); }, 60000);
}());
