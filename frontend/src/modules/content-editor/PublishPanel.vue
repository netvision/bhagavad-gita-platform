<script setup>
defineProps({
  version: { type: Object, default: null },
  busy: { type: Boolean, default: false },
});

defineEmits(['draft', 'publish', 'save']);
</script>

<template>
  <aside class="publish-panel">
    <p class="section-label">Publishing</p>
    <h2>{{ version?.status || 'No version selected' }}</h2>
    <dl v-if="version">
      <div>
        <dt>Version</dt>
        <dd>{{ version.version_number }}</dd>
      </div>
      <div>
        <dt>Published</dt>
        <dd>{{ version.published_at ? new Date(version.published_at).toLocaleString() : 'Not published' }}</dd>
      </div>
    </dl>
    <button type="button" class="primary-action" :disabled="busy || !version || version.status !== 'draft'" @click="$emit('save')">
      Save draft
    </button>
    <button type="button" :disabled="busy || !version" @click="$emit('draft')">
      Create draft
    </button>
    <button type="button" :disabled="busy || !version || version.status !== 'draft'" @click="$emit('publish')">
      Publish
    </button>
    <p class="muted">Publishing replaces the learner-visible version. Draft edits stay hidden until published.</p>
  </aside>
</template>
