(function () {
    var isProcessing = false;
    var enqueueButtons = [];

    if (typeof opts !== 'undefined' && opts.misc_enable_enqueue_prompt === false) return;

    function opt(name, def) {
        return (typeof opts !== 'undefined' && opts[name] !== undefined) ? opts[name] : def;
    }

    function orderFor(placement) {
        return placement === 'middle' ? ['interrupt', 'enqueue', 'skip'] :
               placement === 'right'  ? ['interrupt', 'skip', 'enqueue'] :
                                        ['enqueue', 'interrupt', 'skip'];
    }

    function updateAllButtons(count) {
        for (var i = 0; i < enqueueButtons.length; i++) {
            enqueueButtons[i].textContent = count > 0 ? 'Enqueue (' + count + ')' : 'Enqueue';
        }
    }

    function notifySDWebUI(message, type) {
        type = type || 'info';
        var app = typeof gradioApp === 'function' ? gradioApp() : document;
        var alertBox = app.querySelector('#js_alert_box input, #js_alert_box textarea');
        var alertBtn = app.querySelector('#js_alert_btn button, #js_alert_btn');
        if (alertBox && alertBtn) {
            alertBox.value = JSON.stringify({ message: message, level: type });
            alertBox.dispatchEvent(new Event('input', { bubbles: true }));
            alertBtn.click();
        } else {
            alert(message);
        }
    }

    function setInputValue(el, value) {
        var tag = el.tagName;
        if (tag === 'INPUT' && el.type === 'checkbox') {
            el.checked = value;
            el.dispatchEvent(new Event('change', { bubbles: true }));
        } else if (tag === 'TEXTAREA') {
            var proto = window.HTMLTextAreaElement.prototype;
            var setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
            setter.call(el, String(value));
            el.dispatchEvent(new Event('input', { bubbles: true }));
        } else if (tag === 'INPUT') {
            var proto = window.HTMLInputElement.prototype;
            var setter = Object.getOwnPropertyDescriptor(proto, 'value').set;
            setter.call(el, String(value));
            el.dispatchEvent(new Event('input', { bubbles: true }));
        } else if (tag === 'SELECT') {
            el.value = value;
            el.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    function getActiveTab() {
        var root = typeof gradioApp === 'function' ? gradioApp() : document;
        var tabs = root.querySelectorAll('#tabs > .tab-nav button');
        for (var i = 0; i < tabs.length; i++) {
            if (tabs[i].classList.contains('selected')) {
                var text = tabs[i].textContent.trim().toLowerCase();
                if (text.indexOf('img2img') !== -1) return 'img2img';
                if (text.indexOf('txt2img') !== -1) return 'txt2img';
            }
        }
        return 'txt2img';
    }

    function readSettings(tab) {
        var root = typeof gradioApp === 'function' ? gradioApp() : document;
        function getVal(id) {
            var el = root.getElementById(tab + '_' + id);
            if (!el) return null;
            if (el.tagName === 'INPUT' && (el.type === 'checkbox' || el.type === 'radio')) return el.checked;
            if (el.tagName === 'TEXTAREA' || el.tagName === 'INPUT' || el.tagName === 'SELECT') return el.value;
            return (el.textContent || '').trim();
        }
        return {
            tab:               tab,
            prompt:             getVal('prompt')             || '',
            negative_prompt:    getVal('neg_prompt')         || '',
            steps:              parseInt(getVal('steps'), 10)        || 20,
            cfg_scale:          parseFloat(getVal('cfg_scale'))      || 7.0,
            width:              parseInt(getVal('width'), 10)        || 512,
            height:             parseInt(getVal('height'), 10)       || 512,
            batch_size:         parseInt(getVal('batch_size'), 10)   || 1,
            n_iter:             parseInt(getVal('batch_count'), 10)  || 1,
            seed:               parseInt(getVal('seed'), 10)         || -1,
            sampler_name:       getVal('sampling')           || '',
            sampler_index:      getVal('sampling')           || '',
            restore_faces:      getVal('restore_faces')      || false,
            tiling:             getVal('tiling')             || false,
            denoising_strength: parseFloat(getVal('denoising_strength')) || 0.75,
        };
    }

    function populateUI(tab, settings) {
        var root = typeof gradioApp === 'function' ? gradioApp() : document;
        var fields = [
            'prompt', 'neg_prompt', 'steps', 'cfg_scale', 'width', 'height',
            'batch_size', 'batch_count', 'seed', 'sampling',
            'restore_faces', 'tiling', 'denoising_strength'
        ];
        for (var i = 0; i < fields.length; i++) {
            var id = fields[i];
            var el = root.getElementById(tab + '_' + id);
            if (!el) continue;
            var key = id === 'neg_prompt' ? 'negative_prompt' :
                     id === 'batch_count' ? 'n_iter' :
                     id === 'sampling' ? 'sampler_name' : id;
            var val = settings[key];
            if (val !== null && val !== undefined) {
                setInputValue(el, val);
            }
        }
    }

    function clickGenerate(tab) {
        var root = typeof gradioApp === 'function' ? gradioApp() : document;
        var btn = root.getElementById(tab + '_generate');
        if (btn) {
            btn.dispatchEvent(new Event('click', { bubbles: true }));
            return true;
        }
        return false;
    }

    function isGenerating() {
        var root = typeof gradioApp === 'function' ? gradioApp() : document;
        var tabs = ['txt2img', 'img2img'];
        for (var i = 0; i < tabs.length; i++) {
            var ib = root.getElementById(tabs[i] + '_interrupt');
            if (ib && window.getComputedStyle(ib).display !== 'none') return true;
            var ing = root.getElementById(tabs[i] + '_interrupting');
            if (ing && window.getComputedStyle(ing).display !== 'none') return true;
        }
        return false;
    }

    function processNextJob() {
        if (isProcessing) return;

        isProcessing = true;
        fetch('/enqueue-prompt/next', { method: 'POST' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.job) {
                    isProcessing = false;
                    updateAllButtons(data.queue_size || 0);
                    return;
                }
                var job = data.job;
                var tab = job.tab || getActiveTab();
                var params = job.params || job;
                delete params.tab;
                updateAllButtons(data.queue_size || 0);

                populateUI(tab, params);

                setTimeout(function () {
                    var switched = false;
                    if (getActiveTab() !== tab) {
                        var root = typeof gradioApp === 'function' ? gradioApp() : document;
                        var tabBtns = root.querySelectorAll('#tabs > .tab-nav button');
                        for (var i = 0; i < tabBtns.length; i++) {
                            var text = tabBtns[i].textContent.trim().toLowerCase();
                            if (text.indexOf(tab) !== -1) {
                                tabBtns[i].click();
                                switched = true;
                                break;
                            }
                        }
                    }
                    var delay = switched ? 800 : 300;
                    setTimeout(function () {
                        clickGenerate(tab);
                        setTimeout(function () { isProcessing = false; }, 500);
                    }, delay);
                }, 300);
            })
            .catch(function (err) {
                console.error('[enqueue-prompt]', err);
                isProcessing = false;
            });
    }

    function checkAndProcess() {
        if (!isGenerating()) {
            processNextJob();
        }
    }

    function setupEnqueueButton(tab) {
        var root = typeof gradioApp === 'function' ? gradioApp() : document;
        var box = root.getElementById(tab + '_generate_box');
        if (!box) return false;

        var btnId = tab + '_enqueue';
        if (root.getElementById(btnId)) return true;

        var interruptBtn = root.getElementById(tab + '_interrupt');
        var skipBtn = root.getElementById(tab + '_skip');
        var interruptingBtn = root.getElementById(tab + '_interrupting');
        if (!interruptBtn || !skipBtn) return false;

        var btn = document.createElement('button');
        btn.id = btnId;
        btn.className = 'lg secondary gradio-button svelte-cmf5ev';
        btn.title = 'Queue current prompt to run after the current generation finishes';
        btn.textContent = 'Enqueue';

        var p = opt('misc_enqueue_placement', 'left');
        var il = p === 'left' ? '0' : p === 'middle' ? '33.33%' : '66.66%';
        var ir = p === 'left' ? '0.5rem 0 0 0.5rem' :
                 p === 'right' ? '0 0.5rem 0.5rem 0' : '0';
        btn.style.cssText = 'position:absolute;left:' + il + ';width:33.33%;height:100%;background:#b4c0cc;border-radius:' + ir + ';display:none;transition:var(--button-transition);box-shadow:var(--button-shadow);';

        btn.addEventListener('click', function (e) {
            e.preventDefault();
            e.stopPropagation();
            var activeTab = getActiveTab();
            var settings = readSettings(activeTab);
            fetch('/enqueue-prompt/enqueue', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tab: activeTab, params: settings })
            })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.status === 'queued') {
                    btn.textContent = 'Queued!';
                    if (opt('misc_enqueue_notifications', true)) {
                        notifySDWebUI('Prompt queued.', 'info');
                    }
                    setTimeout(function () {
                        updateAllButtons(data.queue_size);
                    }, 1500);
                }
            })
            .catch(function (err) {
                console.error('[enqueue-prompt]', err);
            });
        });

        box.insertBefore(btn, interruptBtn);
        enqueueButtons.push(btn);

        function adjustLayout() {
            var interruptVisible = window.getComputedStyle(interruptBtn).display !== 'none';
            var interruptingVisible = interruptingBtn && window.getComputedStyle(interruptingBtn).display !== 'none';
            var skipVisible = window.getComputedStyle(skipBtn).display !== 'none';
            var isGen = interruptVisible || interruptingVisible;

            if (isGen) {
                btn.style.display = 'block';

                var actualInterrupt = interruptingVisible ? interruptingBtn : interruptBtn;
                var slotMap = {};
                slotMap.enqueue = btn;
                slotMap.interrupt = actualInterrupt;
                slotMap.skip = skipVisible ? skipBtn : null;

                var slots = orderFor(opt('misc_enqueue_placement', 'left')).slice();
                if (!skipVisible) {
                    slots = slots.filter(function (id) { return id !== 'skip'; });
                }
                var count = slots.length;

                var w = (100 / count).toFixed(2);
                for (var i = 0; i < slots.length; i++) {
                    var id = slots[i];
                    var el = slotMap[id];
                    if (!el) continue;
                    el.style.left = (i * parseFloat(w)).toFixed(2) + '%';
                    el.style.width = w + '%';
                    el.style.borderRadius = i === 0 ? '0.5rem 0 0 0.5rem' :
                                            i === slots.length - 1 ? '0 0.5rem 0.5rem 0' : '0';
                }
            } else {
                btn.style.display = 'none';
                interruptBtn.style.left = '';
                interruptBtn.style.width = '';
                interruptBtn.style.borderRadius = '';
                if (interruptingBtn) {
                    interruptingBtn.style.left = '';
                    interruptingBtn.style.width = '';
                    interruptingBtn.style.borderRadius = '';
                }
                skipBtn.style.left = '';
                skipBtn.style.width = '';
            }
        }

        adjustLayout();

        var observer = new MutationObserver(adjustLayout);
        observer.observe(interruptBtn, { attributes: true, attributeFilter: ['style', 'class'] });
        observer.observe(skipBtn, { attributes: true, attributeFilter: ['style', 'class'] });
        if (interruptingBtn) {
            observer.observe(interruptingBtn, { attributes: true, attributeFilter: ['style', 'class'] });
        }

        return true;
    }

    var interval = setInterval(function () {
        var txtReady = setupEnqueueButton('txt2img');
        var imgReady = setupEnqueueButton('img2img');
        if (txtReady && imgReady) {
            clearInterval(interval);
        }
    }, 500);

    setTimeout(function () { clearInterval(interval); }, 60000);

    setInterval(checkAndProcess, 1000);
})();
