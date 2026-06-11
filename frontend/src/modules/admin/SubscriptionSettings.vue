<script setup>
import { onMounted, reactive, ref } from 'vue';
import { listSubscriptions, updateSubscription } from './adminApi';

const subscriptions = ref([]);
const selected = ref(null);
const busy = ref(false);
const error = ref('');
const notice = ref('');

const form = reactive({
  status: 'active',
  starts_at: '',
  expires_at: '',
  grace_until: '',
  contract_notes: '',
});

function toInput(value) {
  return value ? String(value).slice(0, 16) : '';
}

function toApi(value) {
  return value ? new Date(value).toISOString() : null;
}

function fill(subscription) {
  selected.value = subscription;
  form.status = subscription.status;
  form.starts_at = toInput(subscription.starts_at);
  form.expires_at = toInput(subscription.expires_at);
  form.grace_until = toInput(subscription.grace_until);
  form.contract_notes = subscription.contract_notes || '';
}

async function refresh() {
  subscriptions.value = await listSubscriptions();
  if (!selected.value && subscriptions.value[0]) fill(subscriptions.value[0]);
}

async function save() {
  if (!selected.value) return;
  busy.value = true;
  error.value = '';
  notice.value = '';
  try {
    await updateSubscription(selected.value.id, {
      status: form.status,
      starts_at: toApi(form.starts_at),
      expires_at: toApi(form.expires_at),
      grace_until: toApi(form.grace_until),
      contract_notes: form.contract_notes || null,
    });
    await refresh();
    notice.value = 'Subscription updated.';
  } catch (err) {
    error.value = err.message || 'Unable to update subscription';
  } finally {
    busy.value = false;
  }
}

onMounted(refresh);
</script>

<template>
  <section class="admin-data-page">
    <header class="page-heading">
      <p class="section-label">Subscriptions</p>
      <h1>Manual school access control</h1>
      <p class="lede">Set active, grace, expired, or suspended status for school learning access.</p>
    </header>
    <p v-if="error" class="form-error">{{ error }}</p>
    <p v-if="notice" class="form-success">{{ notice }}</p>

    <div class="admin-data-grid">
      <section class="data-table-panel">
        <h2>{{ subscriptions.length }} subscriptions</h2>
        <table class="admin-table">
          <thead><tr><th>School</th><th>Plan</th><th>Status</th><th>Expires</th><th></th></tr></thead>
          <tbody>
            <tr v-for="item in subscriptions" :key="item.id">
              <td>{{ item.organization_name || item.organization_id }}</td>
              <td>{{ item.plan_name || item.plan_id }}</td>
              <td>{{ item.status }}</td>
              <td>{{ item.expires_at ? new Date(item.expires_at).toLocaleDateString() : '-' }}</td>
              <td><button type="button" @click="fill(item)">Edit</button></td>
            </tr>
          </tbody>
        </table>
      </section>

      <form class="learning-form" @submit.prevent="save">
        <h2>{{ selected?.organization_name || 'Select subscription' }}</h2>
        <label>Status<select v-model="form.status"><option>active</option><option>grace</option><option>expired</option><option>suspended</option></select></label>
        <label>Starts at<input v-model="form.starts_at" type="datetime-local" /></label>
        <label>Expires at<input v-model="form.expires_at" type="datetime-local" /></label>
        <label>Grace until<input v-model="form.grace_until" type="datetime-local" /></label>
        <label>Contract notes<textarea v-model.trim="form.contract_notes" /></label>
        <button class="primary-action" type="submit" :disabled="busy || !selected">{{ busy ? 'Saving...' : 'Save subscription' }}</button>
      </form>
    </div>
  </section>
</template>
