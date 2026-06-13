<script setup>
defineProps({
  version: { type: Object, default: null },
  versions: { type: Array, default: () => [] },
  busy: { type: Boolean, default: false },
});

defineEmits(['draft', 'publish', 'save', 'select-version']);
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
    <div v-if="versions.length" class="version-history">
      <h3>Version history</h3>
      <button
        v-for="item in versions"
        :key="item.id"
        type="button"
        :class="{ active: item.id === version?.id }"
        @click="$emit('select-version', item)"
      >
        <span>v{{ item.version_number }}</span>
        <strong>{{ item.status }}</strong>
        <small>{{ item.published_at ? new Date(item.published_at).toLocaleDateString() : 'Not published' }}</small>
      </button>
    </div>
    <button type="button" class="primary-action" :disabled="busy || (version && version.status !== 'draft')" @click="$emit('save')">
      {{ version ? 'Save draft' : 'Create chapter draft' }}
    </button>
    <button type="button" :disabled="busy || !version || version.status === 'draft'" @click="$emit('draft')">
      Create draft
    </button>
    <button type="button" :disabled="busy || !version || version.status !== 'draft'" @click="$emit('publish')">
      Publish
    </button>
    <p class="muted">Publishing replaces the learner-visible version. Draft edits stay hidden until published.</p>
  </aside>
</template>
