// Client HTTP partagé par toutes les pages de GIU.
const API_BASE_URL = '/api';

class ApiError extends Error {
  constructor(status, data) {
    super(ApiError.describe(status, data));
    this.status = status;
    this.data = data;
  }

  // Transforme les erreurs DRF ({champ: [messages]}) en phrase lisible.
  static describe(status, data) {
    if (data && typeof data === 'object') {
      if (typeof data.detail === 'string') return data.detail;
      if (typeof data.error === 'string') return data.error;
      const messages = Object.entries(data).flatMap(([field, value]) => {
        const list = Array.isArray(value) ? value : [value];
        return list
          .filter(item => typeof item === 'string')
          .map(item => (field === 'non_field_errors' ? item : `${field} : ${item}`));
      });
      if (messages.length) return messages.join(' ');
    }
    if (status === 0) return 'Impossible de joindre le serveur. Vérifiez votre connexion.';
    if (status === 403) return 'Vous n’avez pas les droits nécessaires pour cette action.';
    if (status === 404) return 'Élément introuvable.';
    if (status === 429) return 'Trop de tentatives. Patientez un instant puis réessayez.';
    return `Erreur du serveur (${status}). Réessayez.`;
  }
}

class APIClient {
  constructor() {
    this.token = localStorage.getItem('auth_token');
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  clearSession() {
    this.token = null;
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_data');
  }

  headers(body) {
    const headers = {};
    if (!(body instanceof FormData)) headers['Content-Type'] = 'application/json';
    if (this.token) headers.Authorization = `Token ${this.token}`;
    return headers;
  }

  async request(endpoint, options = {}) {
    const { raw = false, ...fetchOptions } = options;
    const config = {
      ...fetchOptions,
      headers: { ...this.headers(fetchOptions.body), ...fetchOptions.headers },
    };

    let response;
    try {
      response = await fetch(`${API_BASE_URL}${endpoint}`, config);
    } catch (error) {
      throw new ApiError(0, null);
    }

    if (response.status === 401 && this.token) {
      // Session expirée ou révoquée : retour à la connexion en conservant la page.
      this.clearSession();
      const next = encodeURIComponent(window.location.pathname + window.location.search);
      window.location.href = `/login/?next=${next}`;
    }
    if (!response.ok) {
      const data = await response.json().catch(() => null);
      throw new ApiError(response.status, data);
    }
    if (raw) return response;
    if (response.status === 204) return null;
    return response.json();
  }

  get(endpoint, params) {
    const query = params ? APIClient.query(params) : '';
    return this.request(`${endpoint}${query}`);
  }

  post(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'POST',
      body: data instanceof FormData ? data : JSON.stringify(data),
    });
  }

  patch(endpoint, data = {}) {
    return this.request(endpoint, {
      method: 'PATCH',
      body: data instanceof FormData ? data : JSON.stringify(data),
    });
  }

  delete(endpoint) {
    return this.request(endpoint, { method: 'DELETE' });
  }

  static query(params) {
    const search = new URLSearchParams();
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null && value !== '') search.set(key, value);
    });
    const text = search.toString();
    return text ? `?${text}` : '';
  }

  // Télécharge un fichier protégé par token (les liens <a> ne transmettent pas l'en-tête).
  async download(endpoint, params, fallbackName) {
    const response = await this.request(`${endpoint}${APIClient.query(params || {})}`, { raw: true });
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const match = disposition.match(/filename="([^"]+)"/);
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = match ? match[1] : fallbackName;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  // Authentification
  async logout() {
    try {
      if (this.token) await this.post('/auth/logout/');
    } finally {
      this.clearSession();
    }
  }

  // Users
  getUsers(params) { return this.get('/users/users/', params); }
  getUser(id) { return this.get(`/users/users/${id}/`); }
  getUserStats() { return this.get('/users/users/stats/'); }
  getCurrentUser() { return this.get('/users/users/me/'); }
  updateProfile(data) { return this.patch('/users/users/me/', data); }
  changePassword(data) { return this.post('/users/users/change_password/', data); }
  createUser(data) { return this.post('/users/users/', data); }
  updateUser(id, data) { return this.patch(`/users/users/${id}/`, data); }
  deleteUser(id) { return this.delete(`/users/users/${id}/`); }
  toggleUserActive(id) { return this.post(`/users/users/${id}/toggle_active/`); }
  resetUserPassword(id, newPassword) {
    return this.post(`/users/users/${id}/reset_password/`, { new_password: newPassword });
  }

  // Incidents
  getCategories() { return this.get('/incidents/categories/'); }
  getIncidents(params) { return this.get('/incidents/incidents/', params); }
  getIncident(id) { return this.get(`/incidents/incidents/${id}/`); }
  deleteIncident(id) { return this.delete(`/incidents/incidents/${id}/`); }
  createIncident(data) { return this.post('/incidents/incidents/', data); }
  updateIncident(id, data) { return this.patch(`/incidents/incidents/${id}/`, data); }
  updateIncidentStatus(id, status, comment = '') {
    return this.post(`/incidents/incidents/${id}/update_status/`, { status, comment });
  }
  commentIncident(id, comment) {
    return this.post(`/incidents/incidents/${id}/comment/`, { comment });
  }
  getMyIncidents() { return this.get('/incidents/incidents/my_incidents/'); }
  exportIncidents(params) {
    return this.download('/incidents/incidents/export/', params, 'incidents.csv');
  }
  trackIncident(code) { return this.get(`/incidents/track/${encodeURIComponent(code)}/`); }

  // Assets
  getAssetTypes() { return this.get('/assets/types/'); }
  getAssets(params) { return this.get('/assets/assets/', params); }
  getAsset(id) { return this.get(`/assets/assets/${id}/`); }
  getAssetStats() { return this.get('/assets/assets/stats/'); }
  createAsset(data) { return this.post('/assets/assets/', data); }
  updateAsset(id, data) { return this.patch(`/assets/assets/${id}/`, data); }
  deleteAsset(id) { return this.delete(`/assets/assets/${id}/`); }
  addAssetHistory(data) { return this.post('/assets/history/', data); }

  // Interventions
  getInterventions(params) { return this.get('/interventions/interventions/', params); }
  getIntervention(id) { return this.get(`/interventions/interventions/${id}/`); }
  createIntervention(data) { return this.post('/interventions/interventions/', data); }
  updateIntervention(id, data) { return this.patch(`/interventions/interventions/${id}/`, data); }
  updateInterventionStatus(id, status, comment = '', photo = null) {
    if (photo) {
      const form = new FormData();
      form.append('status', status);
      form.append('comment', comment);
      form.append('photo', photo);
      return this.post(`/interventions/interventions/${id}/update_status/`, form);
    }
    return this.post(`/interventions/interventions/${id}/update_status/`, { status, comment });
  }
  getMyInterventions() { return this.get('/interventions/interventions/my_interventions/'); }

  // Reports
  getGlobalStatistics() { return this.get('/reports/reports/global_statistics/'); }
  getDashboardSummary() { return this.get('/reports/reports/dashboard_summary/'); }
  generateReport(data) { return this.post('/reports/reports/generate_monthly_report/', data); }
  getReports() { return this.get('/reports/reports/'); }
  deleteReport(id) { return this.delete(`/reports/reports/${id}/`); }
  getKpiMetrics() { return this.get('/reports/metrics/'); }
  snapshotKpi() { return this.post('/reports/reports/snapshot_kpi/'); }

  // Notifications
  getNotifications(params) { return this.get('/notifications/', params); }
  getUnreadNotificationCount() { return this.get('/notifications/unread_count/'); }
  markNotificationRead(id) { return this.patch(`/notifications/${id}/`, { is_read: true }); }
  markAllNotificationsRead() { return this.post('/notifications/mark_all_read/'); }
}

// Global API client instance
const apiClient = new APIClient();

// Export for use in other files
window.ApiError = ApiError;
window.APIClient = APIClient;
window.apiClient = apiClient;
