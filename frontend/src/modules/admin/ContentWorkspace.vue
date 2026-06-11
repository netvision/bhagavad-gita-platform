<script setup>
import { computed, onMounted, reactive, ref } from 'vue';
import RichTextEditor from '../content-editor/RichTextEditor.vue';
import ExhibitEditor from '../content-editor/ExhibitEditor.vue';
import PublishPanel from '../content-editor/PublishPanel.vue';
import {
  createChapter,
  createConcept,
  createDraft,
  createExhibit,
  createPhase,
  deleteConcept,
  deleteExhibit,
  deletePhase,
  getChapterVersion,
  listAdminChapters,
  listAdminPhases,
  listConcepts,
  publishChapterVersion,
  updateChapter,
  updateChapterVersion,
  updateConcept,
  updateExhibit,
  updatePhase,
} from './adminApi';

const chapters = ref([]);
const phases = ref([]);
const selectedChapter = ref(null);
const selectedPhase = ref(null);
const version = ref(null);
const concepts = ref([]);
const selectedConcept = ref(null);
const selectedExhibit = ref(null);
const busy = ref(false);
const error = ref('');
const notice = ref('');

const chapterForm = reactive({
  title: '',
  slug: '',
  sort_order: 0,
  curriculum_phase_id: '',
  summary: '',
  body: '',
});

const phaseForm = reactive({
  name: '',
  slug: '',
  description: '',
  sort_order: 0,
});

const conceptForm = reactive({
  title: '',
  slug: '',
  description: '',
  learning_outcome: '',
  teaching_material: '',
  activities: '',
  sort_order: 0,
});

const canEditDraft = computed(() => version.value?.status === 'draft');

function slugify(value) {
  return value.toLowerCase().trim().replace(/[^a-z0-9]+/g, '-').replace(/(^-|-$)/g, '') || 'chapter';
}

function versionPayload() {
  return {
    title: chapterForm.title,
    summary: chapterForm.summary || null,
    body: chapterForm.body || null,
  };
}

function conceptPayload() {
  return {
    title: conceptForm.title,
    slug: conceptForm.slug || null,
    description: conceptForm.description || null,
    learning_outcome: conceptForm.learning_outcome || null,
    teaching_material: conceptForm.teaching_material || null,
    activities: conceptForm.activities || null,
    sort_order: Number(conceptForm.sort_order || 0),
  };
}

function resetMessages() {
  error.value = '';
  notice.value = '';
}

function fillVersionForm(value) {
  chapterForm.title = value?.title || selectedChapter.value?.title || '';
  chapterForm.slug = selectedChapter.value?.slug || slugify(chapterForm.title);
  chapterForm.sort_order = selectedChapter.value?.sort_order ?? 0;
  chapterForm.curriculum_phase_id = selectedChapter.value?.curriculum_phase_id || '';
  chapterForm.summary = value?.summary || '';
  chapterForm.body = value?.body || '';
}

function fillPhaseForm(value = null) {
  selectedPhase.value = value;
  phaseForm.name = value?.name || '';
  phaseForm.slug = value?.slug || slugify(phaseForm.name || 'phase');
  phaseForm.description = value?.description || '';
  phaseForm.sort_order = value?.sort_order ?? phases.value.length + 1;
}

function fillConceptForm(value) {
  conceptForm.title = value?.title || '';
  conceptForm.slug = value?.slug || '';
  conceptForm.description = value?.description || '';
  conceptForm.learning_outcome = value?.learning_outcome || '';
  conceptForm.teaching_material = value?.teaching_material || '';
  conceptForm.activities = value?.activities || '';
  conceptForm.sort_order = value?.sort_order ?? concepts.value.length;
}

async function refreshChapters() {
  chapters.value = await listAdminChapters();
}

async function refreshPhases() {
  phases.value = await listAdminPhases();
}

async function selectChapter(chapter) {
  resetMessages();
  selectedChapter.value = chapter;
  selectedConcept.value = null;
  selectedExhibit.value = null;
  concepts.value = [];
  if (!chapter.current_version_id) {
    version.value = null;
    fillVersionForm(null);
    return;
  }
  version.value = await getChapterVersion(chapter.current_version_id);
  fillVersionForm(version.value);
  concepts.value = await listConcepts(version.value.id);
}

