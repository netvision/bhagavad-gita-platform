<script setup>
import { computed, onMounted, ref, watch } from 'vue';
import { RouterLink, useRoute, useRouter } from 'vue-router';
import SafeRichContent from '../../components/content/SafeRichContent.vue';
import { fetchChapter, fetchLearningIndex } from './learningApi';

const route = useRoute();
const router = useRouter();
const loading = ref(true);
const error = ref('');
const chapters = ref([]);
const chapter = ref(null);

const selectedChapterId = computed(() => Number(route.params.chapterId || chapters.value[0]?.id || 0));
const chapterNav = computed(() => chapters.value);

function exhibitClass(exhibit) {
  return ['exhibit-block', `type-${exhibit.field_type}`, exhibit.field_format ? `format-${exhibit.field_format}` : ''];
}

function isUrl(value) {
  return /^https?:\/\//i.test(value || '');
}

async function loadChapter(chapterId) {
  if (!chapterId) return;
  loading.value = true;
  error.value = '';
  try {
    chapter.value = await fetchChapter(chapterId);
  } catch (err) {
    error.value = err.message || 'Unable to load chapter';
  } finally {
    loading.value = false;
  }
}

onMounted(async () => {
  try {
    const data = await fetchLearningIndex();
    chapters.value = data.chapters;
    if (!route.params.chapterId && chapters.value[0]) {
      await router.replace(`/reader/${chapters.value[0].id}`);
      return;
    }
    await loadChapter(selectedChapterId.value);
  } catch (err) {
    error.value = err.message || 'Unable to load reader';
    loading.value = false;
  }
});

watch(selectedChapterId, (next, previous) => {
  if (next && next !== previous) loadChapter(next);
});
</script>

<template>
  <section class="reader-shell">
    <aside class="reader-nav">
      <p class="section-label">Chapters</p>
      <RouterLink
        v-for="item in chapterNav"
        :key="item.id"
        :to="`/reader/${item.id}`"
        class="reader-nav-item"
        :class="{ active: item.id === selectedChapterId }"
      >
        <span>{{ String(item.sort_order).padStart(2, '0') }}</span>
        {{ item.title }}
      </RouterLink>
    </aside>

    <main class="reader-main">
      <select
        class="mobile-chapter-select"
        :value="selectedChapterId"
        @change="router.push(`/reader/${$event.target.value}`)"
      >
        <option v-for="item in chapterNav" :key="item.id" :value="item.id">{{ item.title }}</option>
      </select>

      <p v-if="error" class="form-error">{{ error }}</p>
      <article v-else-if="loading" class="learning-card">Loading chapter...</article>
      <article v-else-if="chapter" class="reader-article">
        <header class="chapter-header">
          <p class="section-label">Chapter {{ chapter.sort_order }}</p>
          <h1>{{ chapter.title }}</h1>
          <SafeRichContent v-if="chapter.summary" :html="chapter.summary" />
        </header>

        <SafeRichContent v-if="chapter.body" :html="chapter.body" />

        <section v-for="concept in chapter.concepts" :key="concept.id" class="concept-section">
          <div class="concept-heading">
            <span>{{ String(concept.sort_order + 1).padStart(2, '0') }}</span>
            <h2>{{ concept.title }}</h2>
          </div>

          <SafeRichContent v-if="concept.description" :html="concept.description" />

          <div class="concept-notes">
            <article v-if="concept.learning_outcome">
              <h3>Learning outcome</h3>
              <SafeRichContent :html="concept.learning_outcome" />
            </article>
            <article v-if="concept.teaching_material">
              <h3>Teaching material</h3>
              <SafeRichContent :html="concept.teaching_material" />
            </article>
            <article v-if="concept.activities">
              <h3>Activities</h3>
              <SafeRichContent :html="concept.activities" />
            </article>
          </div>

          <div v-if="concept.exhibits?.length" class="exhibit-grid">
            <article v-for="exhibit in concept.exhibits" :key="exhibit.id" :class="exhibitClass(exhibit)">
              <div class="exhibit-meta">
                <span>{{ exhibit.field_format || exhibit.field_type }}</span>
                <RouterLink :to="{ path: '/feedback', query: { scope_type: 'exhibit', scope_id: exhibit.id } }">
                  Feedback
                </RouterLink>
              </div>
              <h3>{{ exhibit.title }}</h3>
              <SafeRichContent v-if="exhibit.field_type === 'html' && exhibit.content" :html="exhibit.content" />
              <a v-else-if="isUrl(exhibit.content)" class="media-link" :href="exhibit.content" target="_blank" rel="noreferrer noopener">
                Open {{ exhibit.field_type }}
              </a>
              <p v-else-if="exhibit.content" class="muted">{{ exhibit.content }}</p>
              <p v-else class="muted">Media asset available in the library.</p>
            </article>
          </div>
        </section>
      </article>
    </main>
  </section>
</template>
