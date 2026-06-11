<script setup>
import { watch } from 'vue';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import { EditorContent, useEditor } from '@tiptap/vue-3';

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Write content...' },
});

const emit = defineEmits(['update:modelValue']);

const editor = useEditor({
  content: props.modelValue || '',
  extensions: [
    StarterKit,
    Link.configure({
      openOnClick: false,
      autolink: true,
      defaultProtocol: 'https',
      HTMLAttributes: { rel: 'noreferrer noopener', target: '_blank' },
    }),
  ],
  editorProps: {
    attributes: {
      class: 'rich-editor-body',
      'aria-label': props.placeholder,
    },
  },
  onUpdate: ({ editor: instance }) => emit('update:modelValue', instance.getHTML()),
});

watch(
  () => props.modelValue,
  (value) => {
    if (!editor.value) return;
    if (editor.value.getHTML() !== (value || '')) {
      editor.value.commands.setContent(value || '', false);
    }
  },
);

function setLink() {
  if (!editor.value) return;
  const previous = editor.value.getAttributes('link').href || '';
  const href = window.prompt('Link URL', previous);
  if (href === null) return;
  if (!href.trim()) {
    editor.value.chain().focus().unsetLink().run();
    return;
  }
  editor.value.chain().focus().extendMarkRange('link').setLink({ href }).run();
}
</script>

<template>
  <div class="rich-editor">
    <div v-if="editor" class="editor-toolbar" aria-label="Editor toolbar">
      <button type="button" :class="{ active: editor.isActive('bold') }" @click="editor.chain().focus().toggleBold().run()">B</button>
      <button type="button" :class="{ active: editor.isActive('italic') }" @click="editor.chain().focus().toggleItalic().run()">I</button>
      <button type="button" :class="{ active: editor.isActive('heading', { level: 2 }) }" @click="editor.chain().focus().toggleHeading({ level: 2 }).run()">H2</button>
      <button type="button" :class="{ active: editor.isActive('heading', { level: 3 }) }" @click="editor.chain().focus().toggleHeading({ level: 3 }).run()">H3</button>
      <button type="button" :class="{ active: editor.isActive('bulletList') }" @click="editor.chain().focus().toggleBulletList().run()">UL</button>
      <button type="button" :class="{ active: editor.isActive('orderedList') }" @click="editor.chain().focus().toggleOrderedList().run()">OL</button>
      <button type="button" :class="{ active: editor.isActive('blockquote') }" @click="editor.chain().focus().toggleBlockquote().run()">Quote</button>
      <button type="button" :class="{ active: editor.isActive('link') }" @click="setLink">Link</button>
    </div>
    <EditorContent :editor="editor" />
  </div>
</template>
