<template>
  <div class="safe-rich-content" v-html="html" />
</template>

<script setup>
defineProps({
  html: {
    type: String,
    default: '',
  },
})
</script>

<style scoped>
.safe-rich-content {
  color: inherit;
  line-height: 1.72;
}

.safe-rich-content :deep(p:last-child),
.safe-rich-content :deep(ul:last-child),
.safe-rich-content :deep(ol:last-child) {
  margin-bottom: 0;
}

.safe-rich-content :deep(a) {
  color: var(--color-indigo-soft);
  font-weight: 750;
  text-decoration: underline;
  text-underline-offset: 0.18em;
}

.safe-rich-content :deep(blockquote) {
  margin: 1rem 0;
  padding-left: 1rem;
  border-left: 3px solid var(--color-saffron);
  color: var(--color-indigo);
  font-weight: 650;
}

.safe-rich-content :deep(table) {
  width: 100%;
  border-collapse: collapse;
  background: #fff;
}

.safe-rich-content :deep(th),
.safe-rich-content :deep(td) {
  padding: 0.5rem;
  border: 1px solid var(--color-line);
}
</style>
