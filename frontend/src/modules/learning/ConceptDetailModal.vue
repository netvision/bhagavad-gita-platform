<script setup>
import SafeRichContent from '../../components/content/SafeRichContent.vue';

defineProps({
  concept: {
    type: Object,
    default: null,
  },
});

const emit = defineEmits(['close', 'feedback']);

function exhibitClass(exhibit) {
  return ['modal-exhibit', `type-${exhibit.field_type}`, exhibit.field_format ? `format-${exhibit.field_format}` : ''];
}

function isUrl(value) {
  return /^https?:\/\//i.test(value || '');
}
</script>

<template>
  <Teleport to="body">
    <div class="chapter-modal-backdrop" role="presentation" @click.self="emit('close')">
      <section class="chapter-modal concept-detail-modal" role="dialog" aria-modal="true">
        <button class="modal-close" type="button" aria-label="Close concept" @click="emit('close')">&times;</button>

        <template v-if="concept">
          <header class="modal-chapter-header">
            <span class="chapter-number">Concept {{ String(concept.sort_order + 1).padStart(2, '0') }}</span>
            <h1>{{ concept.title }}</h1>
            <SafeRichContent v-if="concept.description" :html="concept.description" />
          </header>

          <div class="modal-notes">
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

          <section v-if="concept.exhibits?.length" class="concept-modal-section">
            <div class="strip-header">
              <div>
                <p class="section-label">Exhibits</p>
                <h2>Explore supporting material</h2>
              </div>
            </div>
            <div class="modal-exhibit-grid">
              <article v-for="exhibit in concept.exhibits" :key="exhibit.id" :class="exhibitClass(exhibit)">
                <div class="exhibit-meta">
                  <span>{{ exhibit.field_format || exhibit.field_type }}</span>
                  <button type="button" @click="emit('feedback', exhibit)">Feedback</button>
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
        </template>
      </section>
    </div>
  </Teleport>
</template>
