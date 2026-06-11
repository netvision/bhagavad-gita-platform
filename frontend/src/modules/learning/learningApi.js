import { api } from '../../app/apiClient';

export async function fetchLearningIndex() {
  const [phases, chapters] = await Promise.all([
    api('/api/learning/phases'),
    api('/api/learning/chapters'),
  ]);

  return {
    phases: [...phases].sort(bySortOrder),
    chapters: [...chapters].sort(bySortOrder),
  };
}

export function fetchChapter(chapterId) {
  return api(`/api/learning/chapters/${chapterId}`);
}

export function postFeedback(payload) {
  return api('/api/feedback', {
    method: 'POST',
    body: payload,
  });
}

export function fetchReflections() {
  return api('/api/reflections');
}

export function postReflection(payload) {
  return api('/api/reflections', {
    method: 'POST',
    body: payload,
  });
}

export function chaptersForPhase(chapters, phaseId) {
  return chapters.filter((chapter) => chapter.curriculum_phase_id === phaseId);
}

export function bySortOrder(left, right) {
  return (left.sort_order ?? 0) - (right.sort_order ?? 0) || left.id - right.id;
}

export function plainText(html = '') {
  return String(html).replace(/<[^>]+>/g, ' ').replace(/\s+/g, ' ').trim();
}
