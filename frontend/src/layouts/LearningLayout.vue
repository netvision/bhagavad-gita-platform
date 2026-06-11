<script setup>
import { computed } from 'vue';
import { useRouter } from 'vue-router';
import { useAuthStore } from '../app/authStore';

const auth = useAuthStore();
const router = useRouter();

const displayName = computed(() => auth.user?.name || auth.user?.username || 'Learner');

function logout() {
  auth.logout();
  router.replace('/login');
}
</script>

<template>
  <div class="shell">
    <header class="topbar">
      <RouterLink class="brand-link" to="/learn">
        <span class="brand-mark">G</span>
        <span>Gita Learning</span>
      </RouterLink>
      <nav class="topnav" aria-label="Learning navigation">
        <RouterLink to="/learn">Dashboard</RouterLink>
        <RouterLink to="/journey">Journey</RouterLink>
        <RouterLink to="/reader">Reader</RouterLink>
        <RouterLink to="/feedback">Feedback</RouterLink>
        <RouterLink to="/reflections">Reflections</RouterLink>
      </nav>
      <div class="user-menu">
        <span>{{ displayName }}</span>
        <RouterLink v-if="auth.hasAnyRole(['content_admin', 'super_admin'])" to="/admin">Admin</RouterLink>
        <button type="button" @click="logout">Logout</button>
      </div>
    </header>

    <main class="content-shell">
      <RouterView />
    </main>
  </div>
</template>
