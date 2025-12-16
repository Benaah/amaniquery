<template>
  <div class="popup-content">
    <div class="popup-content-wrapper">
      <div v-if="content" class="full-content" :class="{ 'html-content': isHtml }">
        <div v-if="isHtml" v-html="processedContent"></div>
        <template v-else>{{ content }}</template>
      </div>
    </div>
    <div v-if="hasInfo" class="info-section">
      <div v-if="chunkId" class="info-field">
        <span class="field-label">{{ $t('chat.chunkIdLabel') }}</span>
        <span class="field-value"><code>{{ chunkId }}</code></span>
      </div>
      <div v-if="knowledgeId" class="info-field">
        <span class="field-label">{{ $t('chat.documentIdLabel') }}</span>
        <span class="field-value"><code>{{ knowledgeId }}</code></span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { sanitizeHTML } from '@/utils/security';

interface Props {
  content?: string;
  chunkId?: string;
  knowledgeId?: string;
  isHtml?: boolean; // 是否以 HTML 格式显示内容
}

const props = defineProps<Props>();

const hasInfo = computed(() => {
  return !!(props.chunkId || props.knowledgeId);
});

// 处理 HTML 内容
const processedContent = computed(() => {
  if (!props.content) return '';
  if (props.isHtml) {
    return sanitizeHTML(props.content);
  }
  return props.content;
});
</script>

<style lang="less" scoped>
.popup-content {
  display: flex;
  flex-direction: column;
  max-height: 400px;
  max-width: 500px;
  border: 1px solid #07C05F;
  border-radius: 4px;
  word-wrap: break-word;
  word-break: break-word;
  overflow: hidden;
  
  .popup-content-wrapper {
    flex: 1;
    overflow-y: auto;
    overflow-x: hidden;
    padding: 12px;
    min-height: 0;
  }
  
  .full-content {
    font-size: 13px;
    color: #333;
    line-height: 1.8;
    white-space: pre-wrap;
    word-break: break-word;
    
    &.html-content {
      white-space: normal;
      
      :deep(p) {
        margin: 8px 0;
        line-height: 1.8;
      }
      
      :deep(br) {
        line-height: 1.8;
      }
    }
  }
  
  .info-section {
    flex-shrink: 0;
    padding: 8px 12px;
    border-top: 1px solid #e7e7e7;
    background: #fafafa;
  }
  
  .info-field {
    display: flex;
    gap: 8px;
    margin-bottom: 4px;
    font-size: 11px;
    
    .field-label {
      color: #8b8b8b;
      min-width: 60px;
      flex-shrink: 0;
    }
    
    .field-value {
      color: #666;
      flex: 1;
      
      code {
        font-family: 'Monaco', 'Courier New', monospace;
        font-size: 10px;
        background: #f0f0f0;
        padding: 1px 4px;
        border-radius: 2px;
      }
    }
  }
}
</style>

