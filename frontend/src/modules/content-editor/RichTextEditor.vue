<script setup>
import { watch } from 'vue';
import StarterKit from '@tiptap/starter-kit';
import Link from '@tiptap/extension-link';
import { EditorContent, useEditor } from '@tiptap/vue-3';

const props = defineProps({
  modelValue: { type: String, default: '' },
  placeholder: { type: String, default: 'Write content...' },
  disabled: { type: Boolean, default: false },
});

const emit = defineEmits(['update:modelValue']);

const editor = useEditor({
  content: props.modelValue || '',
  editable: !props.disabled,
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

watch(
  () => props.disabled,
  (value) => {
    editor.value?.setEditable(!value);
  },
);

function run(command) {
  if (props.disabled || !editor.value) return;
  command();
}

function setLink() {
  if (props.disabled || !editor.value) return;
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
  <div class="rich-editor" :class="{ disabled }">
    <div v-if="editor" class="editor-toolbar" aria-label="Editor toolbar">
      <div class="toolbar-group">
        <button type="button" title="Bold" aria-label="Bold" :disabled="disabled" :class="{ active: editor.isActive('bold') }" @click="run(() => editor.chain().focus().toggleBold().run())">
          <strong>B</strong>
        </button>
        <button type="button" title="Italic" aria-label="Italic" :disabled="disabled" :class="{ active: editor.isActive('italic') }" @click="run(() => editor.chain().focus().toggleItalic().run())">
          <em>I</em>
        </button>
      </div>
      <div class="toolbar-group">
        <button type="button" title="Heading 2" aria-label="Heading 2" :disabled="disabled" :class="{ active: editor.isActive('heading', { level: 2 }) }" @click="run(() => editor.chain().focus().toggleHeading({ level: 2 }).run())">H2</button>
        <button type="button" title="Heading 3" aria-label="Heading 3" :disabled="disabled" :class="{ active: editor.isActive('heading', { level: 3 }) }" @click="run(() => editor.chain().focus().toggleHeading({ level: 3 }).run())">H3</button>
      </div>
      <div class="toolbar-group">
        <button type="button" title="Bullet list" aria-label="Bullet list" :disabled="disabled" :class="{ active: editor.isActive('bulletList') }" @click="run(() => editor.chain().focus().toggleBulletList().run())">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M8 6h12M8 12h12M8 18h12"/><circle cx="4" cy="6" r="1.4"/><circle cx="4" cy="12" r="1.4"/><circle cx="4" cy="18" r="1.4"/></svg>
        </button>
        <button type="button" title="Numbered list" aria-label="Numbered list" :disabled="disabled" :class="{ active: editor.isActive('orderedList') }" @click="run(() => editor.chain().focus().toggleOrderedList().run())">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 6h10M10 12h10M10 18h10M4 5h1v3M3.5 11.5h2l-2 2h2M3.5 17h2v2h-2"/></svg>
        </button>
        <button type="button" title="Quote" aria-label="Quote" :disabled="disabled" :class="{ active: editor.isActive('blockquote') }" @click="run(() => editor.chain().focus().toggleBlockquote().run())">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M7 7h5v5H9c0 2-1 3.5-3 4.5M16 7h5v5h-3c0 2-1 3.5-3 4.5"/></svg>
        </button>
      </div>
      <div class="toolbar-group">
        <button type="button" title="Link" aria-label="Link" :disabled="disabled" :class="{ active: editor.isActive('link') }" @click="setLink">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.1 0l2-2a5 5 0 0 0-7.1-7.1l-1.1 1.1M14 11a5 5 0 0 0-7.1 0l-2 2a5 5 0 0 0 7.1 7.1l1.1-1.1"/></svg>
        </button>
        <button type="button" title="Undo" aria-label="Undo" :disabled="disabled" @click="run(() => editor.chain().focus().undo().run())">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="M9 7 5 11l4 4M5 11h9a5 5 0 0 1 0 10h-1"/></svg>
        </button>
        <button type="button" title="Redo" aria-label="Redo" :disabled="disabled" @click="run(() => editor.chain().focus().redo().run())">
          <svg viewBox="0 0 24 24" aria-hidden="true"><path d="m15 7 4 4-4 4M19 11h-9a5 5 0 0 0 0 10h1"/></svg>
        </button>
      </div>
    </div>
    <EditorContent :editor="editor" />
  </div>
</template>
