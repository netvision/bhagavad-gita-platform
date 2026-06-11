<script setup>
import { computed, reactive, ref } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useAuthStore } from '../../app/authStore';
import { defaultRouteForRole } from '../../app/permissions';

const auth = useAuthStore();
const route = useRoute();
const router = useRouter();
const error = ref('');
const busy = ref(false);

const form = reactive({
  identifier: '',
  password: '',
});

const destination = computed(() => {
  const redirect = route.query.redirect;
  return typeof redirect === 'string' && redirect.startsWith('/') ? redirect : null;
});

async function submit() {
  error.value = '';
  busy.value = true;

  try {
    await auth.login(form.identifier, form.password);
    await router.replace(destination.value || defaultRouteForRole(auth.user?.role));
  } catch (err) {
    error.value = err.message || 'Unable to sign in';
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <form class="login-form" @submit.prevent="submit">
    <label>
      Username or email
      <input v-model.trim="form.identifier" autocomplete="username" required />
    </label>
    <label>
      Password
      <input v-model="form.password" type="password" autocomplete="current-password" required />
    </label>
    <p v-if="error" class="form-error">{{ error }}</p>
    <button class="primary-action" type="submit" :disabled="busy">
      {{ busy ? 'Signing in...' : 'Sign in' }}
    </button>
  </form>
</template>
