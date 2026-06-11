<script setup>
import { onMounted, ref } from 'vue';
import { listMedia, uploadMedia } from './adminApi';

const media = ref([]);
const file = ref(null);
const altText = ref('');
const busy = ref(false);
const error = ref('');
const notice = ref('');

async function refresh() {
  media.value = await listMedia();
}

function pick(event) {
  file.value = event.target.files?.[0] || null;
}

async function submit() {
  if (!file.value) return;
  busy.value = true;
  error.value = '';
  notice.value = '';
  try {
    await uploadMedia(file.value, altText.value);
    file.value = null;
    altText.value = '';
    await refresh();
    notice.value = 'Media uploaded.';
  } catch (err) {
    error.value = err.message || 'Unable to upload media';
  } finally {
    busy.value = false;
  }
}

async function copyId(id) {
  await navigator.clipboard?.writeText(String(id));
  notice.value = `Asset ID ${id} copied.`;
}

onMounted(refresh);
</script>

<template>
  <section class="admin-data-page">
    <header class="page-heading">
      <p class="section-label">Media</p>
      <h1>Media library</h1>
      <p class="lede">Upload images, audio, video, and PDFs for exhibits. Copy asset IDs into exhibit records.</p>
    </header>
    <p v-if="error" class="form-error">{{ error }}</p>
    <p v-if="notice" class="form-success">{{ notice }}</p>

    <form class="learning-form media-upload" @submit.prevent="submit">
      <label>File<input type="file" accept="image/*,audio/*,video/*,application/pdf" required @change="pick" /></label>
      <label>Alt text<input v-model.trim="altText" /></label>
      <button class="primary-action" type="submit" :disabled="busy || !file">{{ busy ? 'Uploading...' : 'Upload media' }}</button>
    </form>

    <section class="data-table-panel">
      <h2>{{ media.length }} assets</h2>
      <table class="admin-table">
        <thead><tr><th>ID</th><th>Name</th><th>Type</th><th>Size</th><th>Alt text</th><th></th></tr></thead>
        <tbody>
          <tr v-for="asset in media" :key="asset.id">
            <td>{{ asset.id }}</td>
            <td>{{ asset.original_filename || asset.storage_key }}</td>
            <td>{{ asset.mime_type }}</td>
            <td>{{ asset.size_bytes ? `${Math.round(asset.size_bytes / 1024)} KB` : '-' }}</td>
            <td>{{ asset.alt_text || '-' }}</td>
            <td><button type="button" @click="copyId(asset.id)">Copy ID</button></td>
          </tr>
        </tbody>
      </table>
    </section>
  </section>
</template>
