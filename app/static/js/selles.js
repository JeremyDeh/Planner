function openSellesPopup() {
    fetch("/enregistre_selles", {
        headers: { 'X-Requested-With': 'XMLHttpRequest' }
    })
    .then(response => response.text())
    .then(html => {
        document.getElementById('sellesPopupContent').innerHTML = html;
        document.getElementById('sellesPopup').style.display = 'flex';
    })
    .catch(() => alert('Erreur lors du chargement des résidents.'));
}

function closeSellesPopup() {
    document.getElementById('sellesPopup').style.display = 'none';
}

function enregistre_selles() {
    const lignes = document.querySelectorAll('#sellesPopupContent tbody tr');
    const data = {};

    lignes.forEach(row => {
        
        const nom = row.querySelector('td:first-child').innerText.trim();
        const pk = row.querySelector('td:last-child').innerText.trim();
        const safe_nom = pk.replace(/ /g, "_");

        const nuit = document.getElementById(`${safe_nom}-nuit-select`).value;
        const matin = document.getElementById(`${safe_nom}-matin-select`).value;
        const apres_midi = document.getElementById(`${safe_nom}-apres_midi-select`).value;
        const note = row.querySelector('input[type="text"]').value;

        data[nom] = {
            pk: pk,
            nuit: nuit,
            matin: matin,
            apres_midi: apres_midi,
            commentaire: note
        };
    });

    fetch("/enregistre_selles", {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify(data)
    })
    .then(response => response.json())
    .then(result => {
        alert(result.message);
        closeSellesPopup();
    })
    .catch(error => {
        console.error('Erreur:', error);
        alert("Erreur lors de l'enregistrement");
    });
}
