<script setup>
import { reactive, watch } from 'vue';
import RichTextEditor from './RichTextEditor.vue';

const props = defineProps({
  exhibit: { type: Object, default: null },
  busy: { type: Boolean, default: false },
});

const emit = defineEmits(['save', 'delete']);

const form = reactive({
  title: '',
  field_type: 'html',
  field_format: '',
  content: '',
  media_asset_id: '',
  sort_order: 0,
});

watch(
  () => props.exhibit,
  (value) => {
    form.title = value?.title || '';
    form.field_type = value?.field_type || 'html';
    form.field_format = value?.field_format || '';
    form.content = value?.content || '';
    form.media_asset_id = value?.media_asset_id || '';
    form.sort_order = value?.sort_order ?? 0;
  },
  { immediate: true },
);

function payload() {
  return {
    title: form.title,
    field_type: form.field_type,
    field_format: form.field_format || null,
    content: form.content || null,
    media_asset_id: form.media_asset_id ? Number(form.media_asset_id) : null,
    sort_order: Number(form.sort_order || 0),
  };
}
</script>

<template>
  <section class="editor-subpanel">
    <div class="panel-heading">
      <div>
        <p class="section-label">Exhibit</p>
        <h3>{{ exhibit?.id ? 'Edit exhibit' : 'New exhibit' }}</h3>
      </div>
      <button v-if="exhibit?.id" type="button" :disabled="busy" @click="$emit('delete', exhibit)">Delete</button>
    </div>
    <label>
      Title
      <input v-model.trim="form.title" :disabled="busy" required />
    </label>
    <div class="form-row">
      <label>
        Field type
        <select v-model="form.field_type" :disabled="busy">
          <option value="html">HTML</option>
          <option value="link">Link</option>
          <option value="image">Image</option>
          <option value="audio">Audio</option>
          <option value="video">Video</option>
        </select>
      </label>
      <label>
        Field format
        <input v-model.trim="form.field_format" :disabled="busy" placeholder="story, shloka, example" />
      </label>
      <label>
        Order
        <input v-model.number="form.sort_order" :disabled="busy" type="number" />
      </label>
    </div>
    <label v-if="form.field_type === 'html'">
      Value
      <RichTextEditor v-model="form.content" :disabled="busy" placeholder="Exhibit HTML" />
    </label>
    <label v-else>
      Value or URL
      <input v-model.trim="form.content" :disabled="busy" />
    </label>
    <label>
      Media asset ID
      <input v-model.number="form.media_asset_id" :disabled="busy" type="number" min="1" placeholder="Optional" />
    </label>
    <button type="button" class="primary-action" :disabled="busy || !form.title" @click="$emit('save', payload())">
      Save exhibit
    </button>
  </section>
</template>
