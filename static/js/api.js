// Configuration API
const API_BASE_URL = 'http://localhost:8000/api';

class APIClient {
  constructor() {
    this.token = localStorage.getItem('auth_token');
  }

  setToken(token) {
    this.token = token;
    localStorage.setItem('auth_token', token);
  }

  async getHeaders() {
    const headers = {
      'Content-Type': 'application/json',
    };
    
    if (this.token) {
      headers['Authorization'] = `Token ${this.token}`;
    }
    
    return headers;
  }

  async request(endpoint, options = {}) {
    const url = `${API_BASE_URL}${endpoint}`;
    const headers = await this.getHeaders();
    
    const config = {
      ...options,
      headers: { ...headers, ...options.headers }
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        if (response.status === 401) {
          // Unauthorized - clear token and redirect
          this.token = null;
          localStorage.removeItem('auth_token');
          window.location.href = '/login.html';
        }
        throw new Error(`HTTP Error: ${response.status}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error('API Error:', error);
      throw error;
    }
  }

  // Users
  async getUsers() {
    return this.request('/users/users/');
  }

  async getCurrentUser() {
    return this.request('/users/users/me/');
  }

  async createUser(userData) {
    return this.request('/users/users/', {
      method: 'POST',
      body: JSON.stringify(userData)
    });
  }

  // Incidents
  async getIncidents() {
    return this.request('/incidents/incidents/');
  }

  async getIncident(id) {
    return this.request(`/incidents/incidents/${id}/`);
  }

  async createIncident(data) {
    return this.request('/incidents/incidents/', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async updateIncidentStatus(id, status, comment = '') {
    return this.request(`/incidents/incidents/${id}/update_status/`, {
      method: 'POST',
      body: JSON.stringify({ status, comment })
    });
  }

  async getMyIncidents() {
    return this.request('/incidents/incidents/my_incidents/');
  }

  // Assets
  async getAssets() {
    return this.request('/assets/assets/');
  }

  async getAsset(id) {
    return this.request(`/assets/assets/${id}/`);
  }

  async createAsset(data) {
    return this.request('/assets/assets/', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  // Interventions
  async getInterventions() {
    return this.request('/interventions/interventions/');
  }

  async getIntervention(id) {
    return this.request(`/interventions/interventions/${id}/`);
  }

  async createIntervention(data) {
    return this.request('/interventions/interventions/', {
      method: 'POST',
      body: JSON.stringify(data)
    });
  }

  async updateInterventionStatus(id, status, comment = '') {
    return this.request(`/interventions/interventions/${id}/update_status/`, {
      method: 'POST',
      body: JSON.stringify({ status, comment })
    });
  }

  async getMyInterventions() {
    return this.request('/interventions/interventions/my_interventions/');
  }

  // Reports
  async getGlobalStatistics() {
    return this.request('/reports/reports/global_statistics/');
  }

  async getIncidentsByStatus() {
    return this.request('/reports/reports/incidents_by_status/');
  }

  async getIncidentsByCategory() {
    return this.request('/reports/reports/incidents_by_category/');
  }

  async getKPISummary() {
    return this.request('/reports/reports/kpi_summary/');
  }

  async getRecentIncidents() {
    return this.request('/reports/reports/recent_incidents/');
  }

  async getPendingInterventions() {
    return this.request('/reports/reports/pending_interventions/');
  }
}

// Global API client instance
const apiClient = new APIClient();

// Utility functions
function showNotification(message, type = 'success') {
  const notification = document.createElement('div');
  notification.className = `notification notification-${type}`;
  notification.textContent = message;
  document.body.appendChild(notification);
  
  setTimeout(() => {
    notification.remove();
  }, 5000);
}

function formatDate(dateString) {
  const date = new Date(dateString);
  return date.toLocaleDateString('fr-FR', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
}

function getStatusBadge(status) {
  const statusMap = {
    'created': 'En attente',
    'validated': 'Validé',
    'planned': 'Planifié',
    'in_progress': 'En cours',
    'resolved': 'Résolu',
    'rejected': 'Rejeté',
    'pending': 'En attente',
    'assigned': 'Assignée',
    'completed': 'Complétée',
    'cancelled': 'Annulée'
  };
  
  const badgeClass = `badge badge-${status.replace('_', '-')}`;
  return `<span class="${badgeClass}">${statusMap[status] || status}</span>`;
}

function getPriorityBadge(priority) {
  const priorityMap = {
    'low': 'Basse',
    'medium': 'Moyenne',
    'high': 'Haute',
    'urgent': 'Urgente'
  };
  
  const colorMap = {
    'low': 'info',
    'medium': 'warning',
    'high': 'danger',
    'urgent': 'danger'
  };
  
  const badgeClass = `badge badge-${colorMap[priority]}`;
  return `<span class="${badgeClass}">${priorityMap[priority]}</span>`;
}

// Export for use in other files
window.APIClient = APIClient;
window.apiClient = apiClient;
window.showNotification = showNotification;
window.formatDate = formatDate;
window.getStatusBadge = getStatusBadge;
window.getPriorityBadge = getPriorityBadge;
