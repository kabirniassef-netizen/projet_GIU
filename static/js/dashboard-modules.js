(() => {
  const moduleDefinitions = {
    users: {
      title: 'Utilisateurs',
      description: 'Comptes enregistrés et rôles attribués.',
      allowedRoles: ['manager', 'admin'],
      load: loadUsers,
    },
    assets: {
      title: 'Patrimoine urbain',
      description: 'Équipements enregistrés et état de fonctionnement.',
      load: loadAssets,
    },
    interventions: {
      title: 'Interventions organisées',
      description: 'Interventions planifiées, agents affectés et avancement.',
      allowedRoles: ['agent', 'manager', 'admin'],
      load: loadInterventions,
    },
    decisions: {
      title: 'Décisions éclairées',
      description: 'Indicateurs et répartition des incidents pour orienter les priorités.',
      allowedRoles: ['decision_maker', 'manager', 'admin'],
      load: loadDecisions,
    },
    reports: {
      title: 'Rapports & KPI',
      description: 'Indicateurs clés et rapports disponibles.',
      allowedRoles: ['decision_maker', 'manager', 'admin'],
      load: loadReports,
    },
  };

  const user = JSON.parse(localStorage.getItem('user_data') || '{}');
  const moduleKey = new URLSearchParams(window.location.search).get('module');
  const definition = moduleDefinitions[moduleKey];
  if (!definition) return;

  const panel = document.getElementById('moduleSection');
  const content = document.getElementById('moduleContent');
  const message = document.getElementById('moduleMessage');
  document.getElementById('dashboardOverview').classList.add('d-none');
  document.getElementById('incidentFormSection').classList.add('d-none');
  panel.classList.remove('d-none');
  document.getElementById('moduleTitle').textContent = definition.title;
  document.getElementById('moduleDescription').textContent = definition.description;

  if (definition.allowedRoles && !definition.allowedRoles.includes(user.role) && !user.is_superuser) {
    message.className = 'alert alert-warning';
    message.textContent = 'Vous n’avez pas les droits nécessaires pour consulter ce module.';
    return;
  }

  message.textContent = 'Chargement des données…';
  message.className = 'small mb-3 text-secondary';
  definition.load()
    .then(() => {
      message.textContent = '';
      message.className = 'small mb-3';
    })
    .catch(error => {
      console.error(`Erreur de chargement du module ${moduleKey}:`, error);
      message.className = 'alert alert-danger';
      message.textContent = 'Impossible de charger ce module. Vérifiez votre connexion et réessayez.';
    });

  function listItems(data) {
    return Array.isArray(data) ? data : (data && Array.isArray(data.results) ? data.results : []);
  }

  function createTable(headers, rows, emptyMessage) {
    if (!rows.length) {
      const empty = document.createElement('p');
      empty.className = 'text-secondary mb-0';
      empty.textContent = emptyMessage;
      return empty;
    }

    const wrapper = document.createElement('div');
    wrapper.className = 'table-responsive';
    const table = document.createElement('table');
    table.className = 'table table-hover align-middle mb-0';
    const head = document.createElement('thead');
    const headerRow = document.createElement('tr');
    headers.forEach(label => {
      const cell = document.createElement('th');
      cell.scope = 'col';
      cell.textContent = label;
      headerRow.appendChild(cell);
    });
    head.appendChild(headerRow);
    table.appendChild(head);

    const body = document.createElement('tbody');
    rows.forEach(row => {
      const tableRow = document.createElement('tr');
      row.forEach(value => {
        const cell = document.createElement('td');
        cell.textContent = value === null || value === undefined || value === '' ? '—' : value;
        tableRow.appendChild(cell);
      });
      body.appendChild(tableRow);
    });
    table.appendChild(body);
    wrapper.appendChild(table);
    return wrapper;
  }

  function createMetrics(metrics) {
    const row = document.createElement('div');
    row.className = 'row g-3 mb-4';
    metrics.forEach(([label, value]) => {
      const column = document.createElement('div');
      column.className = 'col-6 col-lg-3';
      const card = document.createElement('article');
      card.className = 'metric-card h-100';
      const amount = document.createElement('strong');
      amount.textContent = value ?? '—';
      const caption = document.createElement('span');
      caption.textContent = label;
      card.append(amount, caption);
      column.appendChild(card);
      row.appendChild(column);
    });
    content.appendChild(row);
  }

  function formatDate(value) {
    if (!value) return '—';
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('fr-FR');
  }

  async function loadUsers() {
    const users = listItems(await apiClient.getUsers());
    content.replaceChildren(createTable(
      ['Nom', 'Identifiant', 'Courriel', 'Rôle', 'Service', 'État'],
      users.map(item => [
        `${item.first_name || ''} ${item.last_name || ''}`.trim(),
        item.username,
        item.email,
        item.role_display || item.role,
        item.department,
        item.is_active ? 'Actif' : 'Inactif',
      ]),
      'Aucun utilisateur à afficher.',
    ));
  }

  async function loadAssets() {
    const assets = listItems(await apiClient.getAssets());
    content.replaceChildren(createTable(
      ['Code', 'Équipement', 'Type', 'Emplacement', 'État', 'Installation'],
      assets.map(item => [
        item.code,
        item.name,
        item.asset_type_name,
        item.location,
        item.status_display || item.status,
        formatDate(item.installed_date),
      ]),
      'Aucun équipement à afficher.',
    ));
  }

  async function loadInterventions() {
    const [interventionData] = await Promise.all([
      apiClient.getInterventions(),
      user.role === 'manager' || user.role === 'admin' || user.is_superuser
        ? apiClient.getIncidents()
        : Promise.resolve([]),
    ]);
    const interventions = listItems(interventionData);
    const scheduleButton = document.createElement('button');
    scheduleButton.type = 'button';
    scheduleButton.className = 'btn btn-primary mb-3';
    scheduleButton.dataset.bsToggle = 'modal';
    scheduleButton.dataset.bsTarget = '#interventionModal';
    scheduleButton.textContent = 'Planifier une intervention';
    scheduleButton.addEventListener('click', () => {
      const choices = document.getElementById('interventionIncident').options;
      if (choices.length <= 1) {
        document.getElementById('interventionMessage').textContent =
          'Aucun incident validé disponible pour la planification.';
      }
    });
    const table = createTable(
      ['Incident', 'Agent affecté', 'Date prévue', 'Priorité', 'Statut'],
      interventions.map(item => [
        item.incident_title,
        item.assigned_to_username,
        formatDate(item.scheduled_date),
        item.priority_display || item.priority,
        item.status_display || item.status,
      ]),
      'Aucune intervention à afficher.',
    );
    content.replaceChildren(scheduleButton, table);
  }

  async function loadDecisions() {
    const data = await apiClient.request('/reports/reports/generate_dashboard/', {
      method: 'POST',
      body: JSON.stringify({}),
    });
    content.replaceChildren();
    createMetrics([
      ['Incidents déclarés', data.total_incidents],
      ['Résolus', data.resolved_incidents],
      ['Signalés ce mois', data.incidents_this_month],
      ['Interventions terminées', data.completed_interventions],
      ['Interventions en attente', data.pending_interventions],
    ]);
    const categories = data.category_distribution || [];
    const labels = {
      imprudence: 'Imprudence',
      vitesse: 'Vitesse',
      panne: 'Panne',
      mauvaise_visibilite: 'Mauvaise visibilité',
      lighting: 'Éclairage public',
      road: 'Voirie',
      waste: 'Déchets',
      signal: 'Signalisation',
      water: 'Eau',
      tree: 'Arbres',
      bench: 'Mobilier urbain',
      other: 'Autre',
    };
    const distributionRows = categories.map(item => [
      labels[item.category__name] || item.category__name,
      item.count,
    ]);
    const distributionTitle = document.createElement('h3');
    distributionTitle.className = 'h5 mt-4 mb-3';
    distributionTitle.textContent = 'Incidents par catégorie';
    content.append(distributionTitle, createTable(
      ['Catégorie', 'Nombre'],
      distributionRows,
      'Aucune donnée de catégorie disponible.',
    ));
  }

  async function loadReports() {
    const [statistics, reports, metricData] = await Promise.all([
      apiClient.getGlobalStatistics(),
      apiClient.request('/reports/reports/'),
      apiClient.request('/reports/metrics/'),
    ]);
    content.replaceChildren();
    createMetrics([
      ['Incidents', statistics.total_incidents],
      ['Incidents résolus', statistics.resolved_incidents],
      ['Interventions', statistics.total_interventions],
      ['Interventions terminées', statistics.completed_interventions],
      ['Disponibilité du patrimoine', `${statistics.asset_availability_rate}%`],
    ]);

    const latestMetric = listItems(metricData)[0];
    if (latestMetric) {
      const metricHeading = document.createElement('h3');
      metricHeading.className = 'h5 mt-4 mb-3';
      metricHeading.textContent = `Derniers KPI — ${formatDate(latestMetric.date)}`;
      content.appendChild(metricHeading);
      const metricRows = [
        ['Incidents en attente', latestMetric.pending_incidents],
        ['Durée moyenne de résolution', latestMetric.avg_resolution_time],
        ['Coût moyen d’intervention', latestMetric.avg_intervention_cost],
        ['Disponibilité des actifs', `${latestMetric.asset_availability}%`],
      ].map(([label, value]) => [label, value ?? '—']);
      content.append(metricHeading, createTable(
        ['Indicateur', 'Valeur'],
        metricRows,
        'Aucun KPI enregistré.',
      ));
    }

    const reportHeading = document.createElement('h3');
    reportHeading.className = 'h5 mt-4 mb-3';
    reportHeading.textContent = 'Rapports enregistrés';
    const reportsList = listItems(reports);
    content.append(reportHeading, createTable(
      ['Rapport', 'Type', 'Période', 'Créé le'],
      reportsList.map(item => [
        item.title,
        item.report_type_display || item.report_type,
        `${formatDate(item.start_date)} – ${formatDate(item.end_date)}`,
        formatDate(item.created_at),
      ]),
      'Aucun rapport enregistré.',
    ));

    const generator = document.createElement('form');
    generator.className = 'row g-2 align-items-end mt-4';
    generator.innerHTML = '<div class="col-12"><h3 class="h5">Générer un rapport mensuel</h3></div><div class="col-md-4"><label class="form-label" for="reportStartDate">Date de début</label><input class="form-control" id="reportStartDate" name="start_date" type="date" required></div><div class="col-md-4"><label class="form-label" for="reportEndDate">Date de fin</label><input class="form-control" id="reportEndDate" name="end_date" type="date" required></div><div class="col-md-4"><button class="btn btn-primary" type="submit">Générer</button></div><div class="col-12"><p class="small mb-0" id="reportGenerationMessage" role="status" aria-live="polite"></p></div>';
    generator.addEventListener('submit', async event => {
      event.preventDefault();
      const resultMessage = document.getElementById('reportGenerationMessage');
      const formData = new FormData(generator);
      try {
        const result = await apiClient.request('/reports/reports/generate_monthly_report/', {
          method: 'POST',
          body: JSON.stringify({
            start_date: formData.get('start_date'),
            end_date: formData.get('end_date'),
          }),
        });
        resultMessage.className = 'small mb-0 text-success';
        resultMessage.textContent =
          `Rapport calculé : ${result.total_incidents} incident(s), ${result.resolved_incidents} résolu(s), taux de résolution ${Number(result.resolution_rate).toFixed(1)} %.`;
      } catch (error) {
        console.error('Erreur pendant la génération du rapport mensuel :', error);
        resultMessage.className = 'small mb-0 text-danger';
        resultMessage.textContent = 'Impossible de générer le rapport. Vérifiez les dates et vos droits.';
      }
    });
    content.appendChild(generator);
  }
})();
