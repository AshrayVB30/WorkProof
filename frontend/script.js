document.addEventListener('DOMContentLoaded', () => {
    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.data-section');
    const contentBody = document.querySelector('.content-body');
    const scrapeBtn = document.getElementById('btn-scrape');
    const urlInput = document.getElementById('url-input');
    const accuracyVal = document.getElementById('accuracy-value');
    const errorCount = document.getElementById('error-count');

    // 1. Smooth Navigation
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);

            // Update active state
            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            // Scroll to section
            targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    // 2. Update Active Nav on Scroll
    contentBody.addEventListener('scroll', () => {
        let current = '';
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            if (contentBody.scrollTop >= sectionTop - 100) {
                current = section.getAttribute('id');
            }
        });

        navItems.forEach(item => {
            item.classList.remove('active');
            if (item.getAttribute('href').substring(1) === current) {
                item.classList.add('active');
            }
        });
    });

    // 3. Real Data Scraping Logic
    scrapeBtn.addEventListener('click', async () => {
        const url = urlInput.value.trim();
        if (!url) {
            alert('Please enter a valid URL');
            return;
        }

        // Clear previous data for a "fresh" feel
        const fieldValues = document.querySelectorAll('.field-value');
        fieldValues.forEach(div => {
            div.innerText = '';
            div.classList.add('empty');
        });

        const cards = document.querySelectorAll('.field-card');
        cards.forEach(c => c.classList.remove('match', 'mismatch'));

        accuracyVal.innerText = '0%';
        errorCount.innerText = '0';

        scrapeBtn.disabled = true;
        const isImageUrl = /\.(jpg|jpeg|png|webp|gif|bmp)$/i.test(url) || url.includes('img') || url.includes('image');
        scrapeBtn.innerHTML = isImageUrl ? '<span>👁️ Running OCR...</span>' : '<span>⚡ Scraping...</span>';

        try {
            const response = await fetch('/api/scrape', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ url })
            });

            const result = await response.json();

            if (result.status === 'success') {
                updateFields(result.data);
                calculateStats();

                // Update Link Counter badge
                if (result.metadata && result.metadata.unique_links !== undefined) {
                    updateLinkCounter(result.metadata.unique_links);
                }

                scrapeBtn.innerHTML = result.method === 'ocr' ? '👁️ OCR Done' : '✅ Done';
            } else {
                throw new Error(result.detail || 'Unknown error');
            }

            setTimeout(() => {
                scrapeBtn.disabled = false;
                scrapeBtn.innerHTML = '🌐 Get Data';
            }, 3000);

        } catch (error) {
            console.error('Scraping failed:', error);
            alert('Scraping failed: ' + error.message);
            scrapeBtn.innerHTML = '❌ Failed';
            setTimeout(() => {
                scrapeBtn.disabled = false;
                scrapeBtn.innerHTML = '🌐 Get Data';
            }, 2000);
        }
    });

    // Handle Enter Key in input - robust for all environments
    function triggerScrape(e) {
        if (e.key === 'Enter' || e.keyCode === 13) {
            e.preventDefault();
            e.stopPropagation();
            if (!scrapeBtn.disabled) {
                scrapeBtn.dispatchEvent(new MouseEvent('click', { bubbles: true, cancelable: true }));
            }
        }
    }
    urlInput.addEventListener('keydown', triggerScrape);
    urlInput.addEventListener('keypress', triggerScrape);


    function updateLinkCounter(count) {
        let badge = document.getElementById('link-counter');
        if (!badge) {
            badge = document.createElement('div');
            badge.id = 'link-counter';
            badge.className = 'stats-badge links';
            document.querySelector('.header-actions').prepend(badge);
        }
        badge.innerHTML = `🔗 Unique Links: <span>${count}</span>`;
    }

    function updateFields(data) {
        const fieldCards = document.querySelectorAll('.field-card');

        // Reset old styles
        fieldCards.forEach(c => c.classList.remove('match', 'mismatch'));

        fieldCards.forEach(card => {
            const fieldKey = card.getAttribute('data-field');
            const valueDiv = card.querySelector('.field-value');

            // Try to find a match in the scraped data
            // We use case-insensitive and partial matching for better results
            let foundValue = data[fieldKey];

            if (!foundValue) {
                // Try case-insensitive
                const lowerKey = fieldKey.toLowerCase();
                const matchedKey = Object.keys(data).find(k => k.toLowerCase() === lowerKey);
                if (matchedKey) foundValue = data[matchedKey];
            }

            if (foundValue) {
                valueDiv.innerText = foundValue;
                valueDiv.classList.remove('empty');

                // For now, assume it's a "match" if we found it on the page
                card.classList.add('match');
            }
        });
    }

    function calculateStats() {
        const total = document.querySelectorAll('.field-value:not(.empty)').length;
        const matches = document.querySelectorAll('.field-card.match').length;
        const errors = document.querySelectorAll('.field-card.mismatch').length;

        const accuracy = total > 0 ? Math.round((matches / total) * 100) : 0;

        // Dynamic stats animation
        animateValue(accuracyVal, 0, accuracy, 1000, '%');
        animateValue(errorCount, 0, errors, 1000);
    }

    function animateValue(obj, start, end, duration, suffix = '') {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            obj.innerHTML = Math.floor(progress * (end - start) + start) + suffix;
            if (progress < 1) {
                window.requestAnimationFrame(step);
            }
        };
        window.requestAnimationFrame(step);
    }

    // Editable content handling & Plain Text Paste
    document.querySelectorAll('.field-value').forEach(div => {
        // Prevent rich text pasting (removes background colors, fonts, etc.)
        div.addEventListener('paste', (e) => {
            e.preventDefault();
            const text = (e.originalEvent || e).clipboardData.getData('text/plain');
            document.execCommand('insertText', false, text);
        });

        div.addEventListener('blur', () => {
            if (div.innerText.trim() !== '') {
                div.classList.remove('empty');
            } else {
                div.classList.add('empty');
            }
            calculateStats();
        });
    });

    // Inject copy button into every field card
    document.querySelectorAll('.field-card').forEach(card => {
        const btn = document.createElement('button');
        btn.className = 'copy-btn';
        btn.title = 'Copy value';
        btn.innerHTML = '&#x2398;'; // ⎘ copy symbol
        card.appendChild(btn);
    });

    // Handle copy button clicks (delegated)
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.copy-btn');
        if (!btn) return;
        e.stopPropagation();

        const card = btn.closest('.field-card');
        const valueDiv = card.querySelector('.field-value');
        const text = valueDiv ? valueDiv.innerText.trim() : '';

        if (!text) return; // nothing to copy

        navigator.clipboard.writeText(text).then(() => {
            btn.innerHTML = '&#x2713;'; // ✓
            btn.classList.add('copied');
            setTimeout(() => {
                btn.innerHTML = '&#x2398;';
                btn.classList.remove('copied');
            }, 1500);
        }).catch(() => {
            // Fallback for older browsers / non-HTTPS
            const ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            document.execCommand('copy');
            document.body.removeChild(ta);
            btn.innerHTML = '&#x2713;';
            btn.classList.add('copied');
            setTimeout(() => {
                btn.innerHTML = '&#x2398;';
                btn.classList.remove('copied');
            }, 1500);
        });
    });
});