async function withBusy(action) {
  busy.value = true;
  resetMessages();
  try {
    await action();
  } catch (err) {
    error.value = err.message || 'Action failed';
  } finally {
    busy.value = false;
  }
}

async function createNewChapter() {
  await withBusy(async () => {
    const created = await createChapter({
      curriculum_phase_id: chapterForm.curriculum_phase_id ? Number(chapterForm.curriculum_phase_id) : null,
      title: chapterForm.title,
      slug: chapterForm.slug || slugify(chapterForm.title),
      sort_order: Number(chapterForm.sort_order || 0),
      summary: chapterForm.summary || null,
      body: chapterForm.body || null,
    });
    await refreshChapters();
    const chapter = chapters.value.find((item) => item.id === created.chapter_id);
    if (chapter) await selectChapter(chapter);
    notice.value = 'Chapter draft created.';
  });
}

async function saveChapterMetadata() {
  if (!selectedChapter.value) return;
  await withBusy(async () => {
    const updated = await updateChapter(selectedChapter.value.id, {
      curriculum_phase_id: chapterForm.curriculum_phase_id ? Number(chapterForm.curriculum_phase_id) : null,
      title: selectedChapter.value.title,
      slug: chapterForm.slug || slugify(selectedChapter.value.title),
      sort_order: Number(chapterForm.sort_order || 0),
    });
    await refreshChapters();
    const refreshed = chapters.value.find((item) => item.id === updated.id);
    if (refreshed) selectedChapter.value = refreshed;
    notice.value = 'Chapter phase, slug, and order saved.';
  });
}

async function saveVersion() {
  if (!version.value) return createNewChapter();
  await withBusy(async () => {
    version.value = await updateChapterVersion(version.value.id, versionPayload());
    await refreshChapters();
    notice.value = 'Draft saved.';
  });
}

async function savePhase() {
  await withBusy(async () => {
    const payload = {
      name: phaseForm.name,
      slug: phaseForm.slug || slugify(phaseForm.name),
      description: phaseForm.description || null,
      sort_order: Number(phaseForm.sort_order || 0),
    };
    if (selectedPhase.value?.id) {
      await updatePhase(selectedPhase.value.id, payload);
      notice.value = 'Phase updated.';
    } else {
      await createPhase(payload);
      notice.value = 'Phase created.';
    }
    await refreshPhases();
    fillPhaseForm(null);
  });
}

async function removePhase() {
  if (!selectedPhase.value?.id) return;
  await withBusy(async () => {
    await deletePhase(selectedPhase.value.id);
    await refreshPhases();
    fillPhaseForm(null);
    notice.value = 'Phase deleted.';
  });
}

async function makeDraft() {
  if (!selectedChapter.value) return;
  await withBusy(async () => {
    version.value = await createDraft(selectedChapter.value.id);
    await refreshChapters();
    fillVersionForm(version.value);
    concepts.value = await listConcepts(version.value.id);
    notice.value = 'Draft created from current content.';
  });
}

async function publishDraft() {
  if (!version.value) return;
  await withBusy(async () => {
    version.value = await publishChapterVersion(version.value.id);
    await refreshChapters();
    notice.value = 'Draft published. Learners now see this version.';
  });
}

function newConcept() {
  selectedConcept.value = null;
  selectedExhibit.value = null;
  fillConceptForm(null);
}

function selectConcept(concept) {
  selectedConcept.value = concept;
  selectedExhibit.value = concept.exhibits?.[0] || null;
  fillConceptForm(concept);
}

async function saveConcept() {
  if (!version.value) return;
  await withBusy(async () => {
    if (selectedConcept.value?.id) {
      selectedConcept.value = await updateConcept(selectedConcept.value.id, conceptPayload());
      notice.value = 'Concept saved.';
    } else {
      selectedConcept.value = await createConcept(version.value.id, conceptPayload());
      notice.value = 'Concept created.';
    }
    concepts.value = await listConcepts(version.value.id);
    const refreshed = concepts.value.find((item) => item.id === selectedConcept.value.id);
    if (refreshed) selectConcept(refreshed);
  });
}

