import axios from "axios";
import { clearAuth, getToken, saveAuth } from "../utils/storage";

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    "Content-Type": "application/json",
  },
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
  },
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
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    saveAuth(data.access_token, data.user);
    return data;
  },
  async me() {
    const { data } = await api.get("/auth/me");
    return data;
  },
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
  },
  async updateMemberRole(projectId, userId, role) {
    const { data } = await api.patch(
      `/projects/${projectId}/members/${userId}/role`,
      {
        role,
      },
    );

    return data;
  },

  async removeMember(projectId, userId) {
    await api.delete(`/projects/${projectId}/members/${userId}`);
  },
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
    const { data } = await api.patch(
      `/projects/${projectId}/columns/${columnId}`,
      payload,
    );
    return data;
  },
  async remove(projectId, columnId) {
    await api.delete(`/projects/${projectId}/columns/${columnId}`);
  },
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
    const { data } = await api.patch(
      `/projects/${projectId}/issues/${issueId}`,
      payload,
    );
    return data;
  },
  async move(projectId, issueId, payload) {
    const { data } = await api.patch(
      `/projects/${projectId}/issues/${issueId}/move`,
      payload,
    );
    return data;
  },
  async search(projectId, params = {}) {
    const cleanParams = {};

    Object.entries(params).forEach(([key, value]) => {
      if (value !== "" && value !== null && value !== undefined) {
        cleanParams[key] = value;
      }
    });

    const { data } = await api.get(`/projects/${projectId}/issues/search`, {
      params: cleanParams,
    });

    return data;
  },
  async remove(projectId, issueId) {
    await api.delete(`/projects/${projectId}/issues/${issueId}`);
  },
};

export const commentApi = {
  async list(issueId) {
    const { data } = await api.get(`/issues/${issueId}/comments`);
    return data;
  },
  async create(issueId, payload) {
    const { data } = await api.post(`/issues/${issueId}/comments`, payload);
    return data;
  },
};

export const activityApi = {
  async listProjectLog(projectId, { limit = 50, offset = 0 } = {}) {
    const { data } = await api.get(`/projects/${projectId}/activity-logs`, {
      params: { limit, offset },
    });
    return data;
  },

  async listIssueLog(issueId, { limit = 50, offset = 0 } = {}) {
    const { data } = await api.get(`/issues/${issueId}/activity-logs`, {
      params: { limit, offset },
    });
    return data;
  },
};

export const notificationApi = {
  async list({ unreadOnly = false, limit = 30 } = {}) {
    const { data } = await api.get("/notifications", {
      params: { unread_only: unreadOnly, limit },
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
  },
};

export const checklistApi = {
  async list(issueId) {
    const { data } = await api.get(`/issues/${issueId}/checklists`);
    return data;
  },

  async create(issueId, payload) {
    const { data } = await api.post(`/issues/${issueId}/checklists`, payload);
    return data;
  },

  async update(checklistId, payload) {
    const { data } = await api.patch(`/checklists/${checklistId}`, payload);
    return data;
  },

  async remove(checklistId) {
    await api.delete(`/checklists/${checklistId}`);
  },
};

export const dashboardApi = {
  async summary(projectId) {
    const { data } = await api.get(`/projects/${projectId}/dashboard/summary`);
    return data;
  },

  async issuesByStatus(projectId) {
    const { data } = await api.get(
      `/projects/${projectId}/dashboard/issues-by-status`,
    );
    return data;
  },

  async issuesByPriority(projectId) {
    const { data } = await api.get(
      `/projects/${projectId}/dashboard/issues-by-priority`,
    );
    return data;
  },

  async issuesByAssignee(projectId) {
    const { data } = await api.get(
      `/projects/${projectId}/dashboard/issues-by-assignee`,
    );
    return data;
  },

  async recentActivity(projectId, limit = 8) {
    const { data } = await api.get(
      `/projects/${projectId}/dashboard/recent-activity`,
      {
        params: { limit },
      },
    );

    return data;
  },
};

export const attachmentApi = {
  async list(issueId) {
    const { data } = await api.get(`/issues/${issueId}/attachments`);
    return data;
  },

  async upload(issueId, file, onProgress) {
    const formData = new FormData();
    formData.append("file", file);

    const { data } = await api.post(
      `/issues/${issueId}/attachments`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent) => {
          if (!progressEvent.total || !onProgress) return;

          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total,
          );
          onProgress(percent);
        },
      },
    );

    return data;
  },

  async uploadMany(issueId, files, onProgress) {
    const formData = new FormData();

    Array.from(files).forEach((file) => {
      formData.append("files", file);
    });

    const { data } = await api.post(
      `/issues/${issueId}/attachments/bulk`,
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data",
        },
        onUploadProgress: (progressEvent) => {
          if (!progressEvent.total || !onProgress) return;

          const percent = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total,
          );
          onProgress(percent);
        },
      },
    );

    return data;
  },

  async preview(issueId, attachmentId) {
    const response = await api.get(
      `/issues/${issueId}/attachments/${attachmentId}/view`,
      {
        responseType: "blob",
      },
    );

    return response.data;
  },

  async download(issueId, attachmentId) {
    const response = await api.get(
      `/issues/${issueId}/attachments/${attachmentId}/download`,
      {
        responseType: "blob",
      },
    );

    return response.data;
  },

  async remove(issueId, attachmentId) {
    await api.delete(`/issues/${issueId}/attachments/${attachmentId}`);
  },
};

export { api, getErrorMessage };
