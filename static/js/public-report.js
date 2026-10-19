document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('publicIncidentForm');
  const categorySelect = document.getElementById('incidentCategory');
  const submitButton = form.querySelector('button[type="submit"]');
  const message = document.getElementById('publicIncidentMessage');
  const photoInput = document.getElementById('incidentPhoto');
  const photoPreview = document.getElementById('photoPreview');
  const successPanel = document.getElementById('publicIncidentSuccess');
  const MAX_PHOTO_SIZE = 5 * 1024 * 1024;

  function showMessage(text, isError = false) {
    message.className = `small mb-2 ${isError ? 'text-danger' : 'text-success'}`;
    message.textContent = text;
  }

  async function readResponse(response) {
    const data = await response.json().catch(() => null);
    if (!response.ok) {
      if (response.status === 429) {
        throw new Error('Trop de signalements envoyés depuis cette connexion. Réessayez dans un moment.');
      }
      const details = data && Object.values(data)
        .flatMap(value => Array.isArray(value) ? value : [value])
        .filter(value => typeof value === 'string')
        .join(' ');
      throw new Error(details || `Le serveur a répondu avec une erreur (${response.status}). Réessayez.`);
    }
    return data;
  }

  async function loadCategories() {
    try {
      const response = await fetch('/api/incidents/categories/');
      const data = await readResponse(response);
      const categories = data.results || data;
      categorySelect.replaceChildren(new Option('Choisir un type d’incident', ''));
      categories.forEach(category => {
        categorySelect.add(new Option(category.name_display || category.name, category.id));
      });
      submitButton.disabled = false;
    } catch (error) {
      categorySelect.replaceChildren(new Option('Catégories indisponibles', ''));
      showMessage(error.message, true);
    }
  }

  photoInput.addEventListener('change', () => {
    const file = photoInput.files[0];
    photoPreview.replaceChildren();
    photoPreview.hidden = !file;
    if (!file) return;
    if (file.size > MAX_PHOTO_SIZE) {
      const warning = document.createElement('span');
      warning.className = 'small text-danger';
      warning.textContent = 'La photo dépasse 5 Mio : choisissez une image plus légère.';
      photoPreview.appendChild(warning);
      return;
    }
    const image = document.createElement('img');
    image.alt = 'Aperçu de la photo';
    image.src = URL.createObjectURL(file);
    image.onload = () => URL.revokeObjectURL(image.src);
    const name = document.createElement('span');
    name.className = 'small text-secondary';
    name.textContent = file.name;
    photoPreview.append(image, name);
  });

  form.addEventListener('submit', async event => {
    event.preventDefault();
    if (!form.checkValidity()) {
      form.classList.add('was-validated');
      showMessage('Complétez les champs obligatoires.', true);
      return;
    }
    const photo = photoInput.files[0];
    if (photo && photo.size > MAX_PHOTO_SIZE) {
      showMessage('La photo ne doit pas dépasser 5 Mio.', true);
      return;
    }

    const payload = new FormData(form);
    if (!photo) payload.delete('photo');
    submitButton.disabled = true;
    showMessage('Envoi du signalement…');
    try {
      const response = await fetch('/api/incidents/public/', {
        method: 'POST',
        body: payload,
      });
      const incident = await readResponse(response);
      form.reset();
      form.classList.remove('was-validated');
      photoPreview.hidden = true;
      message.textContent = '';
      document.getElementById('trackingCode').textContent = incident.tracking_code;
      document.getElementById('trackLink').href = `/suivi/?code=${encodeURIComponent(incident.tracking_code)}`;
      try {
        const saved = JSON.parse(localStorage.getItem('giu_tracking_codes') || '[]');
        localStorage.setItem('giu_tracking_codes', JSON.stringify([incident.tracking_code, ...saved.filter(code => code !== incident.tracking_code)].slice(0, 10)));
      } catch (storageError) { /* l'historique local est facultatif */ }
      form.hidden = true;
      successPanel.hidden = false;
      successPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } catch (error) {
      const messageText = error instanceof TypeError
        ? 'Impossible de joindre le serveur. Vérifiez votre connexion puis réessayez.'
        : error.message;
      showMessage(messageText, true);
    } finally {
      submitButton.disabled = false;
    }
  });

  document.getElementById('copyTrackingCode').addEventListener('click', async event => {
    const code = document.getElementById('trackingCode').textContent;
    try {
      await navigator.clipboard.writeText(code);
      event.currentTarget.textContent = 'Code copié ✓';
    } catch (error) {
      event.currentTarget.textContent = code;
    }
  });

  document.getElementById('newReportButton').addEventListener('click', () => {
    successPanel.hidden = true;
    form.hidden = false;
    document.getElementById('incidentTitle').focus();
  });

  loadCategories();
});
