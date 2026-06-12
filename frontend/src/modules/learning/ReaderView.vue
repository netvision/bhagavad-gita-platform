<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import SafeRichContent from '../../components/content/SafeRichContent.vue';
import ConceptDetailModal from './ConceptDetailModal.vue';
import { fetchChapter, fetchLearningIndex, plainText } from './learningApi';

const route = useRoute();
const router = useRouter();
const loading = ref(true);
const chapterLoading = ref(false);
const error = ref('');
const phases = ref([]);
const chapters = ref([]);
const chapter = ref(null);
const selectedConcept = ref(null);
const activePhaseId = ref('all');

const selectedChapterId = computed(() => Number(route.params.chapterId || 0));
const filteredChapters = computed(() => {
  if (activePhaseId.value === 'all') return chapters.value;
  return chapters.value.filter((item) => item.curriculum_phase_id === Number(activePhaseId.value));
});
const chapterPhase = computed(() => {
  if (!chapter.value) return null;
  return phases.value.find((phase) => phase.id === chapter.value.curriculum_phase_id) || null;
});
const chapterConcepts = computed(() => [...(chapter.value?.concepts || [])].sort((left, right) => {
  return (left.sort_order ?? 0) - (right.sort_order ?? 0) || left.id - right.id;
}));
const exhibitCount = computed(() => {
  return chapterConcepts.value.reduce((total, concept) => total + (concept.exhibits?.length || 0), 0);
});

function phaseName(item) {
  return phases.value.find((phase) => phase.id === item.curriculum_phase_id)?.name || 'Common study';
}

function summaryText(item) {
  return plainText(item.summary).slice(0, 168) || 'A guided study chapter with concepts, exhibits, discussion cues, and reflection prompts.';
}

function outcomeText(item) {
  return plainText(item.learning_outcome).slice(0, 140) || 'Understand the central idea and connect it with thoughtful everyday choices.';
}

function conceptSummary(concept) {
  return plainText(concept.description || concept.learning_outcome || concept.teaching_material).slice(0, 150)
    || 'Open this concept to study the explanation, activities, and supporting exhibits.';
}

function conceptOutcome(concept) {
  return plainText(concept.learning_outcome).slice(0, 120) || 'Study the core idea, examples, and classroom activity.';
}

function coverClass(item) {
  return `chapter-cover cover-${((item.sort_order || item.id || 1) % 6) + 1}`;
}

async function loadChapter(chapterId) {
  if (!chapterId) {
    chapter.value = null;
    selectedConcept.value = null;
    return;
  }
  chapterLoading.value = true;
  error.value = '';
  selectedConcept.value = null;
  try {
    chapter.value = await fetchChapter(chapterId);
  } catch (err) {
    chapter.value = null;
    error.value = err.message || 'Unable to load chapter';
  } finally {
    chapterLoading.value = false;
  }
}

function openChapter(chapterId) {
  router.push(`/reader/${chapterId}`);
}

function sendExhibitFeedback(exhibit) {
  router.push({ path: '/feedback', query: { scope_type: 'exhibit', scope_id: exhibit.id } });
}

onMounted(async () => {
  try {
    const data = await fetchLearningIndex();
    phases.value = data.phases;
    chapters.value = data.chapters;
    await loadChapter(selectedChapterId.value);
  } catch (err) {
    error.value = err.message || 'Unable to load reader';
  } finally {
    loading.value = false;
  }
});

watch(selectedChapterId, (next, previous) => {
  if (next !== previous) loadChapter(next);
});
</script>

<template>
  <section class="learning-page reader-library-page">
    <template v-if="!selectedChapterId">
      <header class="reader-library-header">
        <div>
          <p class="section-label">Reader</p>
          <h1>Chapter library</h1>
          <p class="lede">
            Study each chapter through its concepts, life connections, activities, and exhibits.
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
        <article
          v-for="item in filteredChapters"
          :key="item.id"
          class="public-chapter-card reader-chapter-card clickable-card"
          tabindex="0"
          @click="openChapter(item.id)"
          @keydown.enter="openChapter(item.id)"
        >
          <div :class="coverClass(item)">
            <span>Chapter {{ String(item.sort_order).padStart(2, '0') }}</span>
          </div>
          <div class="chapter-card-topline">
            <span>{{ String(item.sort_order).padStart(2, '0') }}</span>
            <small>{{ phaseName(item) }}</small>
          </div>
          <h2>{{ item.title }}</h2>
          <div class="card-outcome">
            <strong>Learning outcome</strong>
            <p>{{ outcomeText(item) }}</p>
          </div>
          <p class="chapter-card-summary">{{ summaryText(item) }}</p>
          <button class="read-card-button" type="button" @click.stop="openChapter(item.id)">Read chapter</button>
        </article>
      </div>
    </template>

    <template v-else>
      <p v-if="error" class="form-error">{{ error }}</p>
      <article v-if="chapterLoading" class="learning-card">Loading chapter...</article>
      <template v-else-if="chapter">
        <header class="chapter-page-hero">
          <div>
            <RouterLink class="text-link chapter-back-link" to="/reader">Back to chapters</RouterLink>
            <p class="section-label">{{ chapterPhase?.name || 'Chapter' }}</p>
            <h1>{{ chapter.title }}</h1>
            <p v-if="chapter.summary" class="chapter-page-summary">{{ plainText(chapter.summary) }}</p>
          </div>
          <div :class="coverClass(chapter)">
            <span>Chapter {{ String(chapter.sort_order).padStart(2, '0') }}</span>
          </div>
        </header>

        <section class="chapter-study-brief" aria-label="Chapter study brief">
          <article>
            <span>Learning outcome</span>
            <p>{{ outcomeText(chapter) }}</p>
          </article>
          <article>
            <span>Concepts</span>
            <strong>{{ chapterConcepts.length }}</strong>
          </article>
          <article>
            <span>Exhibits</span>
            <strong>{{ exhibitCount }}</strong>
          </article>
        </section>

        <section v-if="chapter.body" class="chapter-body-panel">
          <SafeRichContent :html="chapter.body" />
        </section>

        <section class="concept-card-section">
          <div class="strip-header">
            <div>
              <p class="section-label">Concepts</p>
              <h2>Study this chapter concept by concept</h2>
            </div>
          </div>
          <div class="concept-card-grid">
            <article
              v-for="concept in chapterConcepts"
              :key="concept.id"
              class="concept-card clickable-card"
              tabindex="0"
              @click="selectedConcept = concept"
              @keydown.enter="selectedConcept = concept"
            >
              <div class="concept-card-top">
                <div class="concept-card-number">{{ String(concept.sort_order + 1).padStart(2, '0') }}</div>
                <span>{{ concept.exhibits?.length || 0 }} exhibits</span>
              </div>
              <h3>{{ concept.title }}</h3>
              <div class="concept-card-outcome">
                <strong>Outcome</strong>
                <p>{{ conceptOutcome(concept) }}</p>
              </div>
              <p>{{ conceptSummary(concept) }}</p>
              <div class="concept-card-footer">
                <span>Concept detail</span>
                <button type="button" @click.stop="selectedConcept = concept">Open concept</button>
              </div>
            </article>
          </div>
        </section>
      </template>
    </template>

    <ConceptDetailModal
      v-if="selectedConcept"
      :concept="selectedConcept"
      @close="selectedConcept = null"
      @feedback="sendExhibitFeedback"
    />
  </section>
</template>
