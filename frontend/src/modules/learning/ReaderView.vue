<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import ChapterDetailModal from './ChapterDetailModal.vue';
import { fetchChapter, fetchLearningIndex, plainText } from './learningApi';

const route = useRoute();
const router = useRouter();
const loading = ref(true);
const error = ref('');
const phases = ref([]);
const chapters = ref([]);
const modalChapter = ref(null);
const modalLoading = ref(false);
const modalError = ref('');
const activePhaseId = ref('all');

const selectedChapterId = computed(() => Number(route.params.chapterId || 0));
const filteredChapters = computed(() => {
  if (activePhaseId.value === 'all') return chapters.value;
  return chapters.value.filter((chapter) => chapter.curriculum_phase_id === Number(activePhaseId.value));
});

function phaseName(chapter) {
  return phases.value.find((phase) => phase.id === chapter.curriculum_phase_id)?.name || 'Common study';
}

function summaryText(chapter) {
  return plainText(chapter.summary).slice(0, 168) || 'A guided study chapter with concepts, exhibits, discussion cues, and reflection prompts.';
}

function outcomeText(chapter) {
  return plainText(chapter.learning_outcome).slice(0, 140) || 'Understand the central idea and connect it with thoughtful everyday choices.';
}

async function loadChapter(chapterId) {
  if (!chapterId) return;
  modalLoading.value = true;
  modalError.value = '';
  modalChapter.value = null;
  try {
    modalChapter.value = await fetchChapter(chapterId);
  } catch (err) {
    modalError.value = err.message || 'Unable to load chapter';
  } finally {
    modalLoading.value = false;
  }
}

async function openChapter(chapterId) {
  await router.push(`/reader/${chapterId}`);
}

function closeChapter() {
  modalChapter.value = null;
  modalError.value = '';
  router.push('/reader');
}

function sendExhibitFeedback(exhibit) {
  router.push({ path: '/feedback', query: { scope_type: 'exhibit', scope_id: exhibit.id } });
}

onMounted(async () => {
  try {
    const data = await fetchLearningIndex();
    phases.value = data.phases;
    chapters.value = data.chapters;
    if (selectedChapterId.value) await loadChapter(selectedChapterId.value);
  } catch (err) {
    error.value = err.message || 'Unable to load reader';
  } finally {
    loading.value = false;
  }
});

watch(selectedChapterId, (next, previous) => {
  if (next && next !== previous) loadChapter(next);
  if (!next) {
    modalChapter.value = null;
    modalError.value = '';
  }
});
</script>

<template>
  <section class="learning-page reader-library-page">
    <header class="reader-library-header">
      <div>
        <p class="section-label">Reader</p>
        <h1>Chapter library</h1>
        <p class="lede">
          Browse the complete study sequence. Open a chapter for its concepts, teaching material, activities, and exhibits.
        </p>
      </div>
      <div class="reader-filter-panel">
        <label>
          Phase
          <select v-model="activePhaseId">
            <option value="all">All phases</option>
            <option v-for="phase in phases" :key="phase.id" :value="phase.id">{{ phase.name }}</option>
          </select>
        </label>
      </div>
    </header>

    <p v-if="error" class="form-error">{{ error }}</p>
    <div v-else-if="loading" class="chapter-card-grid">
      <article class="public-chapter-card">Loading chapters...</article>
    </div>
    <div v-else class="chapter-card-grid reader-card-grid">
      <article v-for="chapter in filteredChapters" :key="chapter.id" class="public-chapter-card reader-chapter-card">
        <div class="chapter-card-topline">
          <span>{{ String(chapter.sort_order).padStart(2, '0') }}</span>
          <small>{{ phaseName(chapter) }}</small>
        </div>
        <h2>{{ chapter.title }}</h2>
        <div class="card-outcome">
          <strong>Learning outcome</strong>
          <p>{{ outcomeText(chapter) }}</p>
        </div>
        <p class="chapter-card-summary">{{ summaryText(chapter) }}</p>
        <button class="read-card-button" type="button" @click="openChapter(chapter.id)">Read chapter</button>
      </article>
    </div>

    <ChapterDetailModal
      v-if="modalChapter || modalLoading || modalError"
      :chapter="modalChapter"
      :loading="modalLoading"
      :error="modalError"
      @close="closeChapter"
      @feedback="sendExhibitFeedback"
    />
  </section>
</template>
