<script setup>
import { onMounted, reactive, ref } from 'vue';
import { useRoute } from 'vue-router';
import { fetchLearningIndex, postFeedback } from './learningApi';

const route = useRoute();
const chapters = ref([]);
const busy = ref(false);
const error = ref('');
const saved = ref(false);
const form = reactive({
  scope_type: route.query.scope_type || 'app',
  scope_id: route.query.scope_id ? Number(route.query.scope_id) : null,
  category: 'content',
  rating: '',
  comment: '',
});

onMounted(async () => {
  try {
    const data = await fetchLearningIndex();
    chapters.value = data.chapters;
  } catch {
    chapters.value = [];
  }
});

async function submit() {
  busy.value = true;
  error.value = '';
  saved.value = false;
  try {
    await postFeedback({
      scope_type: form.scope_type,
      scope_id: form.scope_type === 'app' ? null : Number(form.scope_id),
      category: form.category,
      rating: form.rating ? Number(form.rating) : null,
      comment: form.comment,
    });
    form.comment = '';
    saved.value = true;
  } catch (err) {
    error.value = err.message || 'Unable to send feedback';
  } finally {
    busy.value = false;
  }
}
</script>

<template>
  <section class="form-page">
    <header class="page-heading">
      <p class="section-label">Feedback</p>
      <h1>Improve the learning experience</h1>
      <p class="lede">Share content corrections, classroom suggestions, media issues, or general platform feedback.</p>
    </header>

    <form class="learning-form" @submit.prevent="submit">
      <label>
        Feedback area
        <select v-model="form.scope_type">
          <option value="app">Whole application</option>
          <option value="chapter">Specific chapter</option>
          <option value="concept">Concept</option>
          <option value="exhibit">Exhibit</option>
        </select>
      </label>

      <label v-if="form.scope_type === 'chapter'">
        Chapter
        <select v-model.number="form.scope_id" required>
          <option :value="null" disabled>Select chapter</option>
          <option v-for="chapter in chapters" :key="chapter.id" :value="chapter.id">{{ chapter.title }}</option>
        </select>
      </label>

      <label v-else-if="form.scope_type !== 'app'">
        {{ form.scope_type }} ID
        <input v-model.number="form.scope_id" type="number" min="1" required />
      </label>

      <label>
        Category
        <select v-model="form.category">
          <option value="content">Content correction</option>
          <option value="media">Media issue</option>
          <option value="classroom">Classroom use</option>
          <option value="platform">Platform experience</option>
        </select>
      </label>

      <label>
        Rating
        <select v-model="form.rating">
          <option value="">No rating</option>
          <option v-for="rating in [5, 4, 3, 2, 1]" :key="rating" :value="rating">{{ rating }}</option>
        </select>
      </label>

      <label>
        Comment
        <textarea v-model.trim="form.comment" required placeholder="Write specific, actionable feedback." />
      </label>

      <p v-if="error" class="form-error">{{ error }}</p>
      <p v-if="saved" class="form-success">Feedback submitted.</p>
      <button class="primary-action" type="submit" :disabled="busy">{{ busy ? 'Sending...' : 'Send feedback' }}</button>
    </form>
  </section>
</template>
