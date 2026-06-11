<script setup>
import { computed, onMounted, ref } from 'vue';
import { RouterLink } from 'vue-router';
import { chaptersForPhase, fetchLearningIndex } from './learningApi';

const loading = ref(true);
const error = ref('');
const phases = ref([]);
const chapters = ref([]);

const currentPhaseId = computed(() => chapters.value[0]?.curriculum_phase_id || phases.value[0]?.id);

onMounted(async () => {
  try {
    const data = await fetchLearningIndex();
    phases.value = data.phases;
    chapters.value = data.chapters;
  } catch (err) {
    error.value = err.message || 'Unable to load learning path';
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <section class="learning-page">
    <header class="page-heading">
      <p class="section-label">Four year journey</p>
      <h1>Learning path</h1>
      <p class="lede">The common curriculum is arranged as four phases, allowing schools to pace chapters across grades 9 to 12.</p>
    </header>

    <p v-if="error" class="form-error">{{ error }}</p>
    <div v-else-if="loading" class="learning-card">Loading journey...</div>
    <div v-else class="journey-path">
      <article
        v-for="(phase, index) in phases"
        :key="phase.id"
        class="phase-card"
        :class="{ active: phase.id === currentPhaseId }"
      >
        <div class="phase-marker">{{ index + 1 }}</div>
        <p class="section-label">{{ phase.slug }}</p>
        <h2>{{ phase.name }}</h2>
        <p class="muted">{{ phase.description || 'Shared Gita learning sequence.' }}</p>
        <strong>{{ chaptersForPhase(chapters, phase.id).length }} chapters</strong>
        <div class="phase-chapters">
          <RouterLink
            v-for="chapter in chaptersForPhase(chapters, phase.id).slice(0, 5)"
            :key="chapter.id"
            :to="`/reader/${chapter.id}`"
          >
            {{ chapter.title }}
          </RouterLink>
        </div>
      </article>
    </div>
  </section>
</template>
