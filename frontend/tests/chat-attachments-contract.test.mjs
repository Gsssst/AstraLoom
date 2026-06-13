import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { test } from 'node:test';

const attachmentHookSource = readFileSync(
  new URL('../src/hooks/useChatAttachments.ts', import.meta.url),
  'utf8',
);
const chatPageSource = readFileSync(
  new URL('../src/pages/ChatPage.tsx', import.meta.url),
  'utf8',
);
const paperDetailSource = readFileSync(
  new URL('../src/pages/PaperDetailPage.tsx', import.meta.url),
  'utf8',
);
const responsiveSource = readFileSync(
  new URL('../src/styles/responsive.css', import.meta.url),
  'utf8',
);

test('shared chat attachment workflow enforces a 50MB file limit', () => {
  assert.match(attachmentHookSource, /CHAT_ATTACHMENT_MAX_BYTES = 50 \* 1024 \* 1024/);
  assert.match(attachmentHookSource, /CHAT_ATTACHMENT_MAX_MB = 50/);
  assert.match(attachmentHookSource, /file\.size > CHAT_ATTACHMENT_MAX_BYTES/);
  assert.match(attachmentHookSource, /超过\$\{CHAT_ATTACHMENT_MAX_MB\}MB/);
  assert.match(attachmentHookSource, /\/chat-sessions\/extract-file/);
  assert.match(attachmentHookSource, /input\.accept = 'image\/\*,\.pdf'/);
  assert.match(attachmentHookSource, /input\.multiple = true/);
  assert.match(attachmentHookSource, /attachedTextContext/);
  assert.match(attachmentHookSource, /imageAttachmentPayloads/);
});

test('main chat uses the shared attachment workflow', () => {
  assert.match(chatPageSource, /import useChatAttachments from '\.\.\/hooks\/useChatAttachments'/);
  assert.match(chatPageSource, /useChatAttachments\(\)/);
  assert.match(chatPageSource, /attachedTextContext\(files\)/);
  assert.match(chatPageSource, /imageAttachmentPayloads\(files\)/);
  assert.match(chatPageSource, /onClick=\{openAttachmentPicker\}/);
  assert.doesNotMatch(chatPageSource, /10 \* 1024 \* 1024/);
  assert.doesNotMatch(chatPageSource, /超过10MB/);
});

test('paper detail chat supports PDF and image attachments', () => {
  assert.match(paperDetailSource, /import useChatAttachments from '\.\.\/hooks\/useChatAttachments'/);
  assert.match(paperDetailSource, /paperChatAttachments/);
  assert.match(paperDetailSource, /openPaperChatAttachmentPicker/);
  assert.match(paperDetailSource, /paperChatAttachmentTextContext\(attachedFiles\)/);
  assert.match(paperDetailSource, /paperChatImageAttachmentPayloads\(attachedFiles\)/);
  assert.match(paperDetailSource, /用户上传附件提取内容/);
  assert.match(paperDetailSource, /用户上传图片/);
  assert.match(paperDetailSource, /attachments: imageAttachments/);
  assert.match(paperDetailSource, /hasExtractingPaperChatAttachments/);
  assert.match(paperDetailSource, /paper-chat-attachments/);
  assert.match(paperDetailSource, /paper-detail-chat-upload/);
  assert.match(paperDetailSource, /attachmentNames/);
});

test('paper attachment UI has scoped compact styles', () => {
  assert.match(responsiveSource, /\.paper-detail-chat-upload/);
  assert.match(responsiveSource, /\.paper-chat-message-attachments/);
  assert.match(responsiveSource, /\.paper-chat-attachments/);
});
