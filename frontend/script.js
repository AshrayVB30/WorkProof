document.addEventListener('DOMContentLoaded', () => {

    const navItems = document.querySelectorAll('.nav-item');
    const sections = document.querySelectorAll('.data-section');
    const contentBody = document.querySelector('.content-body');
    const scrapeBtn = document.getElementById('btn-scrape');
    const urlInput = document.getElementById('url-input');
    const fileInput = document.getElementById('file-input');
    const accuracyVal = document.getElementById('accuracy-value');
    const errorCount = document.getElementById('error-count');

    initCopyButtons();

    // ---------------- Navigation ----------------
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = item.getAttribute('href').substring(1);
            const targetSection = document.getElementById(targetId);

            navItems.forEach(nav => nav.classList.remove('active'));
            item.classList.add('active');

            targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

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

    // ---------------- SCRAPE BUTTON ----------------
    scrapeBtn.addEventListener('click', async () => {

        const url = urlInput.value.trim();
        const selectedFile = fileInput && fileInput.files ? fileInput.files[0] : null;
        if (!url && !selectedFile) {
            alert('Enter a URL or choose an image file');
            return;
        }

        resetUI();

        scrapeBtn.disabled = true;
        scrapeBtn.innerHTML = '👁️ Running OCR...';

        try {

            let response;
            if (selectedFile) {
                const formData = new FormData();
                formData.append('file', selectedFile);
                response = await fetch('/api/scrape-upload', {
                    method: 'POST',
                    body: formData
                });
            } else {
                response = await fetch('/api/scrape', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url })
                });
            }

            const result = await response.json();

            if (result.status !== 'success') {
                throw new Error(result.detail || 'Unknown error');
            }

            updateFields(result.data);
            calculateStats();

            scrapeBtn.innerHTML = '✅ Done';

        } catch (err) {
            console.error(err);
            alert('Scraping failed: ' + err.message);
            scrapeBtn.innerHTML = '❌ Failed';
        }

        setTimeout(() => {
            scrapeBtn.disabled = false;
            scrapeBtn.innerHTML = '🌐 Get Data';
        }, 2500);

    });

    // ---------------- RESET UI ----------------
    function resetUI() {
        document.querySelectorAll('.field-value').forEach(div => {
            div.innerText = '';
            div.classList.add('empty');
        });

        document.querySelectorAll('.field-card')
            .forEach(c => c.classList.remove('match', 'mismatch'));

        accuracyVal.innerText = '0%';
        errorCount.innerText = '0';
    }

    // ---------------- FLATTEN OBJECT (FIXED) ----------------
    function flattenObject(obj, result = {}) {

        const advisorMap = {
            account_advisor: "Account Advisor - ",
            assets_manager: "Assets Manager - ",
            investment_advisor: "Investment Advisor - ",
            insurance_manager: "Insurance Manager - "
        };

        for (let key in obj) {

            let value = obj[key];

            // Handle Legal Advisor Sections
            if (advisorMap[key] && typeof value === 'object') {

                const prefix = advisorMap[key];

                for (let subKey in value) {

                    let label = '';

                    if (subKey === "advisor_id")
                        label = "Advisor ID";
                    else if (subKey === "manager_id")
                        label = "Manager ID";
                    else if (subKey === "name")
                        label = "Name";
                    else if (subKey === "contact")
                        label = "Contact";
                    else if (subKey === "address")
                        label = "Address";
                    else
                        label = subKey;

                    result[prefix + label] = value[subKey];
                }

                continue;
            }

            // Normal Fields Mapping
            const labelMap = {
                full_name: "Full Name",
                gender: "Gender",
                dob: "DOB",
                ssn: "SSN",
                address_1: "Address 1",
                address_2: "Address 2",
                city: "City",
                state: "State",
                postal: "Postal",
                country: "Country",
                email: "Email",
                contact: "Contact",
                customer_id: "Customer ID",
                a_c_type: "Account Type",
                a_c_name: "Account Name",
                a_c_number: "Account Number",
                account_type: "Account Type",
                account_name: "Account Name",
                account_number: "Account Number",
                iban: "IBAN",
                bic: "BIC",
                btc_address: "BTC Address",
                eth_address: "ETH Address",
                ltc_address: "LTC Address",
                cc_no: "CC No",
                last_txn_amount: "Last Txn Amount",
                last_txn_date: "Last Txn Date",
                company: "Company",
                bs: "BS",
                ein: "EIN",
                skill_description: "Skill Description",
                isin: "ISIN",
                coupon: "Coupon",
                invested_amount: "Invested Amount",
                maturity_date: "Maturity Date",
                bond_name: "Bond Name",
                bond_class: "Bond Class",
                department: "Department",
                ean13: "Ean13",
                product_name: "Product Name",
                unit_price: "Unit Price",
                user: "User",
                purchase_token: "Purchase Token",
                buying_ipv4: "Buying IPv4",
                buying_ipv6: "Buying IPv6",
                type: "Type",
                model: "Model",
                manufacture: "Manufacturer",
                manufacturer: "Manufacturer",
                vin: "VIN",
                beneficiary_identifier_id: "Beneficiary Identifier ID",
                ins_no: "INS No",

                // Flat advisor keys from backend
                account_advisor___advisor_id: "Account Advisor - Advisor ID",
                account_advisor___name: "Account Advisor - Name",
                account_advisor___contact: "Account Advisor - Contact",
                account_advisor___address: "Account Advisor - Address",
                assets_manager___advisor_id: "Assets Manager - Advisor ID",
                assets_manager___name: "Assets Manager - Name",
                assets_manager___contact: "Assets Manager - Contact",
                assets_manager___address: "Assets Manager - Address",
                investment_advisor___manager_id: "Investment Advisor - Manager ID",
                investment_advisor___name: "Investment Advisor - Name",
                investment_advisor___contact: "Investment Advisor - Contact",
                investment_advisor___address: "Investment Advisor - Address",
                insurance_manager___manager_id: "Insurance Manager - Manager ID",
                insurance_manager___name: "Insurance Manager - Name",
                insurance_manager___contact: "Insurance Manager - Contact",
                insurance_manager___address: "Insurance Manager - Address"
            };

            if (labelMap[key]) {
                result[labelMap[key]] = value;
            }
        }

        return result;
    }

    // ---------------- UPDATE UI ----------------
    function updateFields(nestedData) {

        console.log("API DATA:", nestedData);

        const data = flattenObject(nestedData);

        console.log("FLATTENED:", data);

        document.querySelectorAll('.field-card').forEach(card => {

            const fieldKey = card.getAttribute('data-field');
            const valueDiv = card.querySelector('.field-value');

            const value = data[fieldKey] || 'blank';

            valueDiv.innerText = value;
            if (value === 'blank') {
                valueDiv.classList.add('empty');
                card.classList.remove('match');
            } else {
                valueDiv.classList.remove('empty');
                card.classList.add('match');
            }
        });
    }

    // ---------------- STATS ----------------
    function calculateStats() {

        const total = document.querySelectorAll('.field-card').length;
        const matches = document.querySelectorAll('.field-card.match').length;

        const accuracy = total > 0 ? Math.round((matches / total) * 100) : 0;

        accuracyVal.innerText = accuracy + '%';
        errorCount.innerText = total - matches;
    }

    // ---------------- COPY BUTTONS ----------------
    function initCopyButtons() {
        document.querySelectorAll('.field-card').forEach(card => {
            if (card.querySelector('.copy-btn')) {
                return;
            }

            const copyBtn = document.createElement('button');
            copyBtn.type = 'button';
            copyBtn.className = 'copy-btn';
            copyBtn.setAttribute('aria-label', 'Copy value');
            copyBtn.title = 'Copy value';
            copyBtn.innerText = 'Copy';

            copyBtn.addEventListener('click', async (event) => {
                event.preventDefault();
                event.stopPropagation();

                const valueDiv = card.querySelector('.field-value');
                const value = valueDiv ? valueDiv.innerText.trim() : '';

                if (!value || value.toLowerCase() === 'blank' || value === 'Pending...') {
                    return;
                }

                const copied = await copyText(value);
                if (!copied) {
                    return;
                }

                copyBtn.classList.add('copied');
                copyBtn.innerText = 'Copied';
                setTimeout(() => {
                    copyBtn.classList.remove('copied');
                    copyBtn.innerText = 'Copy';
                }, 1000);
            });

            card.appendChild(copyBtn);
        });
    }

    async function copyText(value) {
        try {
            if (navigator.clipboard && navigator.clipboard.writeText) {
                await navigator.clipboard.writeText(value);
                return true;
            }
        } catch (err) {
            console.error('Clipboard API failed, trying fallback:', err);
        }

        const fallbackInput = document.createElement('textarea');
        fallbackInput.value = value;
        fallbackInput.setAttribute('readonly', '');
        fallbackInput.style.position = 'fixed';
        fallbackInput.style.left = '-9999px';
        document.body.appendChild(fallbackInput);
        fallbackInput.select();

        let success = false;
        try {
            success = document.execCommand('copy');
        } catch (err) {
            console.error('execCommand copy failed:', err);
        }

        document.body.removeChild(fallbackInput);
        return success;
    }

});
