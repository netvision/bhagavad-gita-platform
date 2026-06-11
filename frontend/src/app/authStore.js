import { defineStore } from 'pinia';
import { api } from './apiClient';

const TOKEN_KEY = 'gita.token';
const USER_KEY = 'gita.user';

function readStoredUser() {
  try {
    return JSON.parse(localStorage.getItem(USER_KEY) || 'null');
  } catch {
    localStorage.removeItem(USER_KEY);
    return null;
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    user: readStoredUser(),
  }),

  getters: {
    isAuthenticated: (state) => Boolean(state.token && state.user?.role),
  },

  actions: {
    async login(identifier, password) {
      const data = await api('/api/auth/login', {
        method: 'POST',
        body: { identifier, password },
      });

      this.token = data.access_token;
      this.user = data.user;
      localStorage.setItem(TOKEN_KEY, this.token);
      localStorage.setItem(USER_KEY, JSON.stringify(this.user));
      return data;
    },

    logout() {
      this.token = '';
      this.user = null;
      localStorage.removeItem(TOKEN_KEY);
      localStorage.removeItem(USER_KEY);
    },

    hasRole(role) {
      return this.user?.role === role;
    },

    hasAnyRole(roles) {
      return roles.includes(this.user?.role);
    },

    clearInvalidSession() {
      if (this.token && !this.user?.role) this.logout();
    },
  },
});
