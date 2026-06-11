<script setup>
import { onMounted, reactive, ref } from 'vue';
import { createUser, listUsers, resetPasswordToken, setUserActive, updateUser } from './adminApi';

const users = ref([]);
const selected = ref(null);
const busy = ref(false);
const error = ref('');
const notice = ref('');
const tempPassword = ref('');

const form = reactive({
  organization_id: 1,
  email: '',
  username: '',
  password: '',
  full_name: '',
  role: 'student',
  grade_label: '',
  section_label: '',
  is_active: true,
});

function fill(user = null) {
  selected.value = user;
  form.organization_id = user?.organization_id || 1;
  form.email = user?.email || '';
  form.username = user?.username || '';
  form.password = '';
  form.full_name = user?.full_name || '';
  form.role = user?.role || 'student';
  form.grade_label = user?.grade_label || '';
  form.section_label = user?.section_label || '';
  form.is_active = user?.is_active ?? true;
  tempPassword.value = '';
}

function payload(includePassword = false) {
  const data = {
    organization_id: Number(form.organization_id),
    email: form.email || null,
    username: form.username,
    full_name: form.full_name || null,
    role: form.role,
    grade_label: form.grade_label || null,
    section_label: form.section_label || null,
    is_active: form.is_active,
  };
  if (includePassword) data.password = form.password;
  return data;
}

async function refresh() {
  users.value = await listUsers();
}

async function run(action) {
  busy.value = true;
  error.value = '';
  notice.value = '';
  try {
    await action();
  } catch (err) {
    error.value = err.message || 'User action failed';
  } finally {
    busy.value = false;
  }
}

async function save() {
  await run(async () => {
    if (selected.value) {
      await updateUser(selected.value.id, payload(false));
      notice.value = 'User updated.';
    } else {
      await createUser(payload(true));
      notice.value = 'User created.';
    }
    await refresh();
  });
}

async function toggle(user) {
  await run(async () => {
    await setUserActive(user.id, !user.is_active);
    await refresh();
  });
}

async function reset(user) {
  await run(async () => {
    const data = await resetPasswordToken(user.id);
    tempPassword.value = data.temporary_password;
    notice.value = `Temporary password generated for ${user.username}.`;
  });
}

onMounted(() => run(refresh));
</script>

<template>
  <section class="admin-data-page">
    <header class="page-heading">
      <p class="section-label">Users</p>
      <h1>Students, teachers, and admins</h1>
      <p class="lede">Manage username/admission-number accounts, teacher email login, and content admin access.</p>
    </header>
    <p v-if="error" class="form-error">{{ error }}</p>
    <p v-if="notice" class="form-success">{{ notice }} <strong v-if="tempPassword">{{ tempPassword }}</strong></p>

    <div class="admin-data-grid">
      <section class="data-table-panel">
        <div class="panel-heading">
          <h2>{{ users.length }} users</h2>
          <button type="button" @click="fill(null)">New user</button>
        </div>
        <table class="admin-table">
          <thead><tr><th>Name</th><th>Login</th><th>Role</th><th>Grade</th><th>Status</th><th></th></tr></thead>
          <tbody>
            <tr v-for="user in users" :key="user.id">
              <td>{{ user.full_name || user.username }}</td>
              <td>{{ user.email || user.username }}</td>
              <td>{{ user.role }}</td>
              <td>{{ [user.grade_label, user.section_label].filter(Boolean).join(' / ') || '-' }}</td>
              <td>{{ user.is_active ? 'active' : 'inactive' }}</td>
              <td class="table-actions">
                <button type="button" @click="fill(user)">Edit</button>
                <button type="button" @click="toggle(user)">{{ user.is_active ? 'Disable' : 'Enable' }}</button>
                <button type="button" @click="reset(user)">Reset</button>
              </td>
            </tr>
          </tbody>
        </table>
      </section>

      <form class="learning-form" @submit.prevent="save">
        <h2>{{ selected ? 'Edit user' : 'Create user' }}</h2>
        <label>Organization ID<input v-model.number="form.organization_id" type="number" min="1" required /></label>
        <label>Name<input v-model.trim="form.full_name" /></label>
        <label>Email<input v-model.trim="form.email" type="email" /></label>
        <label>Username / admission number<input v-model.trim="form.username" required /></label>
        <label v-if="!selected">Password<input v-model="form.password" type="password" minlength="8" required /></label>
        <div class="form-row">
          <label>Role<select v-model="form.role"><option>student</option><option>teacher</option><option>content_admin</option><option>super_admin</option></select></label>
          <label>Grade<input v-model.trim="form.grade_label" placeholder="Grade 9" /></label>
          <label>Section<input v-model.trim="form.section_label" placeholder="A" /></label>
        </div>
        <label class="check-row"><input v-model="form.is_active" type="checkbox" /> Active</label>
        <button class="primary-action" type="submit" :disabled="busy">{{ busy ? 'Saving...' : 'Save user' }}</button>
      </form>
    </div>
  </section>
</template>
