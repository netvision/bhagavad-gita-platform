<script setup>
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import SafeRichContent from '../../components/content/SafeRichContent.vue';
import { chaptersForPhase, fetchLearningIndex, plainText } from './learningApi';

const loading = ref(true);
const error = ref('');
const phases = ref([]);
const chapters = ref([]);

const currentChapter = computed(() => chapters.value[0] || null);
const currentPhase = computed(() => {
  if (!currentChapter.value) return phases.value[0] || null;
  return phases.value.find((phase) => phase.id === currentChapter.value.curriculum_phase_id) || phases.value[0] || null;
});
const phaseChapters = computed(() => currentPhase.value ? chaptersForPhase(chapters.value, currentPhase.value.id) : []);
const recentChapters = computed(() => chapters.value.slice(0, 4));
const conceptCountLabel = computed(() => `${chapters.value.length} published chapters`);

onMounted(async () => {
  try {
    const data = await fetchLearningIndex();
    phases.value = data.phases;
    chapters.value = data.chapters;
  } catch (err) {
    error.value = err.message || 'Unable to load learning dashboard';
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <section class="learning-page">
    <div class="learning-hero">
      <div>
        <p class="section-label">Learning dashboard</p>
        <h1>Continue the Gita learning journey</h1>
        <p class="lede">
          Study each chapter as a guided sequence of concepts, exhibits, classroom discussion, and reflection.
        </p>
        <div class="hero-actions">
          <RouterLink v-if="currentChapter" class="primary-link" :to="`/reader/${currentChapter.id}`">Resume reading</RouterLink>
          <RouterLink class="secondary-link" to="/journey">View journey</RouterLink>
        </div>
      </div>
      <aside class="progress-card">
        <span>Current phase</span>
        <strong>{{ currentPhase?.name || 'Not started' }}</strong>
        <p>{{ conceptCountLabel }}</p>
      </aside>
    </div>

    <p v-if="error" class="form-error">{{ error }}</p>
    <div v-else-if="loading" class="learning-grid">
      <article class="learning-card">Loading curriculum...</article>
    </div>
    <div v-else class="dashboard-grid">
      <article class="focus-panel">
        <p class="section-label">Continue learning</p>
        <h2>{{ currentChapter?.title || 'No published chapters yet' }}</h2>
        <SafeRichContent v-if="currentChapter?.summary" :html="currentChapter.summary" />
        <p v-else class="muted">Published chapter summaries will appear here as content admins release them.</p>
        <RouterLink v-if="currentChapter" class="text-link" :to="`/reader/${currentChapter.id}`">Open chapter</RouterLink>
      </article>

      <article class="learning-card">
        <p class="section-label">Phase progress</p>
        <h2>{{ currentPhase?.name || 'Phase sequence' }}</h2>
        <p class="muted">{{ phaseChapters.length }} chapters in this phase are available for study.</p>
        <div class="mini-progress"><span :style="{ width: phaseChapters.length ? '28%' : '0%' }" /></div>
      </article>

      <article class="learning-card">
        <p class="section-label">Reflection prompt</p>
        <h2>Pause and connect</h2>
        <p class="muted">What is one idea from today’s study that can guide a real choice this week?</p>
        <RouterLink class="text-link" to="/reflections">Write reflection</RouterLink>
      </article>

      <article class="learning-card shortcut-card">
        <p class="section-label">Feedback</p>
        <h2>Help improve the learning material</h2>
        <p class="muted">Report unclear explanations, broken media, or a classroom suggestion.</p>
        <RouterLink class="text-link" to="/feedback">Send feedback</RouterLink>
      </article>

      <section class="chapter-strip">
        <div class="strip-header">
          <div>
            <p class="section-label">Recent chapters</p>
            <h2>Start with the next available reading</h2>
          </div>
          <RouterLink class="text-link" to="/reader">All chapters</RouterLink>
        </div>
        <RouterLink v-for="chapter in recentChapters" :key="chapter.id" class="chapter-row" :to="`/reader/${chapter.id}`">
          <span>{{ String(chapter.sort_order).padStart(2, '0') }}</span>
          <strong>{{ chapter.title }}</strong>
          <small>{{ plainText(chapter.summary).slice(0, 96) || 'Chapter reading' }}</small>
        </RouterLink>
      </section>
    </div>
  </section>
</template>
