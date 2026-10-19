// Boîte à outils d'interface : construction DOM sûre, toasts, dialogues, formats, graphiques.
(() => {
  // Crée un élément ; le texte passe toujours par textContent (aucune injection HTML).
  function h(tag, attrs = {}, ...children) {
    const element = document.createElement(tag);
    Object.entries(attrs || {}).forEach(([key, value]) => {
      if (value === undefined || value === null || value === false) return;
      if (key === 'class') element.className = value;
      else if (key === 'text') element.textContent = value;
      else if (key === 'dataset') Object.assign(element.dataset, value);
      else if (key === 'style' && typeof value === 'object') {
        // setProperty est requis pour les variables CSS (--value), ignorées par Object.assign.
        Object.entries(value).forEach(([name, styleValue]) => {
          if (name.startsWith('--')) element.style.setProperty(name, styleValue);
          else element.style[name] = styleValue;
        });
      }
      else if (key.startsWith('on') && typeof value === 'function') {
        element.addEventListener(key.slice(2).toLowerCase(), value);
      } else if (value === true) element.setAttribute(key, '');
      else element.setAttribute(key, value);
    });
    children.flat(Infinity).forEach(child => {
      if (child === undefined || child === null || child === false) return;
      element.append(child instanceof Node ? child : document.createTextNode(String(child)));
    });
    return element;
  }

  const icon = (name, extra = '') => h('i', { class: `fa-solid fa-${name} ${extra}`.trim(), 'aria-hidden': 'true' });

  function debounce(fn, delay = 300) {
    let timer;
    return (...args) => {
      clearTimeout(timer);
      timer = setTimeout(() => fn(...args), delay);
    };
  }

  const listItems = data => (Array.isArray(data) ? data : (data && Array.isArray(data.results) ? data.results : []));

  // ---- Formats ----
  const dateFormatter = new Intl.DateTimeFormat('fr-FR', { day: '2-digit', month: 'short', year: 'numeric' });
  const dateTimeFormatter = new Intl.DateTimeFormat('fr-FR', {
    day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit',
  });
  const relativeFormatter = new Intl.RelativeTimeFormat('fr', { numeric: 'auto' });

  function formatDate(value, withTime = false) {
    if (!value) return '—';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return (withTime ? dateTimeFormatter : dateFormatter).format(date);
  }

  function timeAgo(value) {
    if (!value) return '—';
    const seconds = (new Date(value).getTime() - Date.now()) / 1000;
    const units = [['year', 31536000], ['month', 2592000], ['week', 604800], ['day', 86400], ['hour', 3600], ['minute', 60]];
    for (const [unit, size] of units) {
      if (Math.abs(seconds) >= size) return relativeFormatter.format(Math.round(seconds / size), unit);
    }
    return 'à l’instant';
  }

  const formatNumber = value => (value === null || value === undefined ? '—' : new Intl.NumberFormat('fr-FR').format(value));
  const formatPercent = value => `${new Intl.NumberFormat('fr-FR', { maximumFractionDigits: 1 }).format(Number(value) || 0)} %`;

  function formatHours(hours) {
    if (hours === null || hours === undefined) return '—';
    if (hours < 1) return `${Math.round(hours * 60)} min`;
    if (hours < 48) return `${hours.toFixed(1).replace('.', ',')} h`;
    return `${(hours / 24).toFixed(1).replace('.', ',')} j`;
  }

  const initials = name => (name || '?').split(/\s+/).filter(Boolean).slice(0, 2).map(part => part[0].toUpperCase()).join('') || '?';

  // ---- Libellés et pastilles ----
  const STATUS = {
    created: ['Nouveau', 'info'],
    validated: ['Validé', 'primary'],
    planned: ['Planifié', 'violet'],
    in_progress: ['En cours', 'warning'],
    resolved: ['Résolu', 'success'],
    rejected: ['Rejeté', 'danger'],
    pending: ['En attente', 'neutral'],
    assigned: ['Assignée', 'primary'],
    completed: ['Terminée', 'success'],
    cancelled: ['Annulée', 'danger'],
    operational: ['Opérationnel', 'success'],
    under_maintenance: ['En maintenance', 'warning'],
    defective: ['Défectueux', 'danger'],
    retired: ['Retiré', 'neutral'],
  };
  const PRIORITY = {
    low: ['Basse', 'neutral'],
    medium: ['Moyenne', 'info'],
    high: ['Haute', 'warning'],
    urgent: ['Urgente', 'danger'],
  };
  const ROLES = {
    citizen: ['Citoyen', 'info'],
    agent: ['Agent technique', 'warning'],
    manager: ['Gestionnaire', 'primary'],
    decision_maker: ['Décideur', 'violet'],
    admin: ['Administrateur', 'danger'],
  };

  function pill(map, key, fallback) {
    const [label, tone] = map[key] || [fallback || key || '—', 'neutral'];
    return h('span', { class: `pill pill-${tone}` }, label);
  }
  const statusPill = (status, label) => pill(STATUS, status, label);
  const priorityPill = (priority, label) => {
    const element = pill(PRIORITY, priority, label);
    if (priority === 'urgent' || priority === 'high') element.prepend(icon('fire-flame-curved', 'me-1'));
    return element;
  };
  const rolePill = (role, label) => pill(ROLES, role, label);
  const statusLabel = status => (STATUS[status] ? STATUS[status][0] : status);

  // ---- Toasts ----
  function toast(message, type = 'success', options = {}) {
    const region = document.getElementById('toastRegion') || document.body.appendChild(
      h('div', { id: 'toastRegion', class: 'toast-region', 'aria-live': 'polite' }),
    );
    const icons = { success: 'circle-check', error: 'circle-exclamation', info: 'circle-info', warning: 'triangle-exclamation' };
    const node = h('div', { class: `app-toast app-toast-${type}`, role: type === 'error' ? 'alert' : 'status' },
      icon(icons[type] || 'circle-info'),
      h('span', { class: 'flex-grow-1' }, message),
      options.action ? h('button', {
        type: 'button', class: 'btn btn-sm btn-link app-toast-action',
        onclick: () => { options.action.handler(); dismiss(); },
      }, options.action.label) : null,
      h('button', { type: 'button', class: 'btn-close btn-close-sm', 'aria-label': 'Fermer', onclick: () => dismiss() }),
    );
    function dismiss() {
      node.classList.add('leaving');
      setTimeout(() => node.remove(), 200);
    }
    region.appendChild(node);
    setTimeout(dismiss, options.duration || (type === 'error' ? 7000 : 4000));
    return dismiss;
  }

  // ---- Dialogues (remplacent window.confirm / prompt) ----
  function dialog({ title, body, confirmLabel = 'Confirmer', cancelLabel = 'Annuler', tone = 'primary' }) {
    return new Promise(resolve => {
      const content = typeof body === 'string' ? h('p', { class: 'mb-0' }, body) : body;
      const confirmButton = h('button', { type: 'submit', class: `btn btn-${tone}` }, confirmLabel);
      const formElement = h('form', { class: 'modal-content' },
        h('div', { class: 'modal-header' },
          h('h2', { class: 'modal-title fs-5' }, title),
          h('button', { type: 'button', class: 'btn-close', 'data-bs-dismiss': 'modal', 'aria-label': 'Fermer' })),
        h('div', { class: 'modal-body' }, content),
        h('div', { class: 'modal-footer' },
          h('button', { type: 'button', class: 'btn btn-light', 'data-bs-dismiss': 'modal' }, cancelLabel),
          confirmButton),
      );
      const wrapper = h('div', { class: 'modal fade', tabindex: '-1', 'aria-hidden': 'true' },
        h('div', { class: 'modal-dialog modal-dialog-centered' }, formElement));
      document.body.appendChild(wrapper);
      const modal = new bootstrap.Modal(wrapper);
      let result = false;
      formElement.addEventListener('submit', event => {
        event.preventDefault();
        result = true;
        modal.hide();
      });
      wrapper.addEventListener('shown.bs.modal', () => confirmButton.focus());
      wrapper.addEventListener('hidden.bs.modal', () => {
        wrapper.remove();
        resolve(result);
      });
      modal.show();
    });
  }

  const confirmDialog = (title, body, options = {}) => dialog({ title, body, ...options });

  // Formulaire modal dont la soumission est asynchrone (le dialogue reste ouvert en cas d'erreur).
  function formDialog({ title, fields, confirmLabel = 'Enregistrer', tone = 'primary', size = '', onSubmit }) {
    return new Promise(resolve => {
      const errorBox = h('div', { class: 'dialog-error small text-danger mt-2', role: 'alert' });
      const submit = h('button', { type: 'submit', class: `btn btn-${tone}` }, confirmLabel);
      const formElement = h('form', { class: 'modal-content' },
        h('div', { class: 'modal-header' },
          h('h2', { class: 'modal-title fs-5' }, title),
          h('button', { type: 'button', class: 'btn-close', 'data-bs-dismiss': 'modal', 'aria-label': 'Fermer' })),
        h('div', { class: 'modal-body' }, fields, errorBox),
        h('div', { class: 'modal-footer' },
          h('button', { type: 'button', class: 'btn btn-light', 'data-bs-dismiss': 'modal' }, 'Annuler'),
          submit),
      );
      const wrapper = h('div', { class: 'modal fade', tabindex: '-1', 'aria-hidden': 'true' },
        h('div', { class: `modal-dialog modal-dialog-centered modal-dialog-scrollable ${size}` }, formElement));
      document.body.appendChild(wrapper);
      const modal = new bootstrap.Modal(wrapper);
      let result = null;
      formElement.addEventListener('submit', async event => {
        event.preventDefault();
        if (!formElement.checkValidity()) {
          formElement.classList.add('was-validated');
          return;
        }
        errorBox.textContent = '';
        setBusy(submit, true);
        try {
          result = (await onSubmit(new FormData(formElement), formElement)) ?? true;
          modal.hide();
        } catch (error) {
          errorBox.textContent = error.message || 'Une erreur est survenue.';
        } finally {
          setBusy(submit, false);
        }
      });
      wrapper.addEventListener('shown.bs.modal', () => {
        const field = wrapper.querySelector('input:not([type=hidden]):not([readonly]), select, textarea');
        if (field) field.focus();
      });
      wrapper.addEventListener('hidden.bs.modal', () => {
        wrapper.remove();
        resolve(result);
      });
      modal.show();
    });
  }

  function setBusy(button, busy) {
    if (!button) return;
    button.disabled = busy;
    button.classList.toggle('is-busy', busy);
  }

  // ---- Champs de formulaire ----
  function field(label, input, { col = 'col-12', hint } = {}) {
    if (!input.id) input.id = `field-${Math.random().toString(36).slice(2, 9)}`;
    return h('div', { class: col },
      h('label', { class: 'form-label', for: input.id }, label),
      input,
      hint ? h('div', { class: 'form-text' }, hint) : null);
  }

  function select(name, options, value, attrs = {}) {
    const element = h('select', { class: 'form-select', name, ...attrs });
    options.forEach(([optionValue, label]) => {
      const option = new Option(label, optionValue);
      if (String(optionValue) === String(value ?? '')) option.selected = true;
      element.add(option);
    });
    return element;
  }

  const input = (name, attrs = {}) => h('input', { class: 'form-control', name, ...attrs });
  const textarea = (name, attrs = {}) => {
    const { value, ...rest } = attrs;
    const element = h('textarea', { class: 'form-control', name, rows: 3, ...rest });
    if (value) element.value = value;
    return element;
  };

  // ---- États ----
  function skeleton(lines = 4) {
    return h('div', { class: 'skeleton-block', 'aria-busy': 'true', 'aria-label': 'Chargement' },
      Array.from({ length: lines }, (_, index) => h('div', { class: 'skeleton-line', style: { width: `${90 - (index % 3) * 15}%` } })));
  }

  function emptyState(iconName, title, text, action) {
    return h('div', { class: 'empty-state' },
      h('div', { class: 'empty-icon' }, icon(iconName)),
      h('h3', { class: 'h6 mb-1' }, title),
      text ? h('p', { class: 'text-secondary small mb-3' }, text) : null,
      action || null);
  }

  function errorState(error, retry) {
    return emptyState('plug-circle-exclamation', 'Chargement impossible', error.message,
      retry ? h('button', { type: 'button', class: 'btn btn-sm btn-outline-primary', onclick: retry }, icon('rotate-right', 'me-1'), 'Réessayer') : null);
  }

  // ---- Graphiques légers (SVG / CSS, sans dépendance) ----
  function barChart(points, { height = 140, label = 'Signalements' } = {}) {
    const max = Math.max(1, ...points.map(point => point.count));
    const width = 100 / Math.max(points.length, 1);
    const svgNS = 'http://www.w3.org/2000/svg';
    const svg = document.createElementNS(svgNS, 'svg');
    svg.setAttribute('viewBox', `0 0 100 ${height}`);
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.setAttribute('class', 'bar-chart');
    svg.setAttribute('role', 'img');
    const total = points.reduce((sum, point) => sum + point.count, 0);
    svg.setAttribute('aria-label', `${label} sur ${points.length} jours : ${total} au total`);
    points.forEach((point, index) => {
      const barHeight = point.count ? Math.max(3, (point.count / max) * (height - 8)) : 1.5;
      const rect = document.createElementNS(svgNS, 'rect');
      rect.setAttribute('x', index * width + width * 0.15);
      rect.setAttribute('y', height - barHeight);
      rect.setAttribute('width', width * 0.7);
      rect.setAttribute('height', barHeight);
      rect.setAttribute('rx', 1);
      rect.setAttribute('class', point.count ? 'bar' : 'bar bar-empty');
      const title = document.createElementNS(svgNS, 'title');
      title.textContent = `${formatDate(point.date)} : ${point.count}`;
      rect.appendChild(title);
      svg.appendChild(rect);
    });
    const first = points[0];
    const last = points[points.length - 1];
    return h('div', { class: 'chart-wrap' }, svg,
      h('div', { class: 'chart-axis' },
        h('span', {}, first ? formatDate(first.date) : ''),
        h('span', {}, last ? formatDate(last.date) : '')));
  }

  function distribution(items, { tones = {}, emptyText = 'Aucune donnée.' } = {}) {
    const rows = items.filter(item => item.count > 0);
    if (!rows.length) return h('p', { class: 'text-secondary small mb-0' }, emptyText);
    const max = Math.max(...rows.map(item => item.count));
    const total = rows.reduce((sum, item) => sum + item.count, 0);
    return h('ul', { class: 'distribution list-unstyled mb-0' }, rows.map(item => h('li', {},
      h('div', { class: 'd-flex justify-content-between small mb-1' },
        h('span', {}, item.label || item.key || '—'),
        h('strong', {}, `${item.count}`, h('span', { class: 'text-secondary fw-normal ms-1' }, `(${Math.round(item.count / total * 100)} %)`))),
      h('div', { class: 'distribution-track' },
        h('span', { class: `distribution-bar tone-${tones[item.key] || (STATUS[item.key] || PRIORITY[item.key] || [null, 'primary'])[1]}`, style: { width: `${(item.count / max) * 100}%` } })),
    )));
  }

  function donut(value, label) {
    const safe = Math.max(0, Math.min(100, Number(value) || 0));
    return h('div', { class: 'donut', style: { '--value': safe }, role: 'img', 'aria-label': `${label} : ${safe} %` },
      h('div', { class: 'donut-inner' }, h('strong', {}, `${safe.toString().replace('.', ',')} %`), h('span', {}, label)));
  }

  function statCard({ label, value, iconName, tone = 'primary', hint, onClick }) {
    const card = h(onClick ? 'button' : 'article', {
      class: `stat-card${onClick ? ' is-clickable' : ''}`, type: onClick ? 'button' : null, onclick: onClick || null,
    },
    h('span', { class: `stat-icon tone-${tone}` }, icon(iconName)),
    h('div', { class: 'stat-body' },
      h('span', { class: 'stat-label' }, label),
      h('strong', { class: 'stat-value' }, value ?? '—'),
      hint ? h('span', { class: 'stat-hint' }, hint) : null));
    return card;
  }

  async function copyText(text) {
    try {
      await navigator.clipboard.writeText(text);
      toast('Copié dans le presse-papiers.', 'info', { duration: 2000 });
    } catch (error) {
      toast(`Code : ${text}`, 'info');
    }
  }

  function suggestPassword() {
    const alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789';
    const values = crypto.getRandomValues(new Uint32Array(12));
    return `${Array.from(values, value => alphabet[value % alphabet.length]).join('')}!7`;
  }

  window.UI = {
    h, icon, debounce, listItems, formatDate, timeAgo, formatNumber, formatPercent, formatHours, initials,
    statusPill, priorityPill, rolePill, statusLabel, STATUS, PRIORITY, ROLES,
    toast, dialog, confirmDialog, formDialog, setBusy, field, select, input, textarea,
    skeleton, emptyState, errorState, barChart, distribution, donut, statCard, copyText, suggestPassword,
  };
})();
