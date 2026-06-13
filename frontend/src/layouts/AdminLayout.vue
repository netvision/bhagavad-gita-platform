<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../app/authStore';

const auth = useAuthStore();
const router = useRouter();

const displayName = computed(() => auth.user?.name || auth.user?.username || 'Administrator');

function logout() {
  auth.logout();
  router.replace('/login');
}
</script>

<template>
  <div class="admin-shell">
    <aside class="admin-sidebar">
      <RouterLink class="brand-link" to="/admin">
        <span class="brand-mark">G</span>
        <span>Gita Admin</span>
      </RouterLink>
      <nav class="side-nav" aria-label="Admin navigation">
        <RouterLink v-if="auth.hasRole('super_admin')" to="/admin">Overview</RouterLink>
        <RouterLink to="/admin/content">Content</RouterLink>
        <RouterLink v-if="auth.hasRole('super_admin')" to="/admin/users">Users</RouterLink>
        <RouterLink v-if="auth.hasRole('super_admin')" to="/admin/subscription">Subscription</RouterLink>
        <RouterLink to="/admin/media">Media</RouterLink>
      </nav>
      <div class="side-footer">
        <span>{{ displayName }}</span>
        <RouterLink to="/learn">Learning app</RouterLink>
        <button type="button" @click="logout">Logout</button>
      </div>
    </aside>

    <main class="admin-main">
      <RouterView />
    </main>
  </div>
</template>
