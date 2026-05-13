import axios from "axios";
import { clearAuth, getToken, saveAuth } from "../utils/storage";

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json"
  }
});

api.interceptors.request.use((config) => {
  const token = getToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      clearAuth();
    }
    return Promise.reject(error);
  }
);

function getErrorMessage(error) {
  const detail = error.response?.data?.detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join("; ");
  }
  return detail || error.message || "Something went wrong";
}

export const authApi = {
  async register(payload) {
    const { data } = await api.post("/auth/register", payload);
    saveAuth(data.access_token, data.user);
    return data;
  },
  async login(email, password) {
    const form = new URLSearchParams();
    form.append("username", email);
    form.append("password", password);

    const { data } = await api.post("/auth/login", form, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" }
    });
    saveAuth(data.access_token, data.user);
    return data;
  },
  async me() {
    const { data } = await api.get("/auth/me");
    return data;
  }
};

export const projectApi = {
  async list() {
    const { data } = await api.get("/projects");
    return data;
  },
  async create(payload) {
    const { data } = await api.post("/projects", payload);
    return data;
  },
  async get(projectId) {
    const { data } = await api.get(`/projects/${projectId}`);
    return data;
  },
  async update(projectId, payload) {
    const { data } = await api.patch(`/projects/${projectId}`, payload);
    return data;
  },
  async members(projectId) {
    const { data } = await api.get(`/projects/${projectId}/members`);
    return data;
  },
  async addMember(projectId, payload) {
    const { data } = await api.post(`/projects/${projectId}/members`, payload);
    return data;
  }
};

export const columnApi = {
  async list(projectId) {
    const { data } = await api.get(`/projects/${projectId}/columns`);
    return data;
  },
  async create(projectId, payload) {
    const { data } = await api.post(`/projects/${projectId}/columns`, payload);
    return data;
  },
  async update(projectId, columnId, payload) {
    const { data } = await api.patch(`/projects/${projectId}/columns/${columnId}`, payload);
    return data;
  },
  async remove(projectId, columnId) {
    await api.delete(`/projects/${projectId}/columns/${columnId}`);
  }
};

export const issueApi = {
  async list(projectId) {
    const { data } = await api.get(`/projects/${projectId}/issues`);
    return data;
  },
  async create(projectId, payload) {
    const { data } = await api.post(`/projects/${projectId}/issues`, payload);
    return data;
  },
  async update(projectId, issueId, payload) {
    const { data } = await api.patch(`/projects/${projectId}/issues/${issueId}`, payload);
    return data;
  },
  async move(projectId, issueId, payload) {
    const { data } = await api.patch(`/projects/${projectId}/issues/${issueId}/move`, payload);
    return data;
  },
  async remove(projectId, issueId) {
    await api.delete(`/projects/${projectId}/issues/${issueId}`);
  }
};

export const commentApi = {
  async list(issueId) {
    const { data } = await api.get(`/issues/${issueId}/comments`);
    return data;
  },
  async create(issueId, payload) {
    const { data } = await api.post(`/issues/${issueId}/comments`, payload);
    return data;
  }
};

export const notificationApi = {
  async list({ unreadOnly = false, limit = 30 } = {}) {
    const { data } = await api.get("/notifications", {
      params: { unread_only: unreadOnly, limit }
    });
    return data;
  },
  async unreadCount() {
    const { data } = await api.get("/notifications/unread-count");
    return data;
  },
  async markRead(notificationId) {
    const { data } = await api.patch(`/notifications/${notificationId}/read`);
    return data;
  },
  async markAllRead() {
    const { data } = await api.patch("/notifications/read-all");
    return data;
  },
  async remove(notificationId) {
    await api.delete(`/notifications/${notificationId}`);
  }
};

export const attachmentApi = {
  async list(issueId) {
    const { data } = await api.get(`/issues/${issueId}/attachments`);
    return data;
  },

  async upload(issueId, file) {
    const formData = new FormData();
    formData.append("file", file);

    const { data } = await api.post(`/issues/${issueId}/attachments`, formData, {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    });

    return data;
  },

  async download(issueId, attachmentId) {
    const response = await api.get(`/issues/${issueId}/attachments/${attachmentId}/download`, {
      responseType: "blob"
    });

    return response.data;
  },

  async remove(issueId, attachmentId) {
    await api.delete(`/issues/${issueId}/attachments/${attachmentId}`);
  }
};

export { api, getErrorMessage };
