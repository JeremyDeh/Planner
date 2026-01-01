// Externalized JS from client_file.html
// Uses runtime data from window.clientFileConfig

(function(){
    // Naissance formatting
    try {
        const naissanceStr = window.clientFileConfig && window.clientFileConfig.naissance ? window.clientFileConfig.naissance : '';
        const regex = /^(\d{4})-(\d{2})-(\d{2})$/;
        const formattedDate = naissanceStr.replace(regex, '$3/$2/$1');
        const el = document.getElementById('naissance');
        if (el && formattedDate) el.textContent = formattedDate;
    } catch (e) {
        console.warn('Naissance formatting failed', e);
    }

    // Filtrage planning
    function isDateInFuture(dateStr) {
        if (!dateStr) return false;
        let d = null;
        if (/\d{4}-\d{2}-\d{2}/.test(dateStr)) {
            d = new Date(dateStr);
        } else if (/\d{2}\/\d{2}\/\d{4}/.test(dateStr)) {
            const [j,m,a] = dateStr.split(/[\/ ]/);
            d = new Date(`${a}-${m}-${j}`);
        } else {
            return true;
        }
        const today = new Date();
        today.setHours(0,0,0,0);
        return d >= today;
    }

    function filterPlanningRows(showAll) {
        const table = document.getElementById('planningTable');
        if (!table) return;
        const ths = Array.from(table.querySelectorAll('thead th'));
        const dateColIdx = ths.findIndex(th => th.textContent.trim().toLowerCase().includes('date'));
        const rows = table.querySelectorAll('tbody tr');
        rows.forEach(row => {
            const tds = Array.from(row.children);
            const cellDate = dateColIdx !== -1 ? (tds[dateColIdx]?.textContent.trim() || '') : '';
            const isFuture = isDateInFuture(cellDate);
            if (showAll) {
                row.style.display = '';
                if (!isFuture) row.classList.add('past-row'); else row.classList.remove('past-row');
            } else {
                row.classList.remove('past-row');
                if (isFuture) row.style.display = ''; else row.style.display = 'none';
            }
        });
    }

    let historiqueMode = false;
    function setupHistoriqueCheckbox() {
        const historiqueCheckbox = document.getElementById('toggleHistoriqueBtn');
        if (!historiqueCheckbox) return;
        historiqueCheckbox.addEventListener('change', function() {
            historiqueMode = this.checked;
            filterPlanningRows(historiqueMode);
        });
    }

    // Button handlers for table action buttons
    function attachTableButtons() {
        document.querySelectorAll('.dots-btn[data-row]').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                try {
                    const rowData = JSON.parse(this.getAttribute('data-row'));
                    // Prefer DF/pdf popup handler when available
                    openImpressionPopupDF(rowData);
                } catch (err) {
                    alert("Erreur lors de l'ouverture de la fiche : données invalides.");
                }
            });
        });
        document.querySelectorAll('.dots-btn-alt[data-row-alt]').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.stopPropagation();
                try {
                    const rowData = JSON.parse(this.getAttribute('data-row-alt'));
                    openRowPopupAlt(rowData);
                } catch (err) {
                    alert("Erreur lors de l'ouverture de la fiche (alt) : données invalides.");
                }
            });
        });
    }

    // Popups for row
    window.openRowPopup = function(rowData) {
        let nomResident = '';
        let oxygen = '';
        let diabete = '';
        const carte = document.querySelector('.fiche-carte .client-list') || document.querySelector('.fiche-carte');
        if (carte) {
            const titre = carte.querySelector('div[style*="font-size: 1.5em"]');
            if (titre) nomResident = titre.textContent.trim();
            const oxyDiv = Array.from(carte.querySelectorAll('div')).find(div => div.textContent && div.textContent.includes('O₂'));
            if (oxyDiv) {
                const match = oxyDiv.textContent.match(/O₂\s*:\s*(Oui|Non)/i);
                if (match) oxygen = match[1];
            }
            const diabDiv = Array.from(carte.querySelectorAll('div')).find(div => div.textContent && div.textContent.includes('Diabète'));
            if (diabDiv) {
                const match = diabDiv.textContent.match(/Diabète\s*:\s*(Oui|Non)/i);
                if (match) diabete = match[1];
            }
        }
        const dataToSend = Object.assign({}, rowData, { nom_resident: nomResident, oxygen: oxygen, diabete: diabete });
        const popup = document.getElementById('rowPopupOverlay');
        const content = document.getElementById('rowPopupInner');
        if (content) content.innerHTML = 'Chargement...';
        if (popup) popup.style.display = 'flex';
        fetch('/popup_row', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dataToSend)
        })
        .then(r => r.text())
        .then(html => { if (content) content.innerHTML = html; })
        .catch(() => { if (content) content.innerHTML = '<div style="color:red;">Erreur de chargement.</div>'; });
    };
    window.closeRowPopup = function() { const el = document.getElementById('rowPopupOverlay'); if (el) el.style.display = 'none'; };

    window.openPDFPopup = function(rowData) {
        let nomResident = '';
        let oxygen = '';
        let diabete = '';
        const carte = document.querySelector('.fiche-carte .client-list') || document.querySelector('.fiche-carte');
        if (carte) {
            const titre = carte.querySelector('div[style*="font-size: 1.5em"]');
            if (titre) nomResident = titre.textContent.trim();
            const oxyDiv = Array.from(carte.querySelectorAll('div')).find(div => div.textContent && div.textContent.includes('O₂'));
            if (oxyDiv) {
                const match = oxyDiv.textContent.match(/O₂\s*:\s*(Oui|Non)/i);
                if (match) oxygen = match[1];
            }
            const diabDiv = Array.from(carte.querySelectorAll('div')).find(div => div.textContent && div.textContent.includes('Diabète'));
            if (diabDiv) {
                const match = diabDiv.textContent.match(/Diabète\s*:\s*(Oui|Non)/i);
                if (match) diabete = match[1];
            }
        }
        const dataToSend = Object.assign({}, rowData, { nom_resident: nomResident, oxygen: oxygen, diabete: diabete });
        const iframe = document.getElementById('pdfIframe');
        const popup = document.getElementById('impressionPopup');
        if (popup) popup.style.display = 'flex';
        if (!iframe) return;
        fetch('/popup_row_pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dataToSend)
        })
        .then(res => res.blob())
        .then(blob => {
            const url = URL.createObjectURL(blob);
            iframe.src = url;
        })
        .catch(() => { iframe.srcdoc = "<p style='color:red'>Erreur lors de la génération du PDF.</p>"; });
    };

    window.openRowPopupAlt = function(rowData) {
        let nomResident = '';
        let oxygen = '';
        let diabete = '';
        const carte = document.querySelector('.fiche-carte .client-list') || document.querySelector('.fiche-carte');
        if (carte) {
            const titre = carte.querySelector('div[style*="font-size: 1.5em"]');
            if (titre) nomResident = titre.textContent.trim();
            const oxyDiv = Array.from(carte.querySelectorAll('div')).find(div => div.textContent && div.textContent.includes('O₂'));
            if (oxyDiv) {
                const match = oxyDiv.textContent.match(/O₂\s*:\s*(Oui|Non)/i);
                if (match) oxygen = match[1];
            }
            const diabDiv = Array.from(carte.querySelectorAll('div')).find(div => div.textContent && div.textContent.includes('Diabète'));
            if (diabDiv) {
                const match = diabDiv.textContent.match(/Diabète\s*:\s*(Oui|Non)/i);
                if (match) diabete = match[1];
            }
        }
        const dataToSend = Object.assign({}, rowData, { nom_resident: nomResident, oxygen: oxygen, diabete: diabete });
        const popup = document.getElementById('rowPopupOverlayAlt');
        const content = document.getElementById('rowPopupContentAlt');
        if (content) content.innerHTML = 'Chargement...';
        if (popup) popup.style.display = 'flex';
        fetch('/popup_row_alt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(dataToSend)
        })
        .then(r => r.text())
        .then(html => { if (content) content.innerHTML = html; })
        .catch(() => { if (content) content.innerHTML = '<div style="color:red;">Erreur de chargement.</div>'; });
    };
    window.closeRowPopupAlt = function() { const el = document.getElementById('rowPopupOverlayAlt'); if (el) el.style.display = 'none'; };

    // Toggle view helper
    window.toggleView = function(button) {
        const table = document.getElementById("fiche-planning_id");
        const calendar = document.getElementById("calendar");
        if (!table || !calendar) return;
        if (table.style.display === "none") {
            table.style.display = "block";
            calendar.style.display = "none";
            button.textContent = "Afficher le calendrier";
        } else {
            table.style.display = "none";
            calendar.style.display = "block";
            button.textContent = "Afficher la table";
        }
    };

    // Initialize on DOMContentLoaded
    window.addEventListener('DOMContentLoaded', function() {
        setupHistoriqueCheckbox();
        filterPlanningRows(false);
        attachTableButtons();
        // ======= Recap-style global impression (sidebar) =======
        // Open the global impression popup and load /impression via AJAX
        window.openImpressionPopupGlobal = function() {
            // prefer explicit impressionPopupGlobal if present, otherwise use legacy impressionPopup
            var popup = document.getElementById('impressionPopupGlobal') || document.getElementById('impressionPopup');
            if (popup) popup.style.display = 'flex';
            var impressionUrl = '/impression';
            fetch(impressionUrl, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
                .then(function(res) { return res.text(); })
                .then(function(html) {
                    var target = document.getElementById('impressionContentInner');
                    if (target) target.innerHTML = html;
                })
                .catch(function() {
                    var target = document.getElementById('impressionContentInner');
                    if (target) target.innerHTML = '<div style="color:red">Erreur de chargement.</div>';
                });
        };
        window.closeImpressionPopupGlobal = function() {
            var popup = document.getElementById('impressionPopupGlobal') || document.getElementById('impressionPopup');
            if (popup) popup.style.display = 'none';
        };
        window.printImpressionContentGlobal = function() {
            var contentEl = document.getElementById('impressionContentInner');
            if (!contentEl) return;
            var printContents = contentEl.innerHTML;
            var printWindow = window.open('', '', 'height=800,width=1200');
            printWindow.document.write('<html><head><title>Impression</title>');
            printWindow.document.write(document.head.innerHTML);
            printWindow.document.write('</head><body>');
            printWindow.document.write(printContents);
            printWindow.document.write('</body></html>');
            printWindow.document.close();
            printWindow.focus();
            printWindow.print();
            printWindow.close();
        };

        // Bind sidebar & popup buttons for the global impression
        var imprimerBtn = document.getElementById('imprimerBtn');
        if (imprimerBtn) imprimerBtn.addEventListener('click', function(e){ e.preventDefault(); window.openImpressionPopupGlobal(); });
        var closeImprBtn = document.getElementById('closeImpressionGlobalBtn');
        if (closeImprBtn) closeImprBtn.addEventListener('click', function(){ window.closeImpressionPopupGlobal(); });
        var printImprBtn = document.getElementById('printImpressionGlobalBtn');
        if (printImprBtn) printImprBtn.addEventListener('click', function(){ window.printImpressionContentGlobal(); });
    });

})();
// Externalized from client_file.html
(function(){
    // Use config provided by template: window.clientFileConfig
    const cfg = window.clientFileConfig || {};

    // Impression popup functions
    function openImpressionPopup(rowData) {
        const popup = document.getElementById('impressionPopup'); if (!popup) return;
        popup.style.display = 'flex';
        const iframe = document.getElementById('pdfIframe');
        if (!iframe) return;

        fetch('/popup_row_pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(rowData || {})
        })
        .then(res => res.blob())
        .then(blob => { const url = URL.createObjectURL(blob); iframe.src = url; })
        .catch(err => { console.error(err); iframe.srcdoc = "<p style='color:red'>Erreur lors de la génération du PDF.</p>"; });
    }
    function closeImpressionPopup() { const popup = document.getElementById('impressionPopup'); if (popup) popup.style.display = 'none'; const iframe = document.getElementById('pdfIframe'); if (iframe) iframe.src = ''; }
    function printIframe() { const iframe = document.getElementById('pdfIframe'); if (!iframe || !iframe.contentWindow) return; iframe.contentWindow.focus(); iframe.contentWindow.print(); }

    // Expose globals used by templates
    window.openImpressionPopup = openImpressionPopup;
    window.closeImpressionPopup = closeImpressionPopup;
    window.printIframe = printIframe;

    // DF / row-level PDF flow (keeps separate modal 'impressionPopupDF' if present)
    window.openImpressionPopupDF = function(rowData) {
        var popup = document.getElementById('impressionPopupDF') || document.getElementById('impressionPopup');
        var iframe = document.getElementById('pdfIframe');
        if (popup) popup.style.display = 'flex';
        if (!iframe) return;
        fetch('/popup_row_pdf', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(rowData || {})
        })
        .then(function(res){ return res.blob(); })
        .then(function(blob){ var url = URL.createObjectURL(blob); iframe.src = url; })
        .catch(function(err){ console.error(err); iframe.srcdoc = "<p style='color:red'>Erreur lors de la génération du PDF.</p>"; });
    };

    window.closeImpressionPopupDF = function() {
        var popup = document.getElementById('impressionPopupDF') || document.getElementById('impressionPopup');
        if (popup) popup.style.display = 'none';
        var iframe = document.getElementById('pdfIframe'); if (iframe) iframe.src = '';
    };

    // DOM ready handlers
    document.addEventListener('DOMContentLoaded', function() {
        // NOTE: do NOT bind the sidebar `imprimerBtn` here to the row/pdf popup.
        // The sidebar print button must open the 7-day recap overlay only.
        // Binding for the sidebar button to the recap overlay is handled elsewhere
        // (openImpressionPopupGlobal in the other IIFE). This prevents the button
        // from triggering both the recap overlay and the row/pdf iframe.

        // Popup add/resident
        const openBtn    = document.getElementById("openPopupBtn");
        const closeBtn   = document.getElementById("closePopupBtn");
        const popup      = document.getElementById("popupForm");
        const form       = document.getElementById("popupFormInner");

        // Départ résident
        const openDepartBtn    = document.getElementById("openDepartPopupBtn");
        const closeDepartBtn   = document.getElementById("closeDepartPopupBtn");
        const departPopup      = document.getElementById("departPopupForm");
        const departForm       = document.getElementById("departPopupFormInner");

        // Message popup (unique)
        const messageBox = document.getElementById("popupMessage");

        function showPopup(message, type) {
            if (!messageBox) return;
            messageBox.textContent = message;
            messageBox.style.background = type === "success" ? "#1e7e34" : "#c82333";
            messageBox.style.display = "block";
            requestAnimationFrame(() => { messageBox.style.opacity = "1"; });
            setTimeout(() => { messageBox.style.opacity = "0"; setTimeout(()=>{ messageBox.style.display = 'none'; },300); }, 3000);
        }

        if (openBtn && popup) openBtn.onclick = () => popup.style.display = "flex";
        if (closeBtn && popup) closeBtn.onclick = () => popup.style.display = "none";
        if (openDepartBtn && departPopup) openDepartBtn.onclick = () => departPopup.style.display = "flex";
        if (closeDepartBtn && departPopup) closeDepartBtn.onclick = () => departPopup.style.display = "none";

        if (form) {
            form.onsubmit = async function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                try {
                    const response = await fetch("/add_resident", { method: "POST", body: formData });
                    const data = await response.json();
                    if (data.success) {
                        showPopup("✅ Résident ajouté avec succès !", "success");
                        popup.style.display = "none";
                        this.reset();
                    } else {
                        showPopup("❌ Erreur : " + (data.error || "Impossible d'ajouter le résident."), "error");
                    }
                } catch {
                    showPopup("⚠️ Erreur réseau ou serveur.", "error");
                }
            };
        }

        if (departForm) {
            departForm.onsubmit = async function(e) {
                e.preventDefault();
                const formData = new FormData(this);
                try {
                    const response = await fetch("/delete_resident", { method: "POST", body: formData });
                    const data = await response.json();
                    if (data.success) {
                        showPopup("✅ Résident supprimé avec succès !", "success");
                        departPopup.style.display = "none";
                        this.reset();
                    } else {
                        showPopup("❌ Erreur : " + (data.error || "Impossible de supprimer le résident."), "error");
                    }
                } catch {
                    showPopup("⚠️ Erreur réseau ou serveur.", "error");
                }
            };
        }

        // Depart patient helpers
        window.showDepartPatientList = function() { const el = document.getElementById('departPatientList'); if (el) el.style.display = 'block'; };
        window.filterDepartPatientList = function() { const input = (document.getElementById('departNomPatientInput') || {}).value || ''; const q = input.toLowerCase(); document.querySelectorAll('#departPatientList .patient-item').forEach(item => { item.style.display = item.textContent.toLowerCase().includes(q) ? '' : 'none'; }); };
        window.selectDepartPatient = function(el) { if (!el) return; const display = document.getElementById('departNomPatientInput'); const hidden = document.getElementById('departNomPatientHidden'); if (display) display.value = el.textContent.trim(); if (hidden) hidden.value = el.getAttribute('data-pk'); const list = document.getElementById('departPatientList'); if (list) list.style.display = 'none'; };
        document.addEventListener('click', function(e) { const list = document.getElementById('departPatientList'); const input = document.getElementById('departNomPatientInput'); if (!list) return; if (e.target !== input && !list.contains(e.target)) list.style.display = 'none'; });

        // Autocomplete init (the autocomplete.js file must be included by the template)
        try { if (typeof initAutocomplete === 'function') initAutocomplete('nomPatientInput', 'patientList', 'patient-item', 'nomPatientHidden'); } catch (e) { /* ignore */ }

        // Show graph (Plotly)

        const showBtn = document.getElementById('show-graph');

if (showBtn) {
    showBtn.addEventListener('click', function () {

        const idEl = document.getElementById('residentIdHidden');
        const pk = idEl ? idEl.value : '';

        if (!pk) {
            alert('Aucun résident sélectionné');
            return;
        }

        fetch('/graphique_selles?pk=' + encodeURIComponent(pk))
            .then(response => response.json())
            .then(figData => {
                const container = document.getElementById('graph-container');
                if (!container) return;

                container.innerHTML = '';
                const div = document.createElement('div');
                container.appendChild(div);

                Plotly.newPlot(
                    div,
                    figData.data,
                    figData.layout,
                    { responsive: true, displayModeBar: false }
                );

                document.getElementById('popup').style.display = 'block';
            })
            .catch(err => {
                console.error(err);
                alert('Erreur lors du chargement du graphique');
            });
    });
}
        const popupClose = document.getElementById('popup-close'); if (popupClose) popupClose.addEventListener('click', function() { document.getElementById('popup').style.display = 'none'; });

    // Wire impression popup close button (template has id closeImpressionBtn)
    const closeImpressionBtn = document.getElementById('closeImpressionBtn'); if (closeImpressionBtn) closeImpressionBtn.addEventListener('click', closeImpressionPopup);

    // Wire row popup close/print buttons (we removed inline onclicks)
    const rowCloseBtn = document.querySelector('#rowPopupOverlay .row-close-btn'); if (rowCloseBtn) rowCloseBtn.addEventListener('click', function(){ if (typeof window.closeRowPopup === 'function') window.closeRowPopup(); else document.getElementById('rowPopupOverlay').style.display = 'none'; });
    const rowPrintBtn = document.querySelector('#rowPopupOverlay .row-print-btn'); if (rowPrintBtn) rowPrintBtn.addEventListener('click', function(){ try { window.print(); } catch(e) { console.warn('print failed', e); } });
    const rowCloseAltBtn = document.querySelector('#rowPopupOverlayAlt .row-close-alt-btn'); if (rowCloseAltBtn) rowCloseAltBtn.addEventListener('click', function(){ if (typeof window.closeRowPopupAlt === 'function') window.closeRowPopupAlt(); else document.getElementById('rowPopupOverlayAlt').style.display = 'none'; });

    // Attach click handlers for patient lists created server-side (removed inline onclicks)
    document.querySelectorAll('#departPatientList .patient-item').forEach(item => { item.addEventListener('click', function(){ if (typeof window.selectDepartPatient === 'function') window.selectDepartPatient(this); else { const display = document.getElementById('departNomPatientInput'); const hidden = document.getElementById('departNomPatientHidden'); if (display) display.value = this.textContent.trim(); if (hidden) hidden.value = this.getAttribute('data-pk'); const list = document.getElementById('departPatientList'); if (list) list.style.display = 'none'; } }); });
    const selectPatientFn = window.selectPatient || function(el){ const display=document.getElementById('nomPatientInput'); const hidden=document.getElementById('nomPatientHidden'); if(display) display.value = el.textContent.trim(); if(hidden) hidden.value = el.getAttribute('data-pk'); const list=document.getElementById('patientList'); if(list) list.style.display='none'; };
    document.querySelectorAll('#patientList .patient-item').forEach(item => { item.addEventListener('click', function(){ selectPatientFn(this); }); });

        // Row and PDF popups handlers
        window.openRowPopup = function(rowData) {
            let nomResident = '', oxygen = '', diabete = '';
            const carte = document.querySelector('.fiche-carte .client-list') || document.querySelector('.fiche-carte');
            if (carte) {
                const titre = carte.querySelector('div[style*="font-size: 1.5em"]'); if (titre) nomResident = titre.textContent.trim();
                const oxyDiv = Array.from(carte.querySelectorAll('div')).find(div => div.textContent && div.textContent.includes('O₂')); if (oxyDiv) { const match = oxyDiv.textContent.match(/O₂\s*:\s*(Oui|Non)/i); if (match) oxygen = match[1]; }
                const diabDiv = Array.from(carte.querySelectorAll('div')).find(div => div.textContent && div.textContent.includes('Diabète')); if (diabDiv) { const match = diabDiv.textContent.match(/Diabète\s*:\s*(Oui|Non)/i); if (match) diabete = match[1]; }
            }
            const dataToSend = Object.assign({}, rowData, { nom_resident: nomResident, oxygen: oxygen, diabete: diabete });
            const popup = document.getElementById('rowPopupOverlay'); const content = document.getElementById('rowPopupInner'); if (!popup || !content) return; content.innerHTML = 'Chargement...'; popup.style.display = 'flex'; fetch('/popup_row', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dataToSend) }).then(r => r.text()).then(html => { content.innerHTML = html; }).catch(()=>{ content.innerHTML = '<div style="color:red;">Erreur de chargement.</div>'; });
        };
        window.closeRowPopup = function() { const p = document.getElementById('rowPopupOverlay'); if (p) p.style.display = 'none'; };

        window.openPDFPopup = function(rowData) {
            let nomResident = '', oxygen = '', diabete = '';
            const carte = document.querySelector('.fiche-carte .client-list') || document.querySelector('.fiche-carte');
            if (carte) { const titre = carte.querySelector('div[style*="font-size: 1.5em"]'); if (titre) nomResident = titre.textContent.trim(); const oxyDiv = Array.from(carte.querySelectorAll('div')).find(div => div.textContent && div.textContent.includes('O₂')); if (oxyDiv) { const match = oxyDiv.textContent.match(/O₂\s*:\s*(Oui|Non)/i); if (match) oxygen = match[1]; } const diabDiv = Array.from(carte.querySelectorAll('div')).find(div => div.textContent && div.textContent.includes('Diabète')); if (diabDiv) { const match = diabDiv.textContent.match(/Diabète\s*:\s*(Oui|Non)/i); if (match) diabete = match[1]; } }
            const dataToSend = Object.assign({}, rowData, { nom_resident: nomResident, oxygen: oxygen, diabete: diabete });
            const iframe = document.getElementById('pdfIframe'); if (!iframe) return; document.getElementById('impressionPopup').style.display = 'flex'; fetch('/popup_row_pdf', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dataToSend) }).then(res => res.blob()).then(blob => { const url = URL.createObjectURL(blob); iframe.src = url; }).catch(()=>{ iframe.srcdoc = "<p style='color:red'>Erreur lors de la génération du PDF.</p>"; });
        };

        window.openRowPopupAlt = function(rowData) {
            let nomResident = '', oxygen = '', diabete = '';
            const carte = document.querySelector('.fiche-carte .client-list') || document.querySelector('.fiche-carte');
            if (carte) { const titre = carte.querySelector('div[style*="font-size: 1.5em"]'); if (titre) nomResident = titre.textContent.trim(); const oxyDiv = Array.from(carte.querySelectorAll('div')).find(div => div.textContent && div.textContent.includes('O₂')); if (oxyDiv) { const match = oxyDiv.textContent.match(/O₂\s*:\s*(Oui|Non)/i); if (match) oxygen = match[1]; } const diabDiv = Array.from(carte.querySelectorAll('div')).find(div => div.textContent && div.textContent.includes('Diabète')); if (diabDiv) { const match = diabDiv.textContent.match(/Diabète\s*:\s*(Oui|Non)/i); if (match) diabete = match[1]; } }
            const dataToSend = Object.assign({}, rowData, { nom_resident: nomResident, oxygen: oxygen, diabete: diabete });
            const popup = document.getElementById('rowPopupOverlayAlt'); const content = document.getElementById('rowPopupContentAlt'); if (!popup || !content) return; content.innerHTML = 'Chargement...'; popup.style.display = 'flex'; fetch('/popup_row_alt', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(dataToSend) }).then(r => r.text()).then(html => { content.innerHTML = html; }).catch(()=>{ content.innerHTML = '<div style="color:red;">Erreur de chargement.</div>'; });
        };
        window.closeRowPopupAlt = function() { const p = document.getElementById('rowPopupOverlayAlt'); if (p) p.style.display = 'none'; };

        // Planning helpers
        function isDateInFuture(dateStr) { if (!dateStr) return false; let d = null; if (/\d{4}-\d{2}-\d{2}/.test(dateStr)) { d = new Date(dateStr); } else if (/\d{2}\/\d{2}\/\d{4}/.test(dateStr)) { const [j,m,a] = dateStr.split(/[\/ ]/); d = new Date(`${a}-${m}-${j}`); } else { return true; } const today = new Date(); today.setHours(0,0,0,0); return d >= today; }
        function filterPlanningRows(showAll) { const table = document.getElementById('planningTable'); if (!table) return; const ths = Array.from(table.querySelectorAll('thead th')); const dateColIdx = ths.findIndex(th => th.textContent.trim().toLowerCase().includes('date')); const rows = table.querySelectorAll('tbody tr'); rows.forEach(row => { const tds = Array.from(row.children); const cellDate = dateColIdx !== -1 ? (tds[dateColIdx]?.textContent.trim() || '') : ''; const isFuture = isDateInFuture(cellDate); if (showAll) { row.style.display = ''; if (!isFuture) row.classList.add('past-row'); else row.classList.remove('past-row'); } else { row.classList.remove('past-row'); if (isFuture) row.style.display = ''; else row.style.display = 'none'; } }); }
        let historiqueMode = false;
        const historiqueCheckbox = document.getElementById('toggleHistoriqueBtn'); if (historiqueCheckbox) historiqueCheckbox.addEventListener('change', function() { historiqueMode = this.checked; filterPlanningRows(historiqueMode); });
        filterPlanningRows(false);

    // Table dots handlers
    document.querySelectorAll('.dots-btn[data-row]').forEach(btn => { btn.addEventListener('click', function(e) { e.stopPropagation(); try { const rowData = JSON.parse(this.getAttribute('data-row')); if (typeof openImpressionPopupDF === 'function') openImpressionPopupDF(rowData); else openPDFPopup(rowData); } catch (err) { alert('Erreur lors de l\'ouverture de la fiche : données invalides.'); } }); });
        document.querySelectorAll('.dots-btn-alt[data-row-alt]').forEach(btn => { btn.addEventListener('click', function(e) { e.stopPropagation(); try { const rowData = JSON.parse(this.getAttribute('data-row-alt')); openRowPopupAlt(rowData); } catch (err) { alert('Erreur lors de l\'ouverture de la fiche (alt) : données invalides.'); } }); });

        // Calendar (use cfg.nodes if provided)
        (function initCalendar() {
            const calendarEl = document.getElementById('calendar');
            const rawEvents = Array.isArray(cfg.nodes) ? cfg.nodes : [];
            const events = rawEvents.map(ev => ({ title: ev['Rendez-vous'] || 'Rendez-vous', start: ev.Date || null, description: ev['Note'] || '<Aucun commentaire>' }));
            if (calendarEl && typeof FullCalendar !== 'undefined') {
                const calendar = new FullCalendar.Calendar(calendarEl, {
                    initialView: 'dayGridMonth', locale: 'fr', firstDay: 1,
                    slotMinTime: '07:00:00', slotMaxTime: '23:50:00', allDaySlot: false,
                    headerToolbar: { left: 'prev,next today', center: 'title', right: 'dayGridMonth' },
                    buttonText: { today: "Aujourd'hui", month: 'Mois' },
                    events: events,
                    eventDidMount: function (info) {
                        let tooltip; const desc = info.event.extendedProps.description;
                        if (desc) {
                            info.el.addEventListener('mouseenter', function(e) { tooltip = document.createElement('div'); tooltip.className = 'fc-event-custom-tooltip'; tooltip.innerText = desc; document.body.appendChild(tooltip); const rect = info.el.getBoundingClientRect(); tooltip.style.position = 'absolute'; tooltip.style.background = '#232946'; tooltip.style.color = '#fff'; tooltip.style.padding = '8px 14px'; tooltip.style.borderRadius = '8px'; tooltip.style.fontSize = '1em'; tooltip.style.boxShadow = '0 2px 8px rgba(35,41,70,0.18)'; tooltip.style.zIndex = '9999'; tooltip.style.pointerEvents = 'none'; tooltip.style.left = (rect.left + window.scrollX + rect.width/2 - 80) + 'px'; tooltip.style.top = (rect.top + window.scrollY - tooltip.offsetHeight - 12) + 'px'; });
                            info.el.addEventListener('mousemove', function(e) { if (tooltip) { tooltip.style.left = (e.pageX + 12) + 'px'; tooltip.style.top = (e.pageY - tooltip.offsetHeight - 12) + 'px'; } });
                            info.el.addEventListener('mouseleave', function() { if (tooltip) { tooltip.remove(); tooltip = null; } });
                        }
                    }
                });
                calendar.render();
            }
        })();

        // Format naissance if provided
        try {
            const naissanceStr = cfg.naissance || '';
            if (naissanceStr) {
                const regex = /^(\d{4})-(\d{2})-(\d{2})$/;
                const formatted = naissanceStr.replace(regex, '$3/$2/$1');
                const el = document.getElementById('naissance'); if (el) el.textContent = formatted;
            }
        } catch (e) { /* ignore */ }

    }); // DOMContentLoaded

})();
