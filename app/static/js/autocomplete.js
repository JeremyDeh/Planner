function initAutocomplete(inputId, listId, itemClass, hiddenId = null) {

    const inputElem = document.getElementById(inputId);
    const listElem = document.getElementById(listId);

    // Affiche la liste
    function showList() {
        listElem.style.display = 'block';
    }

    // Cache la liste avec petit délai (pour laisser le temps de cliquer)
    function hideList() {
        setTimeout(() => listElem.style.display = 'none', 200);
    }

    // Sélection d'un élément
    function selectItem(element) {
        // Mettre le nom dans le champ visible
        inputElem.value = element.textContent.trim();

        // Si un champ hidden est prévu, mettre la PK
        if (hiddenId) {
            document.getElementById(hiddenId).value = element.getAttribute('data-pk');
        }

        hideList();
    }

    // Filtre la liste selon la saisie
    function filterList() {
        const val = inputElem.value.toLowerCase();
        listElem.querySelectorAll(`.${itemClass}`).forEach(item => {
            item.style.display = item.textContent.toLowerCase().includes(val) ? '' : 'none';
        });
    }

    // Événements
    inputElem.addEventListener('focus', showList);
    inputElem.addEventListener('input', filterList);
    inputElem.addEventListener('blur', hideList);

    // Événement clic sur les items
    listElem.querySelectorAll(`.${itemClass}`).forEach(item => {
        item.addEventListener('click', () => selectItem(item));
    });
}
