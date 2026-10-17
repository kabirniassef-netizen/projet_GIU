(() => {
  const user = JSON.parse(localStorage.getItem('user_data') || '{}');
  const isManager = ['manager', 'admin'].includes(user.role) || user.is_superuser;
  const canManageInterventions = ['agent', 'manager', 'admin'].includes(user.role) || user.is_superuser;
  const workQueue = document.getElementById('workQueue');
  const incidentColumn = document.getElementById('incidentQueueColumn');
  const interventionColumn = document.getElementById('interventionQueueColumn');
  const incidentQueue = document.getElementById('incidentQueue');
  const interventionQueue = document.getElementById('interventionQueue');
  const validatedIncidentIds = new Set();
  let incidentDataLoaded = false;

  function listItems(data) {
    return Array.isArray(data) ? data : (data.results || []);
  }

  function createButton(label, action, id, className) {
    const button = document.createElement('button');
    button.type = 'button';
    button.className = `btn btn-sm ${className}`;
    button.textContent = label;
    button.dataset.queueAction = action;
    button.dataset.recordId = id;
    return button;
  }

  function createQueueRow(title, status) {
    const row = document.createElement('div');
    row.className = 'queue-row border-top py-3';

    const heading = document.createElement('div');
    heading.className = 'd-flex flex-wrap justify-content-between align-items-center gap-2';
    const name = document.createElement('strong');
    name.textContent = title;
    const state = document.createElement('span');
    state.className = 'text-secondary small';
    state.textContent = status;
    heading.append(name, state);

    const controls = document.createElement('div');
    controls.className = 'd-flex flex-wrap gap-2 mt-2';
    const feedback = document.createElement('span');
    feedback.className = 'queue-feedback small mt-2 d-block';
    row.append(heading, controls, feedback);
    return { row, controls, feedback };
  }

  function filterPlannerOptions() {
    if (!incidentDataLoaded) return;
    const select = document.getElementById('interventionIncident');
    if (!select) return;
    for (const option of Array.from(select.options)) {
      if (option.value && !validatedIncidentIds.has(option.value)) option.remove();
    }
  }

  if (isManager) {
    const select = document.getElementById('interventionIncident');
    if (select) {
      new MutationObserver(filterPlannerOptions).observe(select, { childList: true });
    }
  }

  async function loadWorkQueue() {
    const incidentTask = isManager ? apiClient.getIncidents() : Promise.resolve([]);
    const interventionTask = canManageInterventions
      ? apiClient.getInterventions()
      : Promise.resolve([]);

    try {
      const [incidentData, interventionData] = await Promise.all([incidentTask, interventionTask]);
      const incidents = listItems(incidentData);
      const interventions = listItems(interventionData);

      if (isManager) {
        validatedIncidentIds.clear();
        incidents.filter(item => item.status === 'validated').forEach(item => {
          validatedIncidentIds.add(String(item.id));
        });
        incidentDataLoaded = true;
        filterPlannerOptions();

        incidentColumn.classList.remove('d-none');
        incidentQueue.replaceChildren();
        const pendingIncidents = incidents.filter(item => item.status === 'created');
        if (!pendingIncidents.length) {
          incidentQueue.textContent = 'Aucun incident à valider.';
        }
        pendingIncidents.forEach(item => {
          const { row, controls, feedback } = createQueueRow(item.title, 'Nouveau signalement');
          controls.append(
            createButton('Valider', 'validate-incident', item.id, 'btn-outline-success'),
            createButton('Rejeter', 'reject-incident', item.id, 'btn-outline-danger'),
          );
          feedback.setAttribute('aria-live', 'polite');
          incidentQueue.appendChild(row);
        });
      }

      if (canManageInterventions) {
        interventionColumn.classList.remove('d-none');
        interventionQueue.replaceChildren();
        const activeInterventions = interventions.filter(item =>
          ['pending', 'assigned', 'in_progress'].includes(item.status),
        );
        if (!activeInterventions.length) {
          interventionQueue.textContent = 'Aucune intervention à traiter.';
        }
        activeInterventions.forEach(item => {
          const statusLabels = {
            pending: 'En attente d’affectation',
            assigned: 'Affectée',
            in_progress: 'En cours',
          };
          const { row, controls, feedback } = createQueueRow(
            item.incident_title,
            statusLabels[item.status],
          );
          if (item.status === 'assigned') {
            controls.append(createButton(
              'Prendre en charge',
              'start-intervention',
              item.id,
              'btn-outline-primary',
            ));
          } else if (item.status === 'in_progress') {
            controls.append(createButton(
              'Clôturer',
              'complete-intervention',
              item.id,
              'btn-primary',
            ));
          }
          feedback.setAttribute('aria-live', 'polite');
          interventionQueue.appendChild(row);
        });
      }

      if (isManager || canManageInterventions) workQueue.classList.remove('d-none');
    } catch (error) {
      workQueue.classList.remove('d-none');
      if (isManager) {
        incidentColumn.classList.remove('d-none');
        incidentQueue.textContent = 'Impossible de charger les incidents.';
      }
      if (canManageInterventions) {
        interventionColumn.classList.remove('d-none');
        interventionQueue.textContent = 'Impossible de charger les interventions.';
      }
    }
  }

  document.addEventListener('click', async event => {
    const button = event.target.closest('button[data-queue-action]');
    if (!button || button.disabled) return;

    const action = button.dataset.queueAction;
    const id = button.dataset.recordId;
    if (action === 'reject-incident' && !window.confirm('Rejeter ce signalement ?')) return;

    const feedback = button.closest('.queue-row').querySelector('.queue-feedback');
    button.disabled = true;
    feedback.textContent = 'Mise à jour…';
    feedback.className = 'queue-feedback small mt-2 d-block text-secondary';

    try {
      if (action === 'validate-incident') {
        await apiClient.updateIncidentStatus(id, 'validated', 'Validé depuis le tableau de bord.');
      } else if (action === 'reject-incident') {
        await apiClient.updateIncidentStatus(id, 'rejected', 'Rejeté depuis le tableau de bord.');
      } else if (action === 'start-intervention') {
        await apiClient.updateInterventionStatus(id, 'in_progress', 'Prise en charge depuis le tableau de bord.');
      } else if (action === 'complete-intervention') {
        await apiClient.updateInterventionStatus(id, 'completed', 'Intervention clôturée depuis le tableau de bord.');
      }
      window.location.reload();
    } catch (error) {
      button.disabled = false;
      feedback.textContent = 'Échec de la mise à jour. Vérifiez le statut et vos autorisations.';
      feedback.className = 'queue-feedback small mt-2 d-block text-danger';
    }
  });

  loadWorkQueue();
})();