async function removeConcept() {
  if (!selectedConcept.value?.id) return;
  await withBusy(async () => {
    await deleteConcept(selectedConcept.value.id);
    concepts.value = await listConcepts(version.value.id);
    newConcept();
    notice.value = 'Concept deleted.';
  });
}

async function saveExhibit(payload) {
  if (!selectedConcept.value?.id) return;
  await withBusy(async () => {
    if (selectedExhibit.value?.id) {
      await updateExhibit(selectedExhibit.value.id, payload);
      notice.value = 'Exhibit saved.';
    } else {
      await createExhibit(selectedConcept.value.id, payload);
      notice.value = 'Exhibit created.';
    }
    concepts.value = await listConcepts(version.value.id);
    const refreshed = concepts.value.find((item) => item.id === selectedConcept.value.id);
    if (refreshed) selectConcept(refreshed);
  });
}

async function removeExhibit(exhibit) {
  await withBusy(async () => {
    await deleteExhibit(exhibit.id);
    concepts.value = await listConcepts(version.value.id);
    const refreshed = concepts.value.find((item) => item.id === selectedConcept.value.id);
    if (refreshed) selectConcept(refreshed);
    notice.value = 'Exhibit deleted.';
  });
}

onMounted(async () => {
  await withBusy(async () => {
    await refreshPhases();
    await refreshChapters();
    if (chapters.value[0]) await selectChapter(chapters.value[0]);
    fillPhaseForm(phases.value[0] || null);
  });
});
</script>

