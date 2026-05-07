const API_BASE = '/api';

async function request(path, options = {}) {
  const token = localStorage.getItem('admin_token');
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  if (token) {
    headers.Authorization = `Bearer ${token}`;
  }

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers
  });

  const text = await response.text();
  const data = text ? JSON.parse(text) : null;

  if (!response.ok) {
    const message = data?.message || data?.detail || `请求失败：${response.status}`;
    throw new Error(message);
  }

  return data;
}

export const api = {
  login(payload) {
    return request('/admin/login', {
      method: 'POST',
      body: JSON.stringify(payload)
    });
  },
  me() {
    return request('/admin/me');
  },
  logout() {
    return request('/admin/logout', { method: 'POST' });
  },
  dashboard() {
    return request('/admin/stats');
  },
  cardKeys(params = {}) {
    return request(`/admin/licenses${toQuery(params)}`);
  },
  createCardKey(payload) {
    const expiresAt = payload.days
      ? new Date(Date.now() + Number(payload.days) * 24 * 60 * 60 * 1000).toISOString()
      : null;
    return request('/admin/licenses', {
      method: 'POST',
      body: JSON.stringify({
        max_devices: Number(payload.max_devices || 1),
        expires_at: expiresAt,
        note: payload.remark || payload.note || ''
      })
    });
  },
  disableCardKey(id) {
    return request(`/admin/licenses/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ status: 'disabled' })
    });
  },
  bindings(params = {}) {
    return request(`/admin/clients${toQuery(params)}`);
  },
  unbindClient(id) {
    return request(`/admin/clients/${id}/unbind`, { method: 'POST' });
  },
  versions() {
    return request('/admin/releases');
  },
  publishVersion(payload) {
    return request('/admin/releases', {
      method: 'POST',
      body: JSON.stringify({
        version: payload.version,
        platform: 'windows',
        download_url: payload.download_url,
        changelog: payload.release_note || payload.changelog || '',
        mandatory: Boolean(payload.force_update || payload.mandatory),
        active: true
      })
    });
  },
  logs(params = {}) {
    return request(`/admin/events${toQuery(params)}`);
  }
};

function toQuery(params) {
  const query = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      query.set(key, value);
    }
  });
  const text = query.toString();
  return text ? `?${text}` : '';
}
