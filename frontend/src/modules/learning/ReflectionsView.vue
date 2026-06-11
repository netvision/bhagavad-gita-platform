<script setup>
import { onMounted, reactive, ref } from 'vue';
import SafeRichContent from '../../components/content/SafeRichContent.vue';
import { fetchLearningIndex, fetchReflections, postReflection } from './learningApi';

const chapters = ref([]);
const reflections = ref([]);
const busy = ref(false);
const loading = ref(true);
const error = ref('');
const saved = ref(false);
const form = reactive({
  chapter_id: null,
  visibility: 'private',
  body: '',
});

async function refresh() {
  const [index, items] = await Promise.all([fetchLearningIndex(), fetchReflections()]);
  chapters.value = index.chapters;
  reflections.value = items;
}

onMounted(async () => {
  try {
    await refresh();
  } catch (err) {
    error.value = err.message || 'Unable to load reflections';
  } finally {
    loading.value = false;
  }
});

async function submit() {
  busy.value = true;
  error.value = '';
  saved.value = false;
  try {
    await postReflection({
      chapter_id: form.chapter_id || null,
      visibility: form.visibility,
      body: form.body,
    });
    form.body = '';
    saved.value = true;
    await refresh();
  } catch (err) {
    error.value = err.message || 'Unable to save reflection';
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section class="reflection-page">
    <header class="page-heading">
      <p class="section-label">Reflections</p>
      <h1>Learning journal</h1>
      <p class="lede">Keep private notes or submit reflections for teacher review when the school begins guided evaluation.</p>
    </header>

    <div class="reflection-layout">
      <form class="learning-form" @submit.prevent="submit">
        <label>
          Chapter
          <select v-model.number="form.chapter_id">
            <option :value="null">General reflection</option>
            <option v-for="chapter in chapters" :key="chapter.id" :value="chapter.id">{{ chapter.title }}</option>
          </select>
        </label>
        <label>
          Visibility
          <select v-model="form.visibility">
            <option value="private">Private</option>
            <option value="submitted">Submit for review</option>
          </select>
        </label>
        <label>
          Reflection
          <textarea v-model.trim="form.body" required placeholder="Write what you understood, questioned, or want to apply." />
        </label>
        <p v-if="error" class="form-error">{{ error }}</p>
        <p v-if="saved" class="form-success">Reflection saved.</p>
        <button class="primary-action" type="submit" :disabled="busy">{{ busy ? 'Saving...' : 'Save reflection' }}</button>
      </form>

      <aside class="reflection-list">
        <h2>Recent entries</h2>
        <p v-if="loading" class="muted">Loading reflections...</p>
        <article v-for="item in reflections" :key="item.id" class="reflection-entry">
          <div>
            <strong>{{ item.visibility }}</strong>
            <span>{{ item.review_status }}</span>
          </div>
          <SafeRichContent :html="item.body" />
        </article>
      </aside>
    </div>
  </section>
</template>
