<script setup>
import { computed, onMounted, ref } from 'vue';
import { RouterLink, useRouter } from 'vue-router';
import SafeRichContent from '../../components/content/SafeRichContent.vue';
import { chaptersForPhase, fetchLearningIndex, plainText } from './learningApi';

const router = useRouter();
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
const featuredChapters = computed(() => chapters.value.slice(0, 8));
const conceptCountLabel = computed(() => `${chapters.value.length} published chapters`);

function phaseName(chapter) {
  return phases.value.find((phase) => phase.id === chapter.curriculum_phase_id)?.name || 'Common study';
}

function summaryText(chapter) {
  return plainText(chapter.summary).slice(0, 150) || 'A guided study chapter with concepts, exhibits, discussion cues, and reflection prompts.';
}

function outcomeText(chapter) {
  return plainText(chapter.learning_outcome).slice(0, 132) || 'Understand the central idea and connect it with thoughtful everyday choices.';
}

function coverClass(chapter) {
  return `chapter-cover cover-${((chapter.sort_order || chapter.id || 1) % 6) + 1}`;
}

function openChapter(chapterId) {
  router.push(`/reader/${chapterId}`);
}

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
    <div class="learning-hero public-hero">
      <div>
        <p class="section-label">Learning dashboard</p>
        <h1>गीता के गूढ़ ज्ञान को सरल भाषा में समझें</h1>
        <p class="lede">
          विद्यार्थियों के लिए श्लोक, कहानियां और जीवनोपयोगी चिंतन।
        </p>
        <div class="hero-actions">
          <button v-if="currentChapter" class="primary-link" type="button" @click="openChapter(currentChapter.id)">Resume reading</button>
          <RouterLink class="secondary-link" to="/journey">View journey</RouterLink>
        </div>
      </div>
      <aside class="progress-card public-progress-card">
        <span>Current phase</span>
        <strong>{{ currentPhase?.name || 'Not started' }}</strong>
        <p>{{ conceptCountLabel }}</p>
      </aside>
    </div>

    <p v-if="error" class="form-error">{{ error }}</p>
    <div v-else-if="loading" class="chapter-card-grid">
      <article class="public-chapter-card">Loading curriculum...</article>
    </div>
    <div v-else class="public-dashboard-stack">
      <section class="chapter-strip chapter-card-section">
        <div class="strip-header">
          <div>
            <p class="section-label">Chapter library</p>
            <h2>Choose a chapter for focused study</h2>
          </div>
          <RouterLink class="text-link" to="/reader">All chapters</RouterLink>
        </div>
        <div class="chapter-card-grid">
          <article
            v-for="chapter in featuredChapters"
            :key="chapter.id"
            class="public-chapter-card clickable-card"
            tabindex="0"
            @click="openChapter(chapter.id)"
            @keydown.enter="openChapter(chapter.id)"
          >
            <div :class="coverClass(chapter)">
              <span>अध्याय {{ String(chapter.sort_order).padStart(2, '0') }}</span>
            </div>
            <div class="chapter-card-topline">
              <span>{{ String(chapter.sort_order).padStart(2, '0') }}</span>
              <small>{{ phaseName(chapter) }}</small>
            </div>
            <h3>{{ chapter.title }}</h3>
            <div class="card-outcome">
              <strong>Learning outcome</strong>
              <p>{{ outcomeText(chapter) }}</p>
            </div>
            <p class="chapter-card-summary">{{ summaryText(chapter) }}</p>
            <button class="read-card-button" type="button" @click.stop="openChapter(chapter.id)">Read chapter</button>
          </article>
        </div>
      </section>

      <div class="dashboard-grid public-dashboard-grid">
        <article class="focus-panel public-focus-panel">
          <p class="section-label">Continue learning</p>
          <h2>{{ currentChapter?.title || 'No published chapters yet' }}</h2>
          <SafeRichContent v-if="currentChapter?.summary" :html="currentChapter.summary" />
          <p v-else class="muted">Published chapter summaries will appear here as content admins release them.</p>
          <button v-if="currentChapter" class="text-link inline-button" type="button" @click="openChapter(currentChapter.id)">Open chapter</button>
        </article>

        <article class="learning-card public-small-card">
          <p class="section-label">Phase progress</p>
          <h2>{{ currentPhase?.name || 'Phase sequence' }}</h2>
          <p class="muted">{{ phaseChapters.length }} chapters in this phase are available for study.</p>
          <div class="mini-progress"><span :style="{ width: phaseChapters.length ? '28%' : '0%' }" /></div>
        </article>

        <article class="learning-card public-small-card">
          <p class="section-label">Reflection prompt</p>
          <h2>Pause and connect</h2>
          <p class="muted">What is one idea from today's study that can guide a real choice this week?</p>
          <RouterLink class="text-link" to="/reflections">Write reflection</RouterLink>
        </article>

        <article class="learning-card shortcut-card public-small-card">
          <p class="section-label">Feedback</p>
          <h2>Help improve the learning material</h2>
          <p class="muted">Report unclear explanations, broken media, or a classroom suggestion.</p>
          <RouterLink class="text-link" to="/feedback">Send feedback</RouterLink>
        </article>
      </div>
    </div>
  </section>
</template>
