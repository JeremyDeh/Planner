// Externalized JS from recap_jour.html
(function(){
    // URLs populated by template in a small inline block
    const cfg = window.recapConfig || { impression: '/impression', update_status: '/update_status' };

    // Service select filter (cardboxes)
    function appliquerFiltre() {
        var select = document.getElementById('serviceSelect');
        if (!select) return;
        var selectedService = select.value;
        var allCardboxes = document.querySelectorAll('.cardbox-modern.filterable');

        allCardboxes.forEach(function(cardbox) {
            var lis = cardbox.querySelectorAll('ul li[data-responsable]');
            var visibleCount = 0;
            lis.forEach(function(li) {
                if (selectedService === "Tous") {
                    li.style.display = '';
                    visibleCount++;
                } else {
                    if (li.getAttribute('data-responsable') === selectedService || li.getAttribute('data-responsable') === 'Tous') {
                        li.style.display = '';
                        visibleCount++;
                    } else {
                        li.style.display = 'none';
                    }
                }
            });
            cardbox.style.display = visibleCount === 0 ? 'none' : '';
        });
    }

    // Filter for notes list
    function filterByService() {
        var sel = document.getElementById('serviceSelect'); if (!sel) return;
        const selected = sel.value;
        const items = document.querySelectorAll('li[data-service]');
        items.forEach(item => {
            const service = item.getAttribute('data-service');
            if (selected === 'Tous') { item.style.display = 'flex'; return; }
            if (service === selected || service === 'Tous') item.style.display = 'flex'; else item.style.display = 'none';
        });
    }

    // Selles slider behavior
    function setupSellesSlider() {
        var sliderSwitch = document.getElementById('sellesSliderSwitch');
        if (!sliderSwitch) return;
        var normalDiv = document.getElementById('sellesContentNormal');
        var derniersDiv = document.getElementById('sellesContentDerniersJours');
        var labelAuj = document.getElementById('sliderLabelAuj');
        var labelDerniers = document.getElementById('sliderLabelDerniers');

        function updateDisplay() {
            if (sliderSwitch.checked) {
                normalDiv.style.display = '';
                derniersDiv.style.display = 'none';
                labelAuj.style.display = '';
                labelDerniers.style.display = 'none';
            } else {
                normalDiv.style.display = 'none';
                derniersDiv.style.display = '';
                labelAuj.style.display = 'none';
                labelDerniers.style.display = '';
            }
        }

        sliderSwitch.addEventListener('click', function(event) { event.stopPropagation(); updateDisplay(); });
        updateDisplay();
    }

    // Impression popup (recap overlay)
    window.openImpressionPopup = function() {
        var popup = document.getElementById('impressionPopup'); if (!popup) return; popup.style.display = 'flex';
        fetch(cfg.impression, { headers: { 'X-Requested-With': 'XMLHttpRequest' } }).then(r=>r.text()).then(html=>{
            var target = document.getElementById('impressionContentInner'); if (target) target.innerHTML = html;
        }).catch(()=>{ var target = document.getElementById('impressionContentInner'); if (target) target.innerHTML = '<div style="color:red">Erreur de chargement.</div>'; });
    };
    window.closeImpressionPopup = function(){ var popup = document.getElementById('impressionPopup'); if (popup) popup.style.display = 'none'; };
    window.printImpressionContent = function(){ var contentEl = document.getElementById('impressionContentInner'); if (!contentEl) return; var printContents = contentEl.innerHTML; var printWindow = window.open('', '', 'height=800,width=1200'); printWindow.document.write('<html><head><title>Impression</title>'); printWindow.document.write(document.head.innerHTML); printWindow.document.write('</head><body>'); printWindow.document.write(printContents); printWindow.document.write('</body></html>'); printWindow.document.close(); printWindow.focus(); printWindow.print(); printWindow.close(); };

    // updateStatus uses cfg.update_status
    window.updateStatus = function(checkbox) {
        const rowId = checkbox.getAttribute('data-id');
        const newStatus = checkbox.checked ? 0 : 1;
        const liElement = checkbox.closest('li');
        const textElement = liElement.querySelector('.note-text');
        const heureElement = liElement.querySelector('span:first-child');
        if (checkbox.checked) {
            if (textElement) textElement.style.color = '#abababff';
            if (heureElement) heureElement.style.background = '#abababff';
        } else {
            if (textElement) textElement.style.color = '#5c5859';
            if (heureElement) heureElement.style.background = '#eebbc3';
        }
        fetch(cfg.update_status, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ id: rowId, status: newStatus }) })
            .then(res => res.json()).then(data => console.log('Mise à jour :', data)).catch(err => console.error(err));
    };

    // DOM ready wiring
    document.addEventListener('DOMContentLoaded', function(){
        // serviceSelect
        var select = document.getElementById('serviceSelect'); if (select) { select.addEventListener('change', appliquerFiltre); setTimeout(appliquerFiltre,10); }
        // notes filter
        setTimeout(filterByService, 10);
        var ss = document.getElementById('serviceSelect'); if (ss) ss.addEventListener('change', filterByService);
        // setup slider
        setupSellesSlider();
        // bind global impression buttons
        var imprBtn = document.getElementById('imprimerBtn'); if (imprBtn) imprBtn.addEventListener('click', function(e){ e.preventDefault(); window.openImpressionPopup(); });
        // init selles popup opener placeholder - original template calls openSellesPopup() via onclick; keep a global no-op if missing
        if (typeof window.openSellesPopup !== 'function') window.openSellesPopup = function(){ var p = document.getElementById('sellesPopup'); if (p) p.style.display = 'flex'; };
    });
})();