<template>
  <section class="content-workspace">
    <header class="page-heading">
      <p class="section-label">Content workspace</p>
      <h1>Chapter, concept, and exhibit editor</h1>
      <p class="lede">Draft safely, keep published learner content stable, then publish when review is complete.</p>
    </header>

    <p v-if="error" class="form-error">{{ error }}</p>
    <p v-if="notice" class="form-success">{{ notice }}</p>

    <div class="admin-editor-grid">
      <aside class="chapter-tree">
        <div class="panel-heading">
          <div>
            <p class="section-label">Chapters</p>
            <h2>{{ chapters.length }}</h2>
          </div>
          <button type="button" @click="selectedChapter = null; version = null; concepts = []; fillVersionForm(null)">New</button>
        </div>
        <button
          v-for="chapter in chapters"
          :key="chapter.id"
          type="button"
          class="chapter-tree-item"
          :class="{ active: selectedChapter?.id === chapter.id }"
          @click="selectChapter(chapter)"
        >
          <span>{{ chapter.sort_order }}</span>
          <strong>{{ chapter.title }}</strong>
          <small>{{ chapter.current_status || 'no version' }}</small>
        </button>

        <section class="phase-manager">
          <div class="panel-heading">
            <div>
              <p class="section-label">Phases</p>
              <h2>{{ phases.length }}</h2>
            </div>
            <button type="button" @click="fillPhaseForm(null)">New</button>
          </div>
          <div class="phase-list">
            <button
              v-for="phase in phases"
              :key="phase.id"
              type="button"
              :class="{ active: selectedPhase?.id === phase.id }"
              @click="fillPhaseForm(phase)"
            >
              {{ phase.sort_order }}. {{ phase.name }}
            </button>
          </div>
          <label>Name<input v-model.trim="phaseForm.name" @input="!selectedPhase && (phaseForm.slug = slugify(phaseForm.name))" /></label>
          <label>Slug<input v-model.trim="phaseForm.slug" /></label>
          <label>Order<input v-model.number="phaseForm.sort_order" type="number" /></label>
          <label>Description<textarea v-model.trim="phaseForm.description" /></label>
          <div class="button-row">
            <button type="button" class="primary-action" :disabled="busy || !phaseForm.name" @click="savePhase">Save phase</button>
            <button type="button" :disabled="busy || !selectedPhase" @click="removePhase">Delete</button>
          </div>
        </section>
      </aside>

      <main class="chapter-editor">
        <section class="editor-panel">
          <div class="panel-heading">
            <div>
              <p class="section-label">Chapter version</p>
              <h2>{{ version ? `Version ${version.version_number}` : 'New chapter draft' }}</h2>
            </div>
            <strong class="status-chip">{{ version?.status || 'draft' }}</strong>
          </div>
          <label>
            Title
            <input v-model.trim="chapterForm.title" :disabled="version && !canEditDraft" />
          </label>
          <div class="form-row">
            <label>
              Slug
              <input v-model.trim="chapterForm.slug" />
            </label>
            <label>
              Phase
              <select v-model.number="chapterForm.curriculum_phase_id">
                <option value="">No phase</option>
                <option v-for="phase in phases" :key="phase.id" :value="phase.id">{{ phase.sort_order }}. {{ phase.name }}</option>
              </select>
            </label>
            <label>
              Order
              <input v-model.number="chapterForm.sort_order" type="number" />
            </label>
          </div>
          <button v-if="selectedChapter" type="button" :disabled="busy" @click="saveChapterMetadata">
            Save phase, slug, and order
          </button>
          <label>
            Summary
            <RichTextEditor v-model="chapterForm.summary" placeholder="Chapter summary" />
          </label>
          <label>
            Body
            <RichTextEditor v-model="chapterForm.body" placeholder="Chapter body" />
          </label>
        </section>

        <section class="editor-panel">
          <div class="panel-heading">
            <div>
              <p class="section-label">Concepts</p>
              <h2>{{ selectedConcept?.title || 'New concept' }}</h2>
            </div>
            <button type="button" :disabled="!canEditDraft" @click="newConcept">New concept</button>
          </div>
          <div class="concept-list">
            <button
              v-for="concept in concepts"
              :key="concept.id"
              type="button"
              :class="{ active: selectedConcept?.id === concept.id }"
              @click="selectConcept(concept)"
            >
              {{ concept.sort_order }}. {{ concept.title }}
            </button>
          </div>
          <label>
            Title
            <input v-model.trim="conceptForm.title" :disabled="!canEditDraft" />
          </label>
          <div class="form-row">
            <label>
              Slug
              <input v-model.trim="conceptForm.slug" :disabled="!canEditDraft" />
            </label>
            <label>
              Order
              <input v-model.number="conceptForm.sort_order" type="number" :disabled="!canEditDraft" />
            </label>
          </div>
          <label>Description<RichTextEditor v-model="conceptForm.description" /></label>
          <label>Learning outcome<RichTextEditor v-model="conceptForm.learning_outcome" /></label>
          <label>Teaching material<RichTextEditor v-model="conceptForm.teaching_material" /></label>
          <label>Activities<RichTextEditor v-model="conceptForm.activities" /></label>
          <div class="button-row">
            <button type="button" class="primary-action" :disabled="busy || !canEditDraft || !conceptForm.title" @click="saveConcept">Save concept</button>
            <button type="button" :disabled="busy || !canEditDraft || !selectedConcept" @click="removeConcept">Delete concept</button>
          </div>
        </section>

        <section v-if="selectedConcept" class="editor-panel">
          <div class="panel-heading">
            <div>
              <p class="section-label">Exhibits</p>
              <h2>{{ selectedConcept.exhibits?.length || 0 }} items</h2>
            </div>
            <button type="button" :disabled="!canEditDraft" @click="selectedExhibit = null">New exhibit</button>
          </div>
          <div class="concept-list">
            <button
              v-for="exhibit in selectedConcept.exhibits"
              :key="exhibit.id"
              type="button"
              :class="{ active: selectedExhibit?.id === exhibit.id }"
              @click="selectedExhibit = exhibit"
            >
              {{ exhibit.sort_order }}. {{ exhibit.title }}
            </button>
          </div>
          <ExhibitEditor :exhibit="selectedExhibit" :busy="busy || !canEditDraft" @save="saveExhibit" @delete="removeExhibit" />
        </section>
      </main>

      <PublishPanel :version="version" :busy="busy" @save="saveVersion" @draft="makeDraft" @publish="publishDraft" />
    </div>
  </section>
</template>
