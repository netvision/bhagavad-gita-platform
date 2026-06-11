import { api } from '../../app/apiClient';

export function listAdminChapters() {
  return api('/api/admin/content/chapters');
}

export function listAdminPhases() {
  return api('/api/admin/content/phases');
}

export function createPhase(payload) {
  return api('/api/admin/content/phases', { method: 'POST', body: payload });
}

export function updatePhase(phaseId, payload) {
  return api(`/api/admin/content/phases/${phaseId}`, { method: 'PUT', body: payload });
}

export function deletePhase(phaseId) {
  return api(`/api/admin/content/phases/${phaseId}`, { method: 'DELETE' });
}

export function createChapter(payload) {
  return api('/api/admin/content/chapters', { method: 'POST', body: payload });
}

export function updateChapter(chapterId, payload) {
  return api(`/api/admin/content/chapters/${chapterId}`, { method: 'PUT', body: payload });
}

export function createDraft(chapterId) {
  return api(`/api/admin/content/chapters/${chapterId}/draft`, { method: 'POST' });
}

export function getChapterVersion(versionId) {
  return api(`/api/admin/content/chapter-versions/${versionId}`);
}

export function updateChapterVersion(versionId, payload) {
  return api(`/api/admin/content/chapter-versions/${versionId}`, { method: 'PUT', body: payload });
}

export function publishChapterVersion(versionId) {
  return api(`/api/admin/content/chapter-versions/${versionId}/publish`, { method: 'POST' });
}

export function listConcepts(versionId) {
  return api(`/api/admin/content/chapter-versions/${versionId}/concepts`);
}

export function createConcept(versionId, payload) {
  return api(`/api/admin/content/chapter-versions/${versionId}/concepts`, { method: 'POST', body: payload });
}

export function updateConcept(conceptId, payload) {
  return api(`/api/admin/content/concepts/${conceptId}`, { method: 'PUT', body: payload });
}

export function deleteConcept(conceptId) {
  return api(`/api/admin/content/concepts/${conceptId}`, { method: 'DELETE' });
}

export function createExhibit(conceptId, payload) {
  return api(`/api/admin/content/concepts/${conceptId}/exhibits`, { method: 'POST', body: payload });
}

export function updateExhibit(exhibitId, payload) {
  return api(`/api/admin/content/exhibits/${exhibitId}`, { method: 'PUT', body: payload });
}

export function deleteExhibit(exhibitId) {
  return api(`/api/admin/content/exhibits/${exhibitId}`, { method: 'DELETE' });
}

export function listUsers() {
  return api('/api/admin/users');
}

export function createUser(payload) {
  return api('/api/admin/users', { method: 'POST', body: payload });
}

export function updateUser(userId, payload) {
  return api(`/api/admin/users/${userId}`, { method: 'PUT', body: payload });
}

export function setUserActive(userId, isActive) {
  return api(`/api/admin/users/${userId}/active`, { method: 'PUT', body: { is_active: isActive } });
}

export function resetPasswordToken(userId) {
  return api(`/api/admin/users/${userId}/reset-password-token`, { method: 'POST' });
}

export function listSubscriptions() {
  return api('/api/admin/subscriptions');
}

export function updateSubscription(subscriptionId, payload) {
  return api(`/api/admin/subscriptions/${subscriptionId}`, { method: 'PUT', body: payload });
}

export function listMedia() {
  return api('/api/admin/media');
}

export function uploadMedia(file, altText = '') {
  const body = new FormData();
  body.append('file', file);
  if (altText) body.append('alt_text', altText);
  return api('/api/admin/media', { method: 'POST', body });
}
