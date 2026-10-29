// Espace de travail GIU : navigation sans rechargement, vues par rôle, tiroirs de détail.
(() => {
  const {
    h, icon, debounce, listItems, formatDate, timeAgo, formatNumber, formatPercent, formatHours, initials,
    statusPill, priorityPill, rolePill, toast, confirmDialog, formDialog, setBusy, field, select,
    input, textarea, skeleton, emptyState, errorState, barChart, distribution, donut, statCard, copyText,
  } = UI;
  const api = apiClient;

  // ------------------------------------------------------------------ Session
  const readStoredUser = () => {
    try { return JSON.parse(localStorage.getItem('user_data') || '{}'); } catch (error) { return {}; }
  };
  const state = {
    user: readStoredUser(),
    refreshView: null,
    categories: null,
    agents: null,
    assetTypes: null,
    unread: 0,
  };
  const roleOf = user => user.effective_role || (user.is_superuser ? 'admin' : user.role) || 'citizen';
  const role = () => roleOf(state.user);
  const is = (...roles) => roles.includes(role());
  const isManager = () => is('manager', 'admin');
  const isField = () => is('agent', 'manager', 'admin');
  const canReport = () => is('decision_maker', 'manager', 'admin');
  const displayName = user => [user.first_name, user.last_name].filter(Boolean).join(' ') || user.full_name || user.username || 'utilisateur';

  // --------------------------------------------------------------- Navigation
  const ROUTES = {
    overview: { label: 'Tableau de bord', icon: 'gauge-high', roles: null, view: viewOverview },
    incidents: { label: 'Incidents', citizenLabel: 'Mes signalements', icon: 'triangle-exclamation', roles: ['citizen', 'agent', 'manager', 'admin'], view: viewIncidents },
    interventions: { label: 'Interventions', icon: 'helmet-safety', roles: ['agent', 'manager', 'admin'], view: viewInterventions },
    assets: { label: 'Patrimoine urbain', icon: 'building-circle-check', roles: ['agent', 'manager', 'admin', 'decision_maker'], view: viewAssets },
    users: { label: 'Usagers & comptes', icon: 'users', roles: ['manager', 'admin'], view: viewUsers, section: 'Administration' },
    decisions: { label: 'Décisions éclairées', icon: 'chart-pie', roles: ['decision_maker', 'manager', 'admin'], view: viewDecisions, section: 'Pilotage' },
    reports: { label: 'Rapports & KPI', icon: 'chart-column', roles: ['decision_maker', 'manager', 'admin'], view: viewReports },
    profile: { label: 'Mon profil', icon: 'user-gear', roles: null, view: viewProfile, section: 'Compte' },
  };
  const allowed = key => {
    const route = ROUTES[key];
    return route && (!route.roles || route.roles.includes(role()));
  };

  const content = document.getElementById('moduleSection');
  const params = () => new URLSearchParams(window.location.search);

  function renderNav() {
    const nav = document.getElementById('appNav');
    nav.replaceChildren();
    let currentSection = null;
    Object.entries(ROUTES).forEach(([key, route]) => {
      if (!allowed(key)) return;
      if (route.section && route.section !== currentSection) {
        currentSection = route.section;
        nav.appendChild(h('div', { class: 'nav-section' }, route.section));
      }
      const label = role() === 'citizen' && route.citizenLabel ? route.citizenLabel : route.label;
      nav.appendChild(h('a', { href: key === 'overview' ? '/dashboard/' : `/dashboard/?module=${key}`, dataset: { route: key } },
        icon(route.icon), h('span', {}, label),
        h('span', { class: 'nav-badge', dataset: { badgeFor: key }, hidden: true })));
    });
    highlightNav();
  }

  function currentRoute() {
    const key = params().get('module') || 'overview';
    return ROUTES[key] ? key : 'overview';
  }

  function highlightNav() {
    const key = currentRoute();
    document.querySelectorAll('#appNav a').forEach(link => {
      const active = link.dataset.route === key;
      link.classList.toggle('active', active);
      if (active) link.setAttribute('aria-current', 'page'); else link.removeAttribute('aria-current');
    });
  }

  function navigate(key, extra = {}, { replace = false } = {}) {
    const search = new URLSearchParams();
    if (key !== 'overview') search.set('module', key);
    Object.entries(extra).forEach(([name, value]) => { if (value) search.set(name, value); });
    const url = `/dashboard/${search.toString() ? `?${search}` : ''}`;
    window.history[replace ? 'replaceState' : 'pushState']({}, '', url);
    render();
  }

  // Met à jour l'URL (filtres, page) sans recharger la vue.
  function syncUrl(values) {
    const search = params();
    Object.entries(values).forEach(([name, value]) => {
      if (value === '' || value === null || value === undefined || value === 1 && name === 'page') search.delete(name);
      else search.set(name, value);
    });
    window.history.replaceState({}, '', `/dashboard/?${search}`);
  }

  async function render() {
    const key = currentRoute();
    highlightNav();
    state.refreshView = null;
    bootstrap.Offcanvas.getInstance(document.getElementById('appSidebar'))?.hide();
    const route = ROUTES[key];
    document.title = `${route.label} — GIU`;
    content.replaceChildren();
    content.classList.remove('view-enter');
    void content.offsetWidth;
    content.classList.add('view-enter');
    if (!allowed(key)) {
      content.appendChild(emptyState('lock', 'Accès restreint', 'Vous n’avez pas les droits nécessaires pour consulter ce module.',
        h('a', { class: 'btn btn-primary btn-sm', href: '/dashboard/', dataset: { route: 'overview' } }, 'Retour au tableau de bord')));
      return;
    }
    try {
      await route.view(content, params());
    } catch (error) {
      console.error(error);
      content.replaceChildren(errorState(error, render));
    }
  }

  document.addEventListener('click', event => {
    const link = event.target.closest('a[data-route]');
    if (!link || event.metaKey || event.ctrlKey || event.shiftKey || event.button !== 0) return;
    event.preventDefault();
    navigate(link.dataset.route);
  });
  window.addEventListener('popstate', render);

  const afterChange = () => {
    if (state.refreshView) state.refreshView();
    refreshBadges();
  };

  // ------------------------------------------------------------ Composants
  function pageHeader(title, subtitle, actions = [], eyebrow) {
    return h('div', { class: 'page-header' },
      h('div', {}, eyebrow ? h('span', { class: 'eyebrow-label' }, eyebrow) : null, h('h1', {}, title), subtitle ? h('p', {}, subtitle) : null),
      h('div', { class: 'd-flex flex-wrap gap-2' }, actions));
  }

  function panel(title, body, { actions = null, flush = false } = {}) {
    return h('section', { class: 'panel h-100' },
      title ? h('div', { class: 'panel-header' }, h('h2', {}, title), actions) : null,
      h('div', { class: flush ? '' : 'panel-body' }, body));
  }

  function setActiveChip(group, value) {
    group.querySelectorAll('.chip').forEach(chip => {
      const active = chip.dataset.value === String(value ?? '');
      chip.classList.toggle('active', active);
      chip.setAttribute('aria-pressed', String(active));
    });
  }

  function chips(options, active, onChange) {
    const group = h('div', { class: 'chip-group', role: 'group' });
    options.forEach(([value, label, count]) => {
      group.appendChild(h('button', {
        type: 'button', class: 'chip', dataset: { value: String(value) },
        onclick: () => { setActiveChip(group, value); onChange(value); },
      }, label, count !== undefined ? h('span', { class: 'count' }, count) : null));
    });
    setActiveChip(group, active);
    return group;
  }

  function searchField(value, placeholder, onSearch) {
    const searchInput = h('input', { class: 'form-control', type: 'search', placeholder, value: value || '', 'aria-label': placeholder });
    searchInput.addEventListener('input', debounce(() => onSearch(searchInput.value.trim()), 300));
    return h('div', { class: 'search-field' }, icon('magnifying-glass'), searchInput);
  }

  function dataTable(columns, rows, onRowClick) {
    const table = h('table', { class: 'data-table' },
      h('thead', {}, h('tr', {}, columns.map(column => h('th', { scope: 'col', class: column.class || '' }, column.label)))),
      h('tbody', {}, rows.map(row => {
        const tr = h('tr', { tabindex: onRowClick ? '0' : null },
          columns.map(column => h('td', { class: column.class || '', 'data-label': column.mobileLabel === false ? null : column.label }, column.render(row))));
        if (onRowClick) {
          tr.addEventListener('click', event => { if (!event.target.closest('button, a, select')) onRowClick(row); });
          tr.addEventListener('keydown', event => { if (event.key === 'Enter') onRowClick(row); });
        }
        return tr;
      })));
    return h('div', { class: 'table-responsive' }, table);
  }

  function pager(data, page, pageSize, onPage) {
    const count = data.count ?? listItems(data).length;
    const pages = Math.max(1, Math.ceil(count / pageSize));
    const start = count ? (page - 1) * pageSize + 1 : 0;
    const end = Math.min(page * pageSize, count);
    return h('div', { class: 'table-footer' },
      h('span', {}, count ? `${start}–${end} sur ${formatNumber(count)}` : 'Aucun résultat'),
      pages > 1 ? h('div', { class: 'btn-group btn-group-sm' },
        h('button', { type: 'button', class: 'btn btn-light', disabled: page <= 1, onclick: () => onPage(page - 1), 'aria-label': 'Page précédente' }, icon('chevron-left')),
        h('span', { class: 'btn btn-light disabled' }, `${page} / ${pages}`),
        h('button', { type: 'button', class: 'btn btn-light', disabled: page >= pages, onclick: () => onPage(page + 1), 'aria-label': 'Page suivante' }, icon('chevron-right'))) : null);
  }

  // Liste paginée générique : barre d'outils + tableau + pagination, rechargée sans clignotement.
  function listView({ toolbar, load, columns, onRowClick, empty, pageSize = 20 }) {
    const body = h('div', {}, skeleton(6));
    const wrapper = h('section', { class: 'panel' }, toolbar, body);
    let page = Number(params().get('page')) || 1;
    let requestId = 0;
    async function refresh(resetPage = false) {
      if (resetPage) page = 1;
      syncUrl({ page });
      const current = ++requestId;
      body.style.opacity = '.55';
      try {
        const data = await load(page, pageSize);
        if (current !== requestId) return;
        const rows = listItems(data);
        body.replaceChildren(rows.length ? dataTable(columns, rows, onRowClick) : empty(), pager(data, page, pageSize, next => { page = next; refresh(); content.scrollIntoView({ behavior: 'smooth' }); }));
      } catch (error) {
        if (current !== requestId) return;
        if (error.status === 404 && page > 1) { page = 1; refresh(); return; }
        body.replaceChildren(errorState(error, () => refresh()));
      } finally {
        if (current === requestId) body.style.opacity = '';
      }
    }
    return { element: wrapper, refresh };
  }

  // ------------------------------------------------------------ Tiroir
  const drawerElement = document.getElementById('detailDrawer');
  const drawer = new bootstrap.Offcanvas(drawerElement);
  const drawerBody = document.getElementById('detailDrawerBody');
  let drawerReload = null;

  function openDrawer(kicker, title, loader) {
    document.getElementById('detailDrawerKicker').textContent = kicker;
    document.getElementById('detailDrawerTitle').textContent = title;
    drawerBody.replaceChildren(skeleton(8));
    drawer.show();
    drawerReload = async () => {
      try {
        await loader(drawerBody);
      } catch (error) {
        drawerBody.replaceChildren(errorState(error, drawerReload));
      }
    };
    drawerReload();
  }

  const setDrawerTitle = title => { document.getElementById('detailDrawerTitle').textContent = title; };
  const section = (title, ...children) => h('div', { class: 'detail-section' }, title ? h('h3', {}, title) : null, ...children);
  const details = pairs => h('dl', { class: 'detail-grid mb-0' }, pairs.filter(Boolean).map(([term, value]) =>
    h('div', {}, h('dt', {}, term), h('dd', {}, value === null || value === undefined || value === '' ? '—' : value))));

  // Exécute une action avec retour visuel, puis rafraîchit tiroir et liste.
  async function runAction(button, action, successMessage) {
    setBusy(button, true);
    try {
      const result = await action();
      if (successMessage) toast(successMessage);
      afterChange();
      if (drawerReload && drawerElement.classList.contains('show')) drawerReload();
      return result;
    } catch (error) {
      toast(error.message, 'error');
      return null;
    } finally {
      setBusy(button, false);
    }
  }

  function timeline(updates, { photos = false } = {}) {
    if (!updates || !updates.length) return h('p', { class: 'text-secondary small mb-0' }, 'Aucun historique.');
    return h('ol', { class: 'timeline' }, updates.map(update => h('li', {},
      h('div', { class: 'd-flex flex-wrap align-items-center gap-2' }, statusPill(update.status, update.status_display),
        h('span', { class: 'meta' }, `${formatDate(update.updated_at, true)} · ${update.updated_by_name || update.updated_by_username || 'Système'}`)),
      update.comment ? h('p', { class: 'mb-0 mt-1 small' }, update.comment) : null,
      photos && update.photo ? h('a', { href: update.photo, target: '_blank', rel: 'noopener' }, h('img', { src: update.photo, alt: 'Photo du compte rendu', loading: 'lazy' })) : null)));
  }

  const INCIDENT_STEPS = [['created', 'Reçu'], ['validated', 'Validé'], ['planned', 'Planifié'], ['in_progress', 'En cours'], ['resolved', 'Résolu']];
  function incidentStepper(status) {
    if (status === 'rejected') {
      return h('ol', { class: 'stepper rejected' }, h('li', { class: 'done' }, 'Reçu'), h('li', { class: 'current' }, 'Rejeté'));
    }
    const index = INCIDENT_STEPS.findIndex(([key]) => key === status);
    return h('ol', { class: 'stepper', 'aria-label': 'Avancement' }, INCIDENT_STEPS.map(([key, label], position) =>
      h('li', { class: position < index || status === 'resolved' ? 'done' : position === index ? 'current' : '' }, label)));
  }

  // --------------------------------------------------- Données de référence
  async function categories() {
    if (!state.categories) state.categories = listItems(await api.getCategories());
    return state.categories;
  }
  async function agents() {
    if (!state.agents) state.agents = listItems(await api.getUsers({ role: 'agent', is_active: 'true', page_size: 200 }));
    return state.agents;
  }
  async function assetTypes() {
    if (!state.assetTypes) state.assetTypes = listItems(await api.getAssetTypes());
    return state.assetTypes;
  }

  const localInputValue = date => {
    const pad = value => String(value).padStart(2, '0');
    return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
  };
  const PRIORITY_OPTIONS = [['low', 'Basse'], ['medium', 'Moyenne'], ['high', 'Haute'], ['urgent', 'Urgente']];
  const isOverdue = item => ['pending', 'assigned', 'in_progress'].includes(item.status) && new Date(item.scheduled_date) < new Date();

  // ================================================================ VUES

  // ---------------------------------------------------------- Tableau de bord
  async function viewOverview(root) {
    const now = new Date();
    const hour = now.getHours();
    const greeting = hour < 5 || hour >= 18 ? 'Bonsoir' : 'Bonjour';
    const subtitles = {
      citizen: 'Suivez l’avancement de vos signalements.',
      agent: 'Vos interventions du moment, en un coup d’œil.',
      manager: 'Ce qui demande votre attention aujourd’hui.',
      admin: 'Ce qui demande votre attention aujourd’hui.',
      decision_maker: 'Les indicateurs clés de votre territoire.',
    };
    const actions = [];
    if (isManager()) actions.push(h('button', { type: 'button', class: 'btn btn-light', onclick: () => planDialog() }, icon('calendar-plus', 'me-2'), 'Planifier une intervention'));
    actions.push(h('button', { type: 'button', class: 'btn btn-primary', onclick: openReportModal }, icon('plus', 'me-2'), 'Signaler'));
    root.append(pageHeader(`${greeting}, ${state.user.first_name || displayName(state.user)}`, subtitles[role()],
      actions, new Intl.DateTimeFormat('fr-FR', { weekday: 'long', day: 'numeric', month: 'long' }).format(now)));

    const stats = h('div', { class: 'stat-grid' }, Array.from({ length: 4 }, () => h('div', { class: 'stat-card' }, skeleton(2))));
    const charts = h('div', { class: 'row g-3 mb-4' });
    const queues = h('div', { class: 'row g-3' });
    root.append(stats, charts, queues);

    async function load() {
      const summary = await api.getDashboardSummary();
      const incidents = summary.incidents;
      const interventions = summary.interventions;
      const cards = {
        citizen: [
          { label: 'Mes signalements', value: incidents.total, iconName: 'flag', onClick: () => navigate('incidents') },
          { label: 'En cours de traitement', value: incidents.open, iconName: 'spinner', tone: 'warning', onClick: () => navigate('incidents', { status: 'created,validated,planned,in_progress' }) },
          { label: 'Résolus', value: incidents.resolved, iconName: 'circle-check', tone: 'success', onClick: () => navigate('incidents', { status: 'resolved' }) },
          { label: 'Taux de résolution', value: formatPercent(incidents.resolution_rate), iconName: 'chart-line', tone: 'info' },
        ],
        agent: [
          { label: 'Interventions actives', value: interventions.active, iconName: 'screwdriver-wrench', onClick: () => navigate('interventions') },
          { label: 'En retard', value: interventions.overdue, iconName: 'clock', tone: interventions.overdue ? 'danger' : 'neutral', onClick: () => navigate('interventions') },
          { label: 'Prévues sous 7 jours', value: interventions.next_7_days, iconName: 'calendar-week', tone: 'info' },
          { label: 'Terminées', value: interventions.completed, iconName: 'circle-check', tone: 'success', onClick: () => navigate('interventions', { status: 'completed' }) },
        ],
        manager: [
          { label: 'À valider', value: incidents.awaiting_validation, iconName: 'inbox', tone: incidents.awaiting_validation ? 'warning' : 'neutral', hint: 'Nouveaux signalements', onClick: () => navigate('incidents', { status: 'created' }) },
          { label: 'À planifier', value: incidents.awaiting_planning, iconName: 'calendar-plus', tone: 'primary', hint: 'Incidents validés', onClick: () => navigate('incidents', { status: 'validated' }) },
          { label: 'Urgences ouvertes', value: incidents.urgent_open, iconName: 'fire-flame-curved', tone: incidents.urgent_open ? 'danger' : 'neutral', onClick: () => navigate('incidents', { priority: 'high,urgent' }) },
          { label: 'Interventions en retard', value: interventions.overdue, iconName: 'clock', tone: interventions.overdue ? 'danger' : 'neutral', onClick: () => navigate('interventions') },
          { label: 'Taux de résolution', value: formatPercent(incidents.resolution_rate), iconName: 'chart-line', tone: 'success', hint: `Délai moyen ${formatHours(incidents.avg_resolution_hours)}` },
          { label: 'Disponibilité du patrimoine', value: formatPercent(summary.assets.availability_rate), iconName: 'building-circle-check', tone: 'info', onClick: () => navigate('assets') },
        ],
        decision_maker: [
          { label: 'Incidents (30 jours)', value: incidents.last_30_days, iconName: 'triangle-exclamation', tone: 'warning' },
          { label: 'Taux de résolution', value: formatPercent(incidents.resolution_rate), iconName: 'chart-line', tone: 'success' },
          { label: 'Délai moyen de résolution', value: formatHours(incidents.avg_resolution_hours), iconName: 'stopwatch', tone: 'info' },
          { label: 'Disponibilité du patrimoine', value: formatPercent(summary.assets.availability_rate), iconName: 'building-circle-check', tone: 'primary', onClick: () => navigate('assets') },
        ],
      };
      cards.admin = cards.manager;
      stats.replaceChildren(...cards[role()].map(statCard));

      charts.replaceChildren(
        h('div', { class: 'col-lg-8' }, panel('Signalements des 30 derniers jours', barChart(incidents.trend), {
          actions: h('span', { class: 'text-secondary small' }, `${incidents.last_30_days} au total`),
        })),
        h('div', { class: 'col-lg-4' }, panel('Répartition par statut', distribution(incidents.by_status, { emptyText: 'Aucun signalement pour le moment.' }))),
      );

      queues.replaceChildren();
      if (isManager()) {
        queues.append(
          h('div', { class: 'col-lg-6' }, await incidentQueue('Nouveaux signalements à valider', { status: 'created' }, 'inbox')),
          h('div', { class: 'col-lg-6' }, await incidentQueue('Incidents validés à planifier', { status: 'validated' }, 'calendar-plus')),
        );
      } else if (is('agent')) {
        queues.append(h('div', { class: 'col-12' }, await interventionQueue()));
      } else if (is('citizen')) {
        queues.append(h('div', { class: 'col-12' }, await citizenRecent()));
      } else {
        queues.append(
          h('div', { class: 'col-lg-6' }, panel('Catégories les plus signalées', distribution(incidents.by_category.slice(0, 6)))),
          h('div', { class: 'col-lg-6' }, panel('Priorités', distribution(incidents.by_priority))),
        );
      }
    }
    state.refreshView = () => load().catch(error => toast(error.message, 'error'));
    await load();
  }

  async function incidentQueue(title, filters, iconName) {
    const data = await api.getIncidents({ ...filters, page_size: 6, ordering: '-created_at' });
    const items = listItems(data);
    const list = h('div', {});
    const more = (data.count || 0) > items.length
      ? h('a', { href: '#', class: 'small text-decoration-none', onclick: event => { event.preventDefault(); navigate('incidents', filters); } }, `Voir les ${data.count}`)
      : null;
    if (!items.length) list.appendChild(emptyState(iconName, 'Tout est à jour', 'Aucun élément en attente.'));
    items.forEach(incident => {
      const row = h('div', { class: 'queue-item' },
        h('div', { class: 'queue-main', onclick: () => openIncident(incident.id) },
          h('span', { class: 'cell-title' }, incident.title),
          h('span', { class: 'cell-sub' }, `${incident.category_display || ''} · ${incident.commune || 'Lieu non précisé'} · ${timeAgo(incident.created_at)}`)),
        priorityPill(incident.priority, incident.priority_display));
      const actions = h('div', { class: 'queue-actions' });
      if (incident.status === 'created') {
        actions.append(
          h('button', { type: 'button', class: 'btn btn-sm btn-outline-success', title: 'Valider', 'aria-label': `Valider ${incident.title}`,
            onclick: async event => {
              const ok = await runAction(event.currentTarget, () => api.updateIncidentStatus(incident.id, 'validated', 'Validé depuis le tableau de bord.'), 'Signalement validé.');
              if (ok) row.classList.add('leaving');
            } }, icon('check')),
          h('button', { type: 'button', class: 'btn btn-sm btn-outline-danger', title: 'Rejeter', 'aria-label': `Rejeter ${incident.title}`,
            onclick: () => rejectIncident(incident) }, icon('xmark')));
      } else if (incident.status === 'validated') {
        actions.append(h('button', { type: 'button', class: 'btn btn-sm btn-primary', onclick: () => planDialog(incident) }, icon('calendar-plus', 'me-1'), 'Planifier'));
      }
      row.appendChild(actions);
      list.appendChild(row);
    });
    return panel(title, list, { flush: true, actions: more });
  }

  async function interventionQueue() {
    const items = listItems(await api.getInterventions({ active: 'true', page_size: 10, ordering: 'scheduled_date' }));
    const list = h('div', {});
    if (!items.length) list.appendChild(emptyState('mug-hot', 'Aucune intervention en cours', 'Les nouvelles affectations apparaîtront ici.'));
    items.forEach(item => {
      list.appendChild(h('div', { class: 'queue-item' },
        h('div', { class: 'queue-main', onclick: () => openIntervention(item.id) },
          h('span', { class: 'cell-title' }, item.incident_title),
          h('span', { class: 'cell-sub' }, `${formatDate(item.scheduled_date, true)} · ${item.incident_location || 'Lieu non précisé'}`)),
        isOverdue(item) ? h('span', { class: 'pill pill-danger' }, 'En retard') : statusPill(item.status, item.status_display),
        h('div', { class: 'queue-actions' }, interventionQuickAction(item))));
    });
    return panel('Mes interventions', list, { flush: true });
  }

  async function citizenRecent() {
    const items = listItems(await api.getIncidents({ page_size: 5 }));
    if (!items.length) {
      return panel('Mes derniers signalements', emptyState('bullhorn', 'Aucun signalement', 'Vous avez remarqué un problème dans votre ville ?',
        h('button', { type: 'button', class: 'btn btn-primary btn-sm', onclick: openReportModal }, 'Faire un signalement')));
    }
    return panel('Mes derniers signalements', h('div', {}, items.map(item => h('div', { class: 'queue-item' },
      h('div', { class: 'queue-main', onclick: () => openIncident(item.id) },
        h('div', { class: 'd-flex flex-wrap justify-content-between gap-2 mb-2' },
          h('span', { class: 'cell-title' }, item.title), h('span', { class: 'code-chip' }, item.tracking_code)),
        incidentStepper(item.status))))), { flush: true });
  }

  // ---------------------------------------------------------------- Incidents
  async function viewIncidents(root, query) {
    const filters = {
      search: query.get('q') || '',
      status: query.get('status') || '',
      priority: query.get('priority') || '',
      category: query.get('category') || '',
    };
    const actions = [];
    if (canReport()) {
      actions.push(h('button', { type: 'button', class: 'btn btn-light', onclick: event => runAction(event.currentTarget, () => api.exportIncidents({ ...filters, search: filters.search }), 'Export téléchargé.') }, icon('file-csv', 'me-2'), 'Exporter'));
    }
    if (isManager()) actions.push(h('button', { type: 'button', class: 'btn btn-light', onclick: () => planDialog() }, icon('calendar-plus', 'me-2'), 'Planifier'));
    actions.push(h('button', { type: 'button', class: 'btn btn-primary', onclick: openReportModal }, icon('plus', 'me-2'), 'Signaler'));
    root.append(pageHeader(is('citizen') ? 'Mes signalements' : 'Incidents',
      is('citizen') ? 'Retrouvez chaque signalement et son avancement.' : is('agent') ? 'Incidents liés à vos interventions.' : 'Validez, priorisez et planifiez les signalements.', actions));

    const categoryOptions = [['', 'Toutes les catégories'], ...(await categories()).map(item => [item.id, item.name_display || item.name])];
    const categorySelect = select('category', categoryOptions, filters.category, { 'aria-label': 'Catégorie' });
    const prioritySelect = select('priority', [['', 'Toutes priorités'], ['high,urgent', 'Haute et urgente'], ...PRIORITY_OPTIONS], filters.priority, { 'aria-label': 'Priorité' });
    const toolbar = h('div', { class: 'toolbar' },
      searchField(filters.search, 'Titre, lieu, code GIU-…', value => { filters.search = value; syncUrl({ q: value }); list.refresh(true); }),
      chips([
        ['', 'Tous'], ['created', 'Nouveaux'], ['validated', 'Validés'], ['planned', 'Planifiés'],
        ['in_progress', 'En cours'], ['resolved', 'Résolus'], ['rejected', 'Rejetés'],
      ], filters.status, value => { filters.status = value; syncUrl({ status: value }); list.refresh(true); }),
      h('div', { class: 'd-flex gap-2 ms-auto flex-wrap' }, prioritySelect, categorySelect));
    prioritySelect.addEventListener('change', () => { filters.priority = prioritySelect.value; syncUrl({ priority: filters.priority }); list.refresh(true); });
    categorySelect.addEventListener('change', () => { filters.category = categorySelect.value; syncUrl({ category: filters.category }); list.refresh(true); });

    const list = listView({
      toolbar,
      load: (page, pageSize) => api.getIncidents({ ...filters, page, page_size: pageSize }),
      onRowClick: row => openIncident(row.id),
      empty: () => emptyState('magnifying-glass', 'Aucun incident trouvé', 'Modifiez les filtres ou la recherche.'),
      columns: [
        { label: 'Incident', mobileLabel: false, render: row => h('div', {}, h('span', { class: 'cell-title' }, row.title), h('span', { class: 'cell-sub' }, `${row.tracking_code} · ${row.description}`)) },
        { label: 'Catégorie', class: 'hide-mobile', render: row => row.category_display || '—' },
        { label: 'Localisation', render: row => row.commune || row.address || '—' },
        { label: 'Priorité', render: row => priorityPill(row.priority, row.priority_display) },
        { label: 'Statut', render: row => statusPill(row.status, row.status_display) },
        { label: 'Signalé', class: 'text-nowrap', render: row => h('span', { title: formatDate(row.created_at, true) }, timeAgo(row.created_at)) },
      ],
    });
    root.appendChild(list.element);
    state.refreshView = () => list.refresh();
    await list.refresh();
  }

  function openIncident(id) {
    openDrawer(`Incident #${id}`, 'Chargement…', async body => {
      const incident = await api.getIncident(id);
      setDrawerTitle(incident.title);
      const parts = [];
      if (incident.photo) parts.push(h('a', { href: incident.photo, target: '_blank', rel: 'noopener' }, h('img', { class: 'detail-photo mb-3', src: incident.photo, alt: 'Photo du signalement' })));
      parts.push(h('div', { class: 'd-flex flex-wrap gap-2 mb-3' }, statusPill(incident.status, incident.status_display), priorityPill(incident.priority, incident.priority_display), h('span', { class: 'pill pill-neutral' }, incident.category_display)));
      parts.push(incidentStepper(incident.status));

      const actionBar = h('div', { class: 'action-bar' });
      if (isManager()) {
        if (incident.status === 'created') {
          actionBar.append(
            h('button', { type: 'button', class: 'btn btn-success', onclick: event => runAction(event.currentTarget, () => api.updateIncidentStatus(id, 'validated', 'Signalement validé.'), 'Signalement validé.') }, icon('check', 'me-2'), 'Valider'),
            h('button', { type: 'button', class: 'btn btn-outline-danger', onclick: () => rejectIncident(incident) }, icon('xmark', 'me-2'), 'Rejeter'));
        }
        if (incident.status === 'validated') {
          actionBar.append(h('button', { type: 'button', class: 'btn btn-primary', onclick: () => planDialog(incident) }, icon('calendar-plus', 'me-2'), 'Planifier une intervention'));
        }
        actionBar.append(
          h('button', { type: 'button', class: 'btn btn-light', onclick: () => editIncident(incident) }, icon('pen', 'me-2'), 'Modifier'),
          h('button', { type: 'button', class: 'btn btn-light text-danger', 'aria-label': 'Supprimer le signalement', title: 'Supprimer le signalement', onclick: () => deleteIncident(incident) }, icon('trash')));
      }
      if (actionBar.children.length) parts.push(h('div', { class: 'mt-3' }, actionBar));

      parts.push(section('Description', h('p', { class: 'mb-0', style: { whiteSpace: 'pre-line' } }, incident.description)));
      parts.push(section('Informations', details([
        ['Code de suivi', h('span', { class: 'd-inline-flex align-items-center gap-2' }, h('span', { class: 'code-chip' }, incident.tracking_code),
          h('button', { type: 'button', class: 'btn btn-sm btn-link p-0', 'aria-label': 'Copier le code', onclick: () => copyText(incident.tracking_code) }, icon('copy')))],
        ['Signalé par', incident.reporter_username || 'Citoyen anonyme'],
        ['Créé', formatDate(incident.created_at, true)],
        ['Mis à jour', timeAgo(incident.updated_at)],
        ['Adresse', incident.address],
        ['Commune', incident.commune],
        ['Département', incident.department],
        ['Région', incident.region],
      ])));
      if (incident.intervention) {
        const intervention = incident.intervention;
        parts.push(section('Intervention',
          h('div', { class: 'd-flex justify-content-between align-items-center gap-2' },
            h('div', {}, statusPill(intervention.status, intervention.status_display),
              h('div', { class: 'small text-secondary mt-1' }, `${intervention.assigned_to_name || 'Non affectée'} · ${formatDate(intervention.scheduled_date, true)}`)),
            isField() ? h('button', { type: 'button', class: 'btn btn-sm btn-light', onclick: () => openIntervention(intervention.id) }, 'Ouvrir', icon('arrow-right', 'ms-1')) : null)));
      }
      if (isField()) {
        const commentInput = textarea('comment', { rows: 2, placeholder: 'Ajouter une note de suivi…', required: true, maxlength: 2000 });
        const commentButton = h('button', { type: 'submit', class: 'btn btn-sm btn-primary mt-2' }, 'Ajouter la note');
        parts.push(section('Note interne', h('form', {
          onsubmit: async event => {
            event.preventDefault();
            if (!commentInput.value.trim()) return;
            const ok = await runAction(commentButton, () => api.commentIncident(id, commentInput.value.trim()), 'Note ajoutée.');
            if (ok) commentInput.value = '';
          },
        }, commentInput, commentButton)));
      }
      parts.push(section('Historique', timeline(incident.updates)));
      body.replaceChildren(...parts);
    });
  }

  async function rejectIncident(incident) {
    const reason = textarea('comment', { rows: 3, placeholder: 'Ex. doublon, hors périmètre, informations insuffisantes…' });
    const done = await formDialog({
      title: 'Rejeter le signalement',
      tone: 'danger',
      confirmLabel: 'Rejeter',
      fields: h('div', {}, h('p', {}, `« ${incident.title} » sera clôturé sans intervention.`), field('Motif (communiqué dans l’historique)', reason)),
      onSubmit: data => api.updateIncidentStatus(incident.id, 'rejected', data.get('comment') || 'Signalement rejeté.'),
    });
    if (done) {
      toast('Signalement rejeté.');
      afterChange();
      if (drawerElement.classList.contains('show')) drawerReload();
    }
  }

  async function editIncident(incident) {
    const categoryOptions = (await categories()).map(item => [item.id, item.name_display || item.name]);
    const done = await formDialog({
      title: 'Modifier le signalement',
      size: 'modal-lg',
      fields: h('div', { class: 'row g-3' },
        field('Titre', input('title', { value: incident.title, required: true, maxlength: 200 }), { col: 'col-md-8' }),
        field('Priorité', select('priority', PRIORITY_OPTIONS, incident.priority), { col: 'col-md-4' }),
        field('Catégorie', select('category', categoryOptions, incident.category), { col: 'col-md-6' }),
        field('Adresse', input('address', { value: incident.address, maxlength: 300 }), { col: 'col-md-6' }),
        field('Région', input('region', { value: incident.region, maxlength: 100 }), { col: 'col-md-4' }),
        field('Département', input('department', { value: incident.department, maxlength: 100 }), { col: 'col-md-4' }),
        field('Commune', input('commune', { value: incident.commune, maxlength: 100 }), { col: 'col-md-4' }),
        field('Description', textarea('description', { value: incident.description, rows: 4, required: true }))),
      onSubmit: data => api.updateIncident(incident.id, Object.fromEntries(data)),
    });
    if (done) {
      toast('Signalement mis à jour.');
      afterChange();
      drawerReload();
    }
  }

  async function deleteIncident(incident) {
    const confirmed = await confirmDialog('Supprimer le signalement ?',
      `« ${incident.title} » et son historique (y compris les interventions liées) seront définitivement supprimés.`,
      { confirmLabel: 'Supprimer définitivement', tone: 'danger' });
    if (!confirmed) return;
    try {
      await api.deleteIncident(incident.id);
      drawer.hide();
      toast('Signalement supprimé.');
      afterChange();
    } catch (error) {
      toast(error.message, 'error');
    }
  }

  // ----------------------------------------------------- Planification
  async function planDialog(incident = null) {
    let incidentOptions;
    if (incident) {
      incidentOptions = [[incident.id, incident.title]];
    } else {
      const validated = listItems(await api.getIncidents({ status: 'validated', page_size: 200 }));
      if (!validated.length) {
        toast('Aucun incident validé à planifier. Validez d’abord un signalement.', 'info');
        return;
      }
      incidentOptions = [['', 'Choisir un incident validé'], ...validated.map(item => [item.id, `${item.title} — ${item.commune || item.tracking_code}`])];
    }
    const agentList = await agents();
    if (!agentList.length) {
      toast('Aucun agent technique actif. Créez un compte agent dans « Usagers & comptes ».', 'warning');
      return;
    }
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(9, 0, 0, 0);
    const done = await formDialog({
      title: 'Planifier une intervention',
      confirmLabel: 'Planifier',
      fields: h('div', { class: 'row g-3' },
        field('Incident', select('incident', incidentOptions, incident ? incident.id : '', { required: true })),
        field('Agent technique', select('assigned_to', [['', 'Choisir un agent'], ...agentList.map(agent => [agent.id, `${displayName(agent)}${agent.department ? ` · ${agent.department}` : ''}`])], '', { required: true })),
        field('Date et heure', input('scheduled_date', { type: 'datetime-local', required: true, value: localInputValue(tomorrow) }), { col: 'col-md-7' }),
        field('Durée estimée (min)', input('estimated_duration', { type: 'number', min: 5, step: 5, value: 60, required: true }), { col: 'col-md-5' }),
        field('Priorité', select('priority', PRIORITY_OPTIONS, incident ? incident.priority : 'medium')),
        field('Consignes pour l’agent', textarea('notes', { rows: 2, placeholder: 'Matériel, accès, précautions…' }))),
      onSubmit: data => api.createIntervention({
        incident: data.get('incident'),
        assigned_to: data.get('assigned_to'),
        scheduled_date: new Date(data.get('scheduled_date')).toISOString(),
        estimated_duration: Number(data.get('estimated_duration')),
        priority: data.get('priority'),
        notes: data.get('notes'),
      }),
    });
    if (done) {
      toast('Intervention planifiée et agent notifié.');
      afterChange();
      if (drawerElement.classList.contains('show')) drawerReload();
    }
  }

  // ------------------------------------------------------------ Interventions
  function interventionQuickAction(item) {
    if (!isField()) return null;
    if (['pending', 'assigned'].includes(item.status)) {
      return h('button', { type: 'button', class: 'btn btn-sm btn-outline-primary', onclick: event => runAction(event.currentTarget, () => api.updateInterventionStatus(item.id, 'in_progress', 'Prise en charge.'), 'Intervention démarrée.') }, icon('play', 'me-1'), 'Démarrer');
    }
    if (item.status === 'in_progress') {
      return h('button', { type: 'button', class: 'btn btn-sm btn-success', onclick: () => completeIntervention(item) }, icon('flag-checkered', 'me-1'), 'Terminer');
    }
    return null;
  }

  async function viewInterventions(root, query) {
    const filters = {
      search: query.get('q') || '',
      status: query.get('status') || 'active',
      assigned_to: query.get('assigned_to') || '',
    };
    const actions = isManager() ? [h('button', { type: 'button', class: 'btn btn-primary', onclick: () => planDialog() }, icon('calendar-plus', 'me-2'), 'Planifier une intervention')] : [];
    root.append(pageHeader(is('agent') ? 'Mes interventions' : 'Interventions', is('agent') ? 'Démarrez, documentez et clôturez vos missions.' : 'Planification, affectation et suivi des équipes terrain.', actions));

    const tools = [
      searchField(filters.search, 'Incident, commune, agent…', value => { filters.search = value; syncUrl({ q: value }); list.refresh(true); }),
      chips([['active', 'Actives'], ['pending', 'En attente'], ['assigned', 'Assignées'], ['in_progress', 'En cours'], ['completed', 'Terminées'], ['cancelled', 'Annulées'], ['all', 'Toutes']],
        filters.status, value => { filters.status = value; syncUrl({ status: value === 'active' ? '' : value }); list.refresh(true); }),
    ];
    if (isManager()) {
      const agentSelect = select('assigned_to', [['', 'Tous les agents'], ...(await agents()).map(agent => [agent.id, displayName(agent)])], filters.assigned_to, { 'aria-label': 'Agent' });
      agentSelect.addEventListener('change', () => { filters.assigned_to = agentSelect.value; syncUrl({ assigned_to: agentSelect.value }); list.refresh(true); });
      tools.push(h('div', { class: 'ms-auto' }, agentSelect));
    }
    const list = listView({
      toolbar: h('div', { class: 'toolbar' }, tools),
      load: (page, pageSize) => api.getInterventions({
        search: filters.search,
        assigned_to: filters.assigned_to,
        active: filters.status === 'active' ? 'true' : '',
        status: ['active', 'all'].includes(filters.status) ? '' : filters.status,
        ordering: filters.status === 'active' ? 'scheduled_date' : '-scheduled_date',
        page, page_size: pageSize,
      }),
      onRowClick: row => openIntervention(row.id),
      empty: () => emptyState('helmet-safety', 'Aucune intervention', filters.status === 'active' ? 'Aucune intervention en cours.' : 'Aucun résultat pour ces filtres.'),
      columns: [
        { label: 'Intervention', mobileLabel: false, render: row => h('div', {}, h('span', { class: 'cell-title' }, row.incident_title), h('span', { class: 'cell-sub' }, row.incident_location || '—')) },
        { label: 'Agent', render: row => row.assigned_to_name ? h('span', { class: 'd-inline-flex align-items-center gap-2' }, h('span', { class: 'avatar avatar-sm' }, initials(row.assigned_to_name)), row.assigned_to_name) : h('span', { class: 'text-secondary' }, 'Non affectée') },
        { label: 'Prévue', class: 'text-nowrap', render: row => h('div', {}, formatDate(row.scheduled_date, true), isOverdue(row) ? h('span', { class: 'pill pill-danger ms-2' }, 'En retard') : null) },
        { label: 'Priorité', render: row => priorityPill(row.priority, row.priority_display) },
        { label: 'Statut', render: row => statusPill(row.status, row.status_display) },
        { label: '', mobileLabel: false, class: 'text-end', render: row => interventionQuickAction(row) || '' },
      ],
    });
    root.appendChild(list.element);
    state.refreshView = () => list.refresh();
    await list.refresh();
  }

  function openIntervention(id) {
    openDrawer(`Intervention #${id}`, 'Chargement…', async body => {
      const item = await api.getIntervention(id);
      setDrawerTitle(item.incident_title);
      const steps = [['assigned', 'Planifiée'], ['in_progress', 'En cours'], ['completed', 'Terminée']];
      const position = item.status === 'pending' ? 0 : steps.findIndex(([key]) => key === item.status);
      const stepper = item.status === 'cancelled'
        ? h('ol', { class: 'stepper rejected' }, h('li', { class: 'done' }, 'Planifiée'), h('li', { class: 'current' }, 'Annulée'))
        : h('ol', { class: 'stepper' }, steps.map(([, label], index) => h('li', { class: index < position || item.status === 'completed' ? 'done' : index === position ? 'current' : '' }, label)));

      const actionBar = h('div', { class: 'action-bar' });
      const quick = interventionQuickAction(item);
      if (quick) actionBar.appendChild(quick);
      if (isManager() && ['pending', 'assigned', 'in_progress'].includes(item.status)) {
        actionBar.append(
          h('button', { type: 'button', class: 'btn btn-sm btn-light', onclick: () => reassignIntervention(item) }, icon('user-pen', 'me-1'), 'Réaffecter / replanifier'),
          h('button', { type: 'button', class: 'btn btn-sm btn-outline-danger', onclick: () => cancelIntervention(item) }, icon('ban', 'me-1'), 'Annuler'));
      }
      body.replaceChildren(
        h('div', { class: 'd-flex flex-wrap gap-2 mb-3' }, statusPill(item.status, item.status_display), priorityPill(item.priority, item.priority_display), isOverdue(item) ? h('span', { class: 'pill pill-danger' }, 'En retard') : null),
        stepper,
        actionBar.children.length ? h('div', { class: 'mt-3' }, actionBar) : '',
        section('Mission', details([
          ['Agent', item.assigned_to_name || 'Non affectée'],
          ['Date prévue', formatDate(item.scheduled_date, true)],
          ['Durée estimée', `${item.estimated_duration} min`],
          ['Lieu', item.incident_location],
          ['Terminée le', item.completed_date ? formatDate(item.completed_date, true) : null],
          ['Créée', formatDate(item.created_at, true)],
        ]), item.notes ? h('p', { class: 'small mt-3 mb-0 p-2 rounded', style: { background: 'var(--app-surface-2)', whiteSpace: 'pre-line' } }, icon('note-sticky', 'me-2 text-secondary'), item.notes) : null,
        h('button', { type: 'button', class: 'btn btn-sm btn-light mt-3', onclick: () => openIncident(item.incident) }, icon('triangle-exclamation', 'me-1'), 'Voir l’incident')),
        section('Comptes rendus', timeline(item.updates, { photos: true })));
    });
  }

  async function completeIntervention(item) {
    const photo = h('input', { class: 'form-control', type: 'file', name: 'photo', accept: 'image/*' });
    const done = await formDialog({
      title: 'Clôturer l’intervention',
      tone: 'success',
      confirmLabel: 'Clôturer',
      fields: h('div', { class: 'row g-3' },
        h('p', { class: 'col-12 mb-0 text-secondary' }, item.incident_title),
        field('Compte rendu', textarea('comment', { rows: 3, required: true, placeholder: 'Travaux réalisés, pièces remplacées, observations…' })),
        field('Photo après intervention (facultative)', photo)),
      onSubmit: async data => api.updateInterventionStatus(item.id, 'completed', data.get('comment'), (await preparePhoto(photo.files[0])) || null),
    });
    if (done) {
      toast('Intervention clôturée : l’incident est résolu.');
      afterChange();
      if (drawerElement.classList.contains('show')) drawerReload();
    }
  }

  async function cancelIntervention(item) {
    const done = await formDialog({
      title: 'Annuler l’intervention',
      tone: 'danger',
      confirmLabel: 'Annuler l’intervention',
      fields: h('div', {}, h('p', {}, 'L’incident repassera à l’état « Validé » pour pouvoir être replanifié.'),
        field('Motif', textarea('comment', { rows: 2, required: true }))),
      onSubmit: data => api.updateInterventionStatus(item.id, 'cancelled', data.get('comment')),
    });
    if (done) {
      toast('Intervention annulée. L’incident est à replanifier.');
      afterChange();
      drawerReload();
    }
  }

  async function reassignIntervention(item) {
    const agentList = await agents();
    const done = await formDialog({
      title: 'Réaffecter ou replanifier',
      fields: h('div', { class: 'row g-3' },
        field('Agent technique', select('assigned_to', agentList.map(agent => [agent.id, displayName(agent)]), item.assigned_to, { required: true })),
        field('Date et heure', input('scheduled_date', { type: 'datetime-local', required: true, value: localInputValue(new Date(item.scheduled_date)) }), { col: 'col-md-7' }),
        field('Durée (min)', input('estimated_duration', { type: 'number', min: 5, step: 5, value: item.estimated_duration, required: true }), { col: 'col-md-5' }),
        field('Priorité', select('priority', PRIORITY_OPTIONS, item.priority)),
        field('Consignes', textarea('notes', { rows: 2, value: item.notes }))),
      onSubmit: data => api.updateIntervention(item.id, {
        assigned_to: data.get('assigned_to'),
        scheduled_date: new Date(data.get('scheduled_date')).toISOString(),
        estimated_duration: Number(data.get('estimated_duration')),
        priority: data.get('priority'),
        notes: data.get('notes'),
      }),
    });
    if (done) {
      toast('Intervention mise à jour.');
      afterChange();
      drawerReload();
    }
  }

  // --------------------------------------------------------------- Patrimoine
  async function viewAssets(root, query) {
    const filters = { search: query.get('q') || '', status: query.get('status') || '', asset_type: query.get('asset_type') || '' };
    const actions = isManager() ? [h('button', { type: 'button', class: 'btn btn-primary', onclick: () => assetDialog() }, icon('plus', 'me-2'), 'Ajouter un équipement')] : [];
    root.append(pageHeader('Patrimoine urbain', 'Inventaire des équipements, état de fonctionnement et entretien.', actions));
    const stats = h('div', { class: 'stat-grid' });
    root.appendChild(stats);
    const loadStats = async () => {
      const data = await api.getAssetStats();
      const count = key => (data.by_status.find(item => item.status === key) || {}).count || 0;
      stats.replaceChildren(
        statCard({ label: 'Équipements', value: formatNumber(data.total), iconName: 'building' }),
        statCard({ label: 'Disponibilité', value: formatPercent(data.availability_rate), iconName: 'circle-check', tone: 'success' }),
        statCard({ label: 'En maintenance', value: count('under_maintenance'), iconName: 'wrench', tone: 'warning' }),
        statCard({ label: 'Défectueux', value: count('defective'), iconName: 'circle-exclamation', tone: count('defective') ? 'danger' : 'neutral' }),
        statCard({ label: 'Coût d’entretien cumulé', value: `${formatNumber(Number(data.maintenance_cost))} F`, iconName: 'coins', tone: 'violet' }));
    };

    const typeSelect = select('asset_type', [['', 'Tous les types'], ...(await assetTypes()).map(item => [item.id, item.name_display || item.name])], filters.asset_type, { 'aria-label': 'Type' });
    typeSelect.addEventListener('change', () => { filters.asset_type = typeSelect.value; syncUrl({ asset_type: typeSelect.value }); list.refresh(true); });
    const list = listView({
      toolbar: h('div', { class: 'toolbar' },
        searchField(filters.search, 'Code, nom, emplacement…', value => { filters.search = value; syncUrl({ q: value }); list.refresh(true); }),
        chips([['', 'Tous'], ['operational', 'Opérationnels'], ['under_maintenance', 'En maintenance'], ['defective', 'Défectueux'], ['retired', 'Retirés']],
          filters.status, value => { filters.status = value; syncUrl({ status: value }); list.refresh(true); }),
        h('div', { class: 'ms-auto' }, typeSelect)),
      load: (page, pageSize) => api.getAssets({ ...filters, page, page_size: pageSize }),
      onRowClick: row => openAsset(row.id),
      empty: () => emptyState('building', 'Aucun équipement', isManager() ? 'Ajoutez votre premier équipement pour suivre son état.' : 'Aucun résultat pour ces filtres.'),
      columns: [
        { label: 'Code', class: 'text-nowrap', render: row => h('span', { class: 'code-chip' }, row.code) },
        { label: 'Équipement', mobileLabel: false, render: row => h('div', {}, h('span', { class: 'cell-title' }, row.name), h('span', { class: 'cell-sub' }, [row.brand, row.model].filter(Boolean).join(' · ') || row.asset_type_name)) },
        { label: 'Type', class: 'hide-mobile', render: row => row.asset_type_name },
        { label: 'Emplacement', render: row => row.location },
        { label: 'État', render: row => statusPill(row.status, row.status_display) },
        { label: 'Installé le', class: 'text-nowrap hide-mobile', render: row => formatDate(row.installed_date) },
      ],
    });
    root.appendChild(list.element);
    state.refreshView = () => { loadStats().catch(() => {}); list.refresh(); };
    await Promise.all([loadStats(), list.refresh()]);
  }

  async function assetDialog(asset = null) {
    const types = (await assetTypes()).map(item => [item.id, item.name_display || item.name]);
    const done = await formDialog({
      title: asset ? 'Modifier l’équipement' : 'Nouvel équipement',
      size: 'modal-lg',
      fields: h('div', { class: 'row g-3' },
        field('Code', input('code', { value: asset?.code, required: true, maxlength: 50, placeholder: 'LAMP-002' }), { col: 'col-md-4' }),
        field('Nom', input('name', { value: asset?.name, required: true, maxlength: 200 }), { col: 'col-md-8' }),
        field('Type', select('asset_type', types, asset?.asset_type, { required: true }), { col: 'col-md-6' }),
        field('État', select('status', [['operational', 'Opérationnel'], ['under_maintenance', 'En maintenance'], ['defective', 'Défectueux'], ['retired', 'Retiré']], asset?.status || 'operational'), { col: 'col-md-6' }),
        field('Emplacement', input('location', { value: asset?.location, required: true, maxlength: 300 })),
        field('Latitude', input('latitude', { type: 'number', step: 'any', min: -90, max: 90, value: asset?.latitude }), { col: 'col-md-4' }),
        field('Longitude', input('longitude', { type: 'number', step: 'any', min: -180, max: 180, value: asset?.longitude }), { col: 'col-md-4' }),
        field('Date d’installation', input('installed_date', { type: 'date', required: true, value: asset?.installed_date || new Date().toISOString().slice(0, 10) }), { col: 'col-md-4' }),
        field('Marque', input('brand', { value: asset?.brand, maxlength: 100 }), { col: 'col-md-6' }),
        field('Modèle', input('model', { value: asset?.model, maxlength: 100 }), { col: 'col-md-6' }),
        field('Description', textarea('description', { value: asset?.description, rows: 2 }))),
      onSubmit: data => {
        const payload = Object.fromEntries(data);
        ['latitude', 'longitude'].forEach(key => { if (payload[key] === '') payload[key] = null; });
        return asset ? api.updateAsset(asset.id, payload) : api.createAsset(payload);
      },
    });
    if (done) {
      toast(asset ? 'Équipement mis à jour.' : 'Équipement ajouté.');
      afterChange();
      if (asset) drawerReload();
    }
  }

  function openAsset(id) {
    openDrawer('Équipement', 'Chargement…', async body => {
      const asset = await api.getAsset(id);
      setDrawerTitle(asset.name);
      const actionBar = h('div', { class: 'action-bar mt-3' });
      if (isManager()) {
        const statusSelect = select('status', [['operational', 'Opérationnel'], ['under_maintenance', 'En maintenance'], ['defective', 'Défectueux'], ['retired', 'Retiré']], asset.status, { 'aria-label': 'Changer l’état', class: 'form-select form-select-sm w-auto' });
        statusSelect.addEventListener('change', () => runAction(statusSelect, () => api.updateAsset(id, { status: statusSelect.value }), 'État mis à jour.'));
        actionBar.append(statusSelect, h('button', { type: 'button', class: 'btn btn-sm btn-light', onclick: () => assetDialog(asset) }, icon('pen', 'me-1'), 'Modifier'));
      }
      if (isField()) actionBar.append(h('button', { type: 'button', class: 'btn btn-sm btn-primary', onclick: () => maintenanceDialog(asset) }, icon('screwdriver-wrench', 'me-1'), 'Consigner un entretien'));
      const hasCoordinates = asset.latitude && asset.longitude;
      body.replaceChildren(
        h('div', { class: 'd-flex flex-wrap gap-2' }, h('span', { class: 'code-chip' }, asset.code), statusPill(asset.status, asset.status_display), h('span', { class: 'pill pill-neutral' }, asset.asset_type_name)),
        actionBar,
        section('Fiche technique', details([
          ['Emplacement', asset.location],
          ['Coordonnées', hasCoordinates ? h('a', { href: `https://www.openstreetmap.org/?mlat=${asset.latitude}&mlon=${asset.longitude}#map=18/${asset.latitude}/${asset.longitude}`, target: '_blank', rel: 'noopener' }, `${Number(asset.latitude).toFixed(5)}, ${Number(asset.longitude).toFixed(5)}`, icon('arrow-up-right-from-square', 'ms-1 small')) : null],
          ['Marque', asset.brand],
          ['Modèle', asset.model],
          ['Installé le', formatDate(asset.installed_date)],
          ['Mis à jour', timeAgo(asset.updated_at)],
        ]), asset.description ? h('p', { class: 'small mt-3 mb-0' }, asset.description) : null),
        section('Journal d’entretien', asset.history.length ? h('ol', { class: 'timeline' }, asset.history.map(entry => h('li', {},
          h('div', { class: 'd-flex flex-wrap gap-2 align-items-center' }, h('strong', { class: 'small' }, entry.action_display),
            h('span', { class: 'meta' }, `${formatDate(entry.date, true)} · ${entry.performed_by_username || 'Système'}`),
            entry.cost ? h('span', { class: 'pill pill-violet' }, `${formatNumber(Number(entry.cost))} F`) : null),
          h('p', { class: 'small mb-0 mt-1' }, entry.description)))) : h('p', { class: 'text-secondary small mb-0' }, 'Aucune opération enregistrée.')));
    });
  }

  async function maintenanceDialog(asset) {
    const done = await formDialog({
      title: `Entretien — ${asset.code}`,
      fields: h('div', { class: 'row g-3' },
        field('Type d’opération', select('action', [['maintenance', 'Maintenance'], ['repair', 'Réparation'], ['inspection', 'Inspection'], ['replacement', 'Remplacement'], ['other', 'Autre']], 'maintenance'), { col: 'col-md-7' }),
        field('Coût (facultatif)', input('cost', { type: 'number', min: 0, step: '0.01' }), { col: 'col-md-5' }),
        field('Description', textarea('description', { rows: 3, required: true }))),
      onSubmit: data => api.addAssetHistory({
        asset: asset.id,
        action: data.get('action'),
        description: data.get('description'),
        cost: data.get('cost') || null,
      }),
    });
    if (done) {
      toast('Opération consignée.');
      afterChange();
      drawerReload();
    }
  }

  // --------------------------------------------- Usagers & comptes (clients)
  const ROLE_OPTIONS = () => [['citizen', 'Citoyen'], ['agent', 'Agent technique'], ['manager', 'Gestionnaire'], ['decision_maker', 'Décideur'], ...(is('admin') ? [['admin', 'Administrateur']] : [])];

  async function viewUsers(root, query) {
    const filters = { search: query.get('q') || '', role: query.get('role') || '', is_active: query.get('is_active') || '' };
    root.append(pageHeader('Usagers & comptes', 'Citoyens, agents et équipes : comptes, rôles, accès et historique de signalements.', [
      h('button', { type: 'button', class: 'btn btn-primary', onclick: () => userDialog() }, icon('user-plus', 'me-2'), 'Nouveau compte'),
    ]));
    const stats = h('div', { class: 'stat-grid' });
    const chipHolder = h('div', {});
    root.appendChild(stats);

    async function loadStats() {
      const data = await api.getUserStats();
      const byRole = Object.fromEntries(data.by_role.map(item => [item.role, item.count]));
      stats.replaceChildren(
        statCard({ label: 'Comptes', value: formatNumber(data.total), iconName: 'users', hint: `${data.active} actifs` }),
        statCard({ label: 'Citoyens', value: formatNumber(byRole.citizen || 0), iconName: 'people-group', tone: 'info', hint: `${data.citizens_with_reports} ont déjà signalé`, onClick: () => setRole('citizen') }),
        statCard({ label: 'Agents techniques', value: formatNumber(byRole.agent || 0), iconName: 'helmet-safety', tone: 'warning', onClick: () => setRole('agent') }),
        statCard({ label: 'Comptes désactivés', value: formatNumber(data.inactive), iconName: 'user-slash', tone: data.inactive ? 'danger' : 'neutral', onClick: () => { activeSelect.value = 'false'; activeSelect.dispatchEvent(new Event('change')); } }));
      chipHolder.replaceChildren(chips([['', 'Tous', data.total], ...data.by_role.map(item => [item.role, item.label, item.count])], filters.role, setRole));
    }
    function setRole(value) {
      filters.role = value;
      syncUrl({ role: value });
      const group = chipHolder.querySelector('.chip-group');
      if (group) setActiveChip(group, value);
      list.refresh(true);
    }
    const activeSelect = select('is_active', [['', 'Tous les états'], ['true', 'Actifs'], ['false', 'Désactivés']], filters.is_active, { 'aria-label': 'État du compte' });
    activeSelect.addEventListener('change', () => { filters.is_active = activeSelect.value; syncUrl({ is_active: activeSelect.value }); list.refresh(true); });

    const list = listView({
      toolbar: h('div', { class: 'toolbar' },
        searchField(filters.search, 'Nom, identifiant, e-mail, téléphone…', value => { filters.search = value; syncUrl({ q: value }); list.refresh(true); }),
        chipHolder, h('div', { class: 'ms-auto' }, activeSelect)),
      load: (page, pageSize) => api.getUsers({ ...filters, page, page_size: pageSize }),
      onRowClick: row => openUser(row.id),
      empty: () => emptyState('user-group', 'Aucun compte trouvé', 'Modifiez la recherche ou créez un nouveau compte.'),
      columns: [
        { label: 'Utilisateur', mobileLabel: false, render: row => h('div', { class: 'd-flex align-items-center gap-2' }, h('span', { class: 'avatar avatar-sm' }, initials(row.full_name)),
          h('div', { class: 'min-w-0' }, h('span', { class: 'cell-title' }, row.full_name), h('span', { class: 'cell-sub' }, `@${row.username}${row.department ? ` · ${row.department}` : ''}`))) },
        { label: 'Contact', render: row => h('div', {}, h('span', { class: 'd-block small' }, row.email || '—'), h('span', { class: 'cell-sub' }, row.phone_number || '')) },
        { label: 'Rôle', render: row => rolePill(row.effective_role, row.role_display) },
        { label: 'Signalements', class: 'text-center', render: row => formatNumber(row.incident_count) },
        { label: 'Dernière connexion', class: 'text-nowrap hide-mobile', render: row => row.last_login ? timeAgo(row.last_login) : h('span', { class: 'text-secondary' }, 'Jamais') },
        { label: 'État', render: row => row.is_active ? h('span', { class: 'pill pill-success' }, 'Actif') : h('span', { class: 'pill pill-neutral' }, 'Désactivé') },
      ],
    });
    root.appendChild(list.element);
    state.refreshView = () => { loadStats().catch(() => {}); list.refresh(); };
    await Promise.all([loadStats(), list.refresh()]);
  }

  function passwordField(name = 'password') {
    const passwordInput = input(name, { type: 'text', required: true, minlength: 8, value: UI.suggestPassword(), autocomplete: 'new-password', spellcheck: 'false' });
    return h('div', { class: 'input-group' }, passwordInput,
      h('button', { type: 'button', class: 'btn btn-light', title: 'Générer', 'aria-label': 'Générer un mot de passe', onclick: () => { passwordInput.value = UI.suggestPassword(); } }, icon('rotate')),
      h('button', { type: 'button', class: 'btn btn-light', title: 'Copier', 'aria-label': 'Copier le mot de passe', onclick: () => copyText(passwordInput.value) }, icon('copy')));
  }

  async function userDialog(user = null) {
    const password = user ? null : passwordField();
    const fields = h('div', { class: 'row g-3' },
      field('Prénom', input('first_name', { value: user?.first_name, required: true, maxlength: 150, autocomplete: 'off' }), { col: 'col-md-6' }),
      field('Nom', input('last_name', { value: user?.last_name, required: true, maxlength: 150, autocomplete: 'off' }), { col: 'col-md-6' }),
      user ? null : field('Identifiant de connexion', input('username', { required: true, maxlength: 150, pattern: '[\\w.@+\\-]+', autocomplete: 'off' }), { col: 'col-md-6', hint: 'Lettres, chiffres et . @ + - _' }),
      field('Rôle', select('role', ROLE_OPTIONS(), user?.role || 'agent', { disabled: user?.is_superuser || null }), { col: user ? 'col-md-12' : 'col-md-6' }),
      field('E-mail', input('email', { type: 'email', value: user?.email, maxlength: 254 }), { col: 'col-md-6' }),
      field('Téléphone', input('phone_number', { type: 'tel', value: user?.phone_number, maxlength: 20, placeholder: '+221 77 000 00 00' }), { col: 'col-md-6' }),
      field('Service / département', input('department', { value: user?.department, maxlength: 100 })),
      password ? field('Mot de passe provisoire', password, { hint: 'Communiquez-le à la personne : elle pourra le changer depuis son profil.' }) : null);
    const saved = await formDialog({
      title: user ? `Modifier ${user.full_name}` : 'Nouveau compte',
      size: 'modal-lg',
      confirmLabel: user ? 'Enregistrer' : 'Créer le compte',
      fields,
      onSubmit: data => {
        const payload = Object.fromEntries(data);
        if (user && user.is_superuser) delete payload.role;
        return user ? api.updateUser(user.id, payload) : api.createUser(payload);
      },
    });
    if (saved) {
      toast(user ? 'Compte mis à jour.' : `Compte « ${saved.username} » créé.`);
      state.agents = null;
      afterChange();
      if (user) drawerReload();
    }
  }

  function openUser(id) {
    openDrawer('Compte', 'Chargement…', async body => {
      const user = await api.getUser(id);
      setDrawerTitle(user.full_name);
      const isSelf = user.id === state.user.id;
      const protectedAccount = user.is_superuser && !state.user.is_superuser;
      const actionBar = h('div', { class: 'action-bar' });
      if (!protectedAccount) {
        actionBar.append(h('button', { type: 'button', class: 'btn btn-sm btn-light', onclick: () => userDialog(user) }, icon('pen', 'me-1'), 'Modifier'));
        if (!isSelf) {
          actionBar.append(
            h('button', { type: 'button', class: `btn btn-sm ${user.is_active ? 'btn-outline-warning' : 'btn-outline-success'}`,
              onclick: event => runAction(event.currentTarget, () => api.toggleUserActive(user.id), user.is_active ? 'Compte désactivé.' : 'Compte réactivé.') },
            icon(user.is_active ? 'user-slash' : 'user-check', 'me-1'), user.is_active ? 'Désactiver' : 'Réactiver'),
            h('button', { type: 'button', class: 'btn btn-sm btn-light', onclick: () => resetPassword(user) }, icon('key', 'me-1'), 'Nouveau mot de passe'),
            h('button', { type: 'button', class: 'btn btn-sm btn-light text-danger', 'aria-label': 'Supprimer le compte', title: 'Supprimer le compte', onclick: () => deleteUser(user) }, icon('trash')));
        }
      }
      const reports = h('div', {}, skeleton(3));
      body.replaceChildren(
        h('div', { class: 'd-flex align-items-center gap-3 mb-3' }, h('span', { class: 'avatar avatar-lg' }, initials(user.full_name)),
          h('div', {}, h('div', { class: 'd-flex flex-wrap gap-2 mb-1' }, rolePill(user.effective_role, user.role_display), user.is_active ? h('span', { class: 'pill pill-success' }, 'Actif') : h('span', { class: 'pill pill-neutral' }, 'Désactivé')),
            h('span', { class: 'text-secondary small' }, `@${user.username}`))),
        actionBar,
        section('Coordonnées', details([
          ['E-mail', user.email ? h('a', { href: `mailto:${user.email}` }, user.email) : null],
          ['Téléphone', user.phone_number ? h('a', { href: `tel:${user.phone_number}` }, user.phone_number) : null],
          ['Service', user.department],
          ['Inscrit le', formatDate(user.date_joined)],
          ['Dernière connexion', user.last_login ? formatDate(user.last_login, true) : 'Jamais'],
          ['Signalements', formatNumber(user.incident_count)],
        ])),
        section('Signalements de cet usager', reports));
      if (!user.incident_count) {
        reports.replaceChildren(h('p', { class: 'text-secondary small mb-0' }, 'Aucun signalement.'));
      } else {
        const items = listItems(await api.getIncidents({ reporter: user.id, page_size: 10 }));
        reports.replaceChildren(h('div', { class: 'list-group list-group-flush' }, items.map(item => h('button', {
          type: 'button', class: 'list-group-item list-group-item-action d-flex justify-content-between align-items-center gap-2 px-0', style: { background: 'transparent', color: 'inherit' },
          onclick: () => openIncident(item.id),
        }, h('span', { class: 'min-w-0' }, h('span', { class: 'cell-title' }, item.title), h('span', { class: 'cell-sub' }, `${item.tracking_code} · ${formatDate(item.created_at)}`)), statusPill(item.status, item.status_display)))));
      }
    });
  }

  async function resetPassword(user) {
    const password = passwordField('new_password');
    let chosen = '';
    const done = await formDialog({
      title: `Nouveau mot de passe — ${user.full_name}`,
      confirmLabel: 'Définir',
      fields: h('div', {}, field('Mot de passe provisoire', password, { hint: 'Les sessions ouvertes de cet utilisateur seront fermées.' })),
      onSubmit: data => { chosen = data.get('new_password'); return api.resetUserPassword(user.id, chosen); },
    });
    if (done) toast('Mot de passe réinitialisé.', 'success', { action: { label: 'Copier', handler: () => copyText(chosen) }, duration: 10000 });
  }

  async function deleteUser(user) {
    const confirmed = await confirmDialog('Supprimer ce compte ?',
      `Le compte « ${user.username} » sera supprimé définitivement. Ses signalements sont conservés de façon anonyme. Pour suspendre l’accès sans perte, préférez « Désactiver ».`,
      { confirmLabel: 'Supprimer', tone: 'danger' });
    if (!confirmed) return;
    try {
      await api.deleteUser(user.id);
      drawer.hide();
      toast('Compte supprimé.');
      state.agents = null;
      afterChange();
    } catch (error) {
      toast(error.message, 'error');
    }
  }

  // ----------------------------------------------------- Décisions éclairées
  async function viewDecisions(root) {
    root.append(pageHeader('Décisions éclairées', 'Les signaux faibles et les priorités, à partir des données terrain.', [
      h('button', { type: 'button', class: 'btn btn-light', onclick: () => navigate('reports') }, icon('file-lines', 'me-2'), 'Générer un rapport'),
    ]));
    const summary = await api.getDashboardSummary();
    const incidents = summary.incidents;
    const interventions = summary.interventions;
    root.append(h('div', { class: 'stat-grid' },
      statCard({ label: 'Incidents déclarés', value: formatNumber(incidents.total), iconName: 'triangle-exclamation', tone: 'warning', hint: `${incidents.last_30_days} sur 30 jours` }),
      statCard({ label: 'Délai moyen de résolution', value: formatHours(incidents.avg_resolution_hours), iconName: 'stopwatch', tone: 'info' }),
      statCard({ label: 'Urgences ouvertes', value: incidents.urgent_open, iconName: 'fire-flame-curved', tone: incidents.urgent_open ? 'danger' : 'neutral' }),
      statCard({ label: 'Interventions en retard', value: interventions.overdue, iconName: 'clock', tone: interventions.overdue ? 'danger' : 'neutral', hint: `${interventions.active} actives` })));

    const insights = [];
    const topCategory = incidents.by_category[0];
    if (topCategory && incidents.total) insights.push(['bullseye', 'primary', `« ${topCategory.label} » représente ${Math.round(topCategory.count / incidents.total * 100)} % des signalements : un plan d’action ciblé aurait le plus d’impact.`]);
    if (incidents.awaiting_validation) insights.push(['inbox', 'warning', `${incidents.awaiting_validation} signalement(s) attendent une validation.`]);
    if (incidents.awaiting_planning) insights.push(['calendar-plus', 'info', `${incidents.awaiting_planning} incident(s) validé(s) n’ont pas encore d’intervention.`]);
    if (interventions.overdue) insights.push(['clock', 'danger', `${interventions.overdue} intervention(s) ont dépassé leur date prévue.`]);
    if (summary.assets.total && summary.assets.availability_rate < 90) insights.push(['building-circle-exclamation', 'danger', `Disponibilité du patrimoine à ${summary.assets.availability_rate} % : sous l’objectif de 90 %.`]);
    if (!insights.length) insights.push(['circle-check', 'success', 'Aucun point d’alerte : les indicateurs sont dans les objectifs.']);

    root.append(
      h('div', { class: 'row g-3 mb-3' },
        h('div', { class: 'col-lg-8' }, panel('Tendance des signalements (30 jours)', barChart(incidents.trend))),
        h('div', { class: 'col-lg-4' }, panel('Taux de résolution', h('div', { class: 'py-2' }, donut(incidents.resolution_rate, 'des incidents résolus'),
          h('p', { class: 'text-center small text-secondary mt-3 mb-0' }, `${incidents.resolved} résolus sur ${incidents.total}`))))),
      h('div', { class: 'row g-3 mb-3' },
        h('div', { class: 'col-lg-6' }, panel('Points d’attention', h('div', {}, insights.map(([iconName, tone, text]) => h('div', { class: 'insight' }, h('span', { class: `stat-icon tone-${tone}`, style: { width: '34px', height: '34px' } }, icon(iconName)), h('p', { class: 'mb-0 small' }, text)))))),
        h('div', { class: 'col-lg-6' }, panel('Incidents par catégorie', distribution(incidents.by_category)))),
      h('div', { class: 'row g-3' },
        h('div', { class: 'col-md-4' }, panel('Par priorité', distribution(incidents.by_priority))),
        h('div', { class: 'col-md-4' }, panel('Par statut', distribution(incidents.by_status))),
        h('div', { class: 'col-md-4' }, panel('Interventions', distribution(interventions.by_status)))));
  }

  // ------------------------------------------------------------ Rapports & KPI
  async function viewReports(root) {
    root.append(pageHeader('Rapports & KPI', 'Bilans périodiques, exports et historique des indicateurs.'));
    const today = new Date();
    const iso = date => `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
    const presets = {
      month: [new Date(today.getFullYear(), today.getMonth(), 1), today],
      previous: [new Date(today.getFullYear(), today.getMonth() - 1, 1), new Date(today.getFullYear(), today.getMonth(), 0)],
      quarter: [new Date(today.getFullYear(), today.getMonth() - 2, 1), today],
      year: [new Date(today.getFullYear(), 0, 1), today],
    };
    const startInput = input('start_date', { type: 'date', required: true, value: iso(presets.month[0]) });
    const endInput = input('end_date', { type: 'date', required: true, value: iso(presets.month[1]) });
    const result = h('div', {});
    const generateButton = h('button', { type: 'submit', class: 'btn btn-primary w-100' }, icon('wand-magic-sparkles', 'me-2'), 'Générer');
    const generator = h('form', { class: 'row g-3 align-items-end', onsubmit: event => { event.preventDefault(); generate(false); } },
      h('div', { class: 'col-12' }, chips([['month', 'Ce mois-ci'], ['previous', 'Mois précédent'], ['quarter', '3 derniers mois'], ['year', 'Année en cours']], 'month', key => {
        startInput.value = iso(presets[key][0]);
        endInput.value = iso(presets[key][1]);
        generate(false);
      })),
      field('Du', startInput, { col: 'col-sm-4' }),
      field('Au', endInput, { col: 'col-sm-4' }),
      h('div', { class: 'col-sm-4' }, generateButton));

    async function generate(save) {
      if (!startInput.value || !endInput.value) return;
      setBusy(generateButton, true);
      try {
        const data = await api.generateReport({ start_date: startInput.value, end_date: endInput.value, save });
        if (save) {
          toast('Rapport enregistré.');
          loadSaved();
        }
        renderResult(data);
      } catch (error) {
        result.replaceChildren(errorState(error));
      } finally {
        setBusy(generateButton, false);
      }
    }

    function renderResult(data) {
      const buttons = [h('button', { type: 'button', class: 'btn btn-light', onclick: event => runAction(event.currentTarget, () => api.exportIncidents({ date_from: startInput.value, date_to: endInput.value }), 'Export téléchargé.') }, icon('file-csv', 'me-2'), 'Exporter les incidents (CSV)')];
      if (isManager() && !data.report_id) buttons.unshift(h('button', { type: 'button', class: 'btn btn-primary', onclick: () => generate(true) }, icon('floppy-disk', 'me-2'), 'Enregistrer ce rapport'));
      result.replaceChildren(h('div', { class: 'mt-4' },
        h('div', { class: 'stat-grid' },
          statCard({ label: 'Incidents', value: data.total_incidents, iconName: 'triangle-exclamation', tone: 'warning' }),
          statCard({ label: 'Résolus', value: data.resolved_incidents, iconName: 'circle-check', tone: 'success', hint: `${Number(data.resolution_rate || 0).toFixed(1).replace('.', ',')} % de résolution` }),
          statCard({ label: 'Délai moyen', value: formatHours(data.avg_resolution_hours), iconName: 'stopwatch', tone: 'info' }),
          statCard({ label: 'Interventions', value: data.interventions_planned, iconName: 'helmet-safety', hint: `${data.interventions_completed} terminées` }),
          statCard({ label: 'Coût d’entretien', value: `${formatNumber(data.maintenance_cost ?? 0)} F`, iconName: 'coins', tone: 'violet' })),
        h('div', { class: 'row g-3' },
          h('div', { class: 'col-md-6' }, h('h3', { class: 'h6' }, 'Par catégorie'), distribution(data.by_category || [])),
          h('div', { class: 'col-md-6' }, h('h3', { class: 'h6' }, 'Par priorité'), distribution(data.by_priority || []))),
        h('div', { class: 'd-flex flex-wrap gap-2 mt-4' }, buttons)));
    }

    const savedBody = h('div', {}, skeleton(3));
    async function loadSaved() {
      const reports = listItems(await api.getReports());
      if (!reports.length) {
        savedBody.replaceChildren(emptyState('folder-open', 'Aucun rapport enregistré', isManager() ? 'Générez un bilan puis enregistrez-le pour le partager.' : null));
        return;
      }
      savedBody.replaceChildren(dataTable([
        { label: 'Rapport', mobileLabel: false, render: row => h('div', {}, h('span', { class: 'cell-title' }, row.title), h('span', { class: 'cell-sub' }, `Par ${row.generated_by_username || '—'}`)) },
        { label: 'Type', render: row => h('span', { class: 'pill pill-neutral' }, row.report_type_display) },
        { label: 'Période', class: 'text-nowrap', render: row => `${formatDate(row.start_date)} → ${formatDate(row.end_date)}` },
        { label: 'Créé', class: 'text-nowrap', render: row => timeAgo(row.created_at) },
        { label: '', mobileLabel: false, class: 'text-end', render: row => isManager() ? h('button', { type: 'button', class: 'btn btn-sm btn-light text-danger', 'aria-label': `Supprimer ${row.title}`, onclick: async () => {
          if (!await confirmDialog('Supprimer ce rapport ?', row.title, { tone: 'danger', confirmLabel: 'Supprimer' })) return;
          try { await api.deleteReport(row.id); toast('Rapport supprimé.'); loadSaved(); } catch (error) { toast(error.message, 'error'); }
        } }, icon('trash')) : '' },
      ], reports, row => {
        startInput.value = row.start_date;
        endInput.value = row.end_date;
        renderResult({ ...row.content, report_id: row.id });
        generator.scrollIntoView({ behavior: 'smooth' });
      }));
    }

    const kpiBody = h('div', {}, skeleton(3));
    async function loadKpi() {
      const metrics = listItems(await api.getKpiMetrics()).slice(0, 12);
      kpiBody.replaceChildren(metrics.length ? dataTable([
        { label: 'Date', render: row => formatDate(row.date) },
        { label: 'Incidents', render: row => row.total_incidents },
        { label: 'Résolus', render: row => row.resolved_incidents },
        { label: 'En attente', render: row => row.pending_incidents },
        { label: 'Délai moyen', render: row => formatHours(row.avg_resolution_time) },
        { label: 'Disponibilité', render: row => `${row.asset_availability} %` },
      ], metrics) : emptyState('chart-line', 'Aucun historique KPI', isManager() ? 'Enregistrez un instantané pour suivre l’évolution dans le temps.' : null));
    }

    root.append(
      h('div', { class: 'mb-3' }, panel('Générer un bilan', h('div', {}, generator, result))),
      h('div', { class: 'row g-3' },
        h('div', { class: 'col-xl-7' }, panel('Rapports enregistrés', savedBody, { flush: true })),
        h('div', { class: 'col-xl-5' }, panel('Historique des KPI', kpiBody, {
          flush: true,
          actions: isManager() ? h('button', { type: 'button', class: 'btn btn-sm btn-light', onclick: event => runAction(event.currentTarget, async () => { await api.snapshotKpi(); await loadKpi(); }, 'Instantané KPI enregistré.') }, icon('camera', 'me-1'), 'Instantané') : null,
        }))));
    await Promise.all([generate(false), loadSaved(), loadKpi()]);
  }

  // ---------------------------------------------------------------- Profil
  async function viewProfile(root) {
    const user = await api.getCurrentUser();
    root.append(pageHeader('Mon profil', 'Vos informations personnelles et la sécurité de votre compte.'));
    const profileButton = h('button', { type: 'submit', class: 'btn btn-primary' }, 'Enregistrer');
    const profileForm = h('form', { class: 'row g-3', onsubmit: async event => {
      event.preventDefault();
      const updated = await runAction(profileButton, () => api.updateProfile(Object.fromEntries(new FormData(profileForm))), 'Profil mis à jour.');
      if (updated) storeUser(updated);
    } },
    field('Prénom', input('first_name', { value: user.first_name, maxlength: 150 }), { col: 'col-md-6' }),
    field('Nom', input('last_name', { value: user.last_name, maxlength: 150 }), { col: 'col-md-6' }),
    field('E-mail', input('email', { type: 'email', value: user.email }), { col: 'col-md-6', hint: 'Utilisé pour vos notifications.' }),
    field('Téléphone', input('phone_number', { type: 'tel', value: user.phone_number, maxlength: 20 }), { col: 'col-md-6' }),
    field('Service / département', input('department', { value: user.department, maxlength: 100 })),
    h('div', { class: 'col-12' }, profileButton));

    const passwordButton = h('button', { type: 'submit', class: 'btn btn-primary' }, 'Changer le mot de passe');
    const passwordForm = h('form', { class: 'row g-3', onsubmit: async event => {
      event.preventDefault();
      const data = new FormData(passwordForm);
      if (data.get('new_password') !== data.get('confirm')) { toast('Les deux mots de passe ne correspondent pas.', 'error'); return; }
      const response = await runAction(passwordButton, () => api.changePassword({ current_password: data.get('current_password'), new_password: data.get('new_password') }), 'Mot de passe modifié. Vos autres sessions ont été fermées.');
      if (response) { api.setToken(response.token); passwordForm.reset(); }
    } },
    field('Mot de passe actuel', input('current_password', { type: 'password', required: true, autocomplete: 'current-password' })),
    field('Nouveau mot de passe', input('new_password', { type: 'password', required: true, minlength: 8, autocomplete: 'new-password' }), { col: 'col-md-6', hint: '8 caractères minimum, évitez les mots trop courants.' }),
    field('Confirmation', input('confirm', { type: 'password', required: true, minlength: 8, autocomplete: 'new-password' }), { col: 'col-md-6' }),
    h('div', { class: 'col-12' }, passwordButton));

    root.append(h('div', { class: 'row g-3' },
      h('div', { class: 'col-lg-4' }, panel(null, h('div', { class: 'text-center py-2' },
        h('span', { class: 'avatar avatar-lg mx-auto mb-3', style: { width: '76px', height: '76px', fontSize: '1.4rem' } }, initials(user.full_name)),
        h('h2', { class: 'h5 mb-1' }, user.full_name), h('p', { class: 'text-secondary small mb-2' }, `@${user.username}`), rolePill(user.effective_role, user.role_display),
        h('hr'), details([['Membre depuis', formatDate(user.date_joined)], ['Signalements', formatNumber(user.incident_count)]])))),
      h('div', { class: 'col-lg-8 d-flex flex-column gap-3' }, panel('Informations personnelles', profileForm), panel('Sécurité', passwordForm))));
  }

  // --------------------------------------------------------- Signalement
  const reportModalElement = document.getElementById('incidentModal');
  const reportModal = new bootstrap.Modal(reportModalElement);
  const reportForm = document.getElementById('incidentForm');
  const photoInput = document.getElementById('incidentPhoto');
  const photoPreview = document.getElementById('incidentPhotoPreview');
  const reportMessage = document.getElementById('incidentMessage');

  async function openReportModal() {
    reportMessage.textContent = '';
    reportModal.show();
    try {
      const categorySelect = document.getElementById('incidentCategory');
      if (categorySelect.options.length <= 1) {
        const items = await categories();
        categorySelect.replaceChildren(new Option('Choisir une catégorie', ''), ...items.map(item => new Option(item.name_display || item.name, item.id)));
      }
    } catch (error) {
      reportMessage.className = 'small mt-3 text-danger';
      reportMessage.textContent = 'Catégories indisponibles. Réessayez plus tard.';
    }
  }
  document.getElementById('showIncidentFormButton').addEventListener('click', openReportModal);
  reportModalElement.addEventListener('shown.bs.modal', () => document.getElementById('incidentTitle').focus());

  let reportPhoto = null;
  photoInput.addEventListener('change', async () => {
    reportPhoto = null;
    photoPreview.replaceChildren();
    photoPreview.hidden = !photoInput.files[0];
    if (!photoInput.files[0]) return;
    photoPreview.textContent = 'Préparation de la photo…';
    const file = await preparePhoto(photoInput.files[0]);
    photoPreview.replaceChildren();
    if (file.size > MAX_PHOTO_SIZE) {
      photoPreview.append(h('span', { class: 'text-danger small' }, 'La photo dépasse 5 Mio : choisissez une image plus légère.'));
      return;
    }
    reportPhoto = file;
    const url = URL.createObjectURL(file);
    photoPreview.append(h('img', { src: url, alt: 'Aperçu de la photo', onload: () => URL.revokeObjectURL(url) }),
      h('div', { class: 'small' }, h('strong', { class: 'd-block' }, file.name), `${(file.size / 1024 / 1024).toFixed(1).replace('.', ',')} Mio`,
        h('button', { type: 'button', class: 'btn btn-link btn-sm text-danger p-0 ms-2', onclick: () => { photoInput.value = ''; photoInput.dispatchEvent(new Event('change')); } }, 'Retirer')));
  });

  document.getElementById('locateButton').addEventListener('click', event => {
    const button = event.currentTarget;
    if (!navigator.geolocation) { toast('La géolocalisation n’est pas disponible sur cet appareil.', 'warning'); return; }
    setBusy(button, true);
    navigator.geolocation.getCurrentPosition(position => {
      const address = document.getElementById('incidentAddress');
      const gps = `GPS ${position.coords.latitude.toFixed(5)}, ${position.coords.longitude.toFixed(5)}`;
      address.value = address.value ? `${address.value.replace(/\s*\(GPS[^)]*\)$/, '')} (${gps})`.slice(0, 300) : gps;
      setBusy(button, false);
      toast('Position ajoutée au signalement.', 'info');
    }, () => {
      setBusy(button, false);
      toast('Position introuvable. Vérifiez l’autorisation de localisation.', 'warning');
    }, { enableHighAccuracy: true, timeout: 10000 });
  });

  reportForm.addEventListener('submit', async event => {
    event.preventDefault();
    if (!reportForm.checkValidity()) {
      reportForm.classList.add('was-validated');
      return;
    }
    if (photoInput.files[0] && !reportPhoto) {
      reportMessage.className = 'small mt-3 text-danger';
      reportMessage.textContent = 'La photo ne doit pas dépasser 5 Mio.';
      return;
    }
    const formData = new FormData(reportForm);
    ['title', 'description', 'address', 'region', 'department', 'commune'].forEach(name => formData.set(name, (formData.get(name) || '').trim()));
    if (reportPhoto) formData.set('photo', reportPhoto, reportPhoto.name);
    else formData.delete('photo');
    const submit = reportForm.querySelector('button[type="submit"]');
    setBusy(submit, true);
    reportMessage.textContent = '';
    try {
      const created = await api.createIncident(formData);
      reportModal.hide();
      reportForm.reset();
      reportPhoto = null;
      reportForm.classList.remove('was-validated');
      photoPreview.hidden = true;
      toast(`Signalement envoyé. Code de suivi : ${created.tracking_code}`, 'success', {
        duration: 10000,
        action: { label: 'Copier', handler: () => copyText(created.tracking_code) },
      });
      afterChange();
    } catch (error) {
      reportMessage.className = 'small mt-3 text-danger';
      reportMessage.textContent = `Le signalement n’a pas pu être envoyé. ${error.message}`;
    } finally {
      setBusy(submit, false);
    }
  });

  // ------------------------------------------------------------ Notifications
  const badge = document.getElementById('notificationBadge');
  const notificationList = document.getElementById('notificationList');

  function setUnread(count) {
    const previous = state.unread;
    const firstLoad = !state.unreadLoaded;
    state.unread = count;
    state.unreadLoaded = true;
    badge.hidden = !count;
    badge.textContent = count > 99 ? '99+' : String(count);
    document.getElementById('notificationButton').setAttribute('aria-label', count ? `Notifications (${count} non lues)` : 'Notifications');
    if (!firstLoad && count > previous) toast('Vous avez une nouvelle notification.', 'info');
  }

  async function refreshBadges() {
    try {
      setUnread((await api.getUnreadNotificationCount()).count);
    } catch (error) { /* silencieux : l'icône reste inchangée */ }
  }

  async function loadNotifications() {
    notificationList.replaceChildren(skeleton(3));
    try {
      const items = listItems(await api.getNotifications({ page_size: 15 }));
      if (!items.length) {
        notificationList.replaceChildren(emptyState('bell-slash', 'Aucune notification', 'Vous serez prévenu ici des nouveautés.'));
        return;
      }
      notificationList.replaceChildren(...items.map(item => h('button', {
        type: 'button', class: `notif-item${item.is_read ? '' : ' unread'}`,
        onclick: async () => {
          if (!item.is_read) {
            try { await api.markNotificationRead(item.id); } catch (error) { /* non bloquant */ }
            refreshBadges();
          }
          bootstrap.Dropdown.getOrCreateInstance(document.getElementById('notificationButton')).hide();
          if (item.related_object_type === 'incident' && item.related_object_id) openIncident(item.related_object_id);
          else if (item.related_object_type === 'intervention' && item.related_object_id && isField()) openIntervention(item.related_object_id);
        },
      }, h('span', { class: 'notif-dot' }), h('span', {}, h('span', { class: 'd-block' }, item.message), h('small', { class: 'text-secondary' }, timeAgo(item.created_at))))));
    } catch (error) {
      notificationList.replaceChildren(errorState(error, loadNotifications));
    }
  }
  document.getElementById('notificationButton').addEventListener('show.bs.dropdown', loadNotifications);
  document.getElementById('markAllReadButton').addEventListener('click', async event => {
    await runAction(event.currentTarget, () => api.markAllNotificationsRead(), null);
    loadNotifications();
  });
  setInterval(() => { if (document.visibilityState === 'visible') refreshBadges(); }, 60000);
  document.addEventListener('visibilitychange', () => { if (document.visibilityState === 'visible') refreshBadges(); });

  // ------------------------------------------------------- Barre supérieure
  function storeUser(user) {
    state.user = { ...state.user, ...user };
    localStorage.setItem('user_data', JSON.stringify(state.user));
    renderIdentity();
  }

  function renderIdentity() {
    const name = displayName(state.user);
    document.getElementById('userName').textContent = name;
    document.getElementById('userAvatar').textContent = initials(name);
    document.getElementById('userRole').textContent = (UI.ROLES[role()] || [role()])[0];
    document.getElementById('globalSearchForm').hidden = !allowed('incidents');
    document.getElementById('showIncidentFormButton').hidden = false;
  }

  document.getElementById('globalSearchForm').addEventListener('submit', event => {
    event.preventDefault();
    const value = document.getElementById('globalSearch').value.trim();
    navigate('incidents', { q: value });
  });
  document.addEventListener('keydown', event => {
    if (event.key === '/' && !event.target.closest('input, textarea, select, [contenteditable]')) {
      event.preventDefault();
      document.getElementById('globalSearch').focus();
    }
  });

  const themeToggle = document.getElementById('themeToggle');
  function paintThemeIcon() {
    const dark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
    themeToggle.replaceChildren(icon(dark ? 'sun' : 'moon'));
    themeToggle.setAttribute('aria-label', dark ? 'Passer au thème clair' : 'Passer au thème sombre');
  }
  themeToggle.addEventListener('click', () => {
    const next = document.documentElement.getAttribute('data-bs-theme') === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-bs-theme', next);
    try { localStorage.setItem('giu_theme', next); } catch (error) { /* préférence non conservée */ }
    paintThemeIcon();
  });

  document.getElementById('logoutButton').addEventListener('click', async () => {
    try { await api.logout(); } catch (error) { api.clearSession(); }
    window.location.href = '/';
  });

  // --------------------------------------------------------------- Démarrage
  async function start() {
    if (!api.token) return;
    paintThemeIcon();
    renderIdentity();
    renderNav();
    render();
    refreshBadges();
    if (window.GIU_OPEN_REPORT) openReportModal();
    try {
      // Rafraîchit le rôle réel côté serveur (sessions anciennes ou rôle modifié).
      const fresh = await api.getCurrentUser();
      const previousRole = role();
      storeUser(fresh);
      if (role() !== previousRole) { renderNav(); render(); }
    } catch (error) { /* une erreur 401 redirige déjà vers la connexion */ }
  }
  start();
})();
