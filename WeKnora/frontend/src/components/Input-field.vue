<script setup lang="ts">
import { ref, defineEmits, onMounted, onUnmounted, defineProps, computed, watch, nextTick, h } from "vue";
import { useRoute, useRouter } from 'vue-router';
import { onBeforeRouteUpdate } from 'vue-router';
import { MessagePlugin } from "tdesign-vue-next";
import { useSettingsStore } from '@/stores/settings';
import { useUIStore } from '@/stores/ui';
import { listKnowledgeBases } from '@/api/knowledge-base';
import { stopSession } from '@/api/chat';
import KnowledgeBaseSelector from './KnowledgeBaseSelector.vue';
import { listModels, type ModelConfig } from '@/api/model';
import { getTenantWebSearchConfig } from '@/api/web-search';
import { getConversationConfig, updateConversationConfig, type ConversationConfig } from '@/api/system';
import { useI18n } from 'vue-i18n';

const route = useRoute();
const router = useRouter();
const settingsStore = useSettingsStore();
const uiStore = useUIStore();
let query = ref("");
const showKbSelector = ref(false);
const atButtonRef = ref<HTMLElement>();
const showAgentModeSelector = ref(false);
const agentModeButtonRef = ref<HTMLElement>();
const agentModeDropdownStyle = ref<Record<string, string>>({});

const props = defineProps({
  isReplying: {
    type: Boolean,
    required: false
  },
  sessionId: {
    type: String,
    required: false
  },
  assistantMessageId: {
    type: String,
    required: false
  }
});

const isAgentEnabled = computed(() => settingsStore.isAgentEnabled);
const isWebSearchEnabled = computed(() => settingsStore.isWebSearchEnabled);
const selectedKbIds = computed(() => settingsStore.settings.selectedKnowledgeBases || []);
const isWebSearchConfigured = ref(false);

// 获取已选择的知识库信息
const knowledgeBases = ref<Array<{ id: string; name: string }>>([]);
const selectedKbs = computed(() => {
  return knowledgeBases.value.filter(kb => selectedKbIds.value.includes(kb.id));
});

// 模型相关状态
const availableModels = ref<ModelConfig[]>([]);
const selectedModelId = ref<string>('');
const conversationConfig = ref<ConversationConfig | null>(null);
const modelsLoading = ref(false);
const showModelSelector = ref(false);
const modelButtonRef = ref<HTMLElement>();
const modelDropdownStyle = ref<Record<string, string>>({});

const { t } = useI18n();

// 显示的知识库标签（最多显示2个）
const displayedKbs = computed(() => selectedKbs.value.slice(0, 2));
const remainingCount = computed(() => Math.max(0, selectedKbs.value.length - 2));

// 加载知识库列表
const loadKnowledgeBases = async () => {
  try {
    const response: any = await listKnowledgeBases();
    if (response.data && Array.isArray(response.data)) {
      const validKbs = response.data.filter((kb: any) => 
        kb.embedding_model_id && kb.embedding_model_id !== '' &&
        kb.summary_model_id && kb.summary_model_id !== ''
      );
      knowledgeBases.value = validKbs;
      
      // 清理无效的知识库ID（已删除或不存在于有效知识库列表中的）
      const validKbIds = new Set(validKbs.map((kb: any) => kb.id));
      const currentSelectedIds = settingsStore.settings.selectedKnowledgeBases || [];
      const validSelectedIds = currentSelectedIds.filter((id: string) => validKbIds.has(id));
      
      // 如果有无效的ID，更新store
      if (validSelectedIds.length !== currentSelectedIds.length) {
        settingsStore.selectKnowledgeBases(validSelectedIds);
      }
    }
  } catch (error) {
    console.error('Failed to load knowledge bases:', error);
  }
};

const loadWebSearchConfig = async () => {
  try {
    const response: any = await getTenantWebSearchConfig();
    const config = response?.data;
    const configured = !!(config && config.provider);
    isWebSearchConfigured.value = configured;

    if (!configured && settingsStore.isWebSearchEnabled) {
      settingsStore.toggleWebSearch(false);
    }
  } catch (error) {
    console.error('Failed to load web search config:', error);
    isWebSearchConfigured.value = false;
    if (settingsStore.isWebSearchEnabled) {
      settingsStore.toggleWebSearch(false);
    }
  }
};

const loadConversationConfig = async () => {
  try {
    const response = await getConversationConfig();
    conversationConfig.value = response.data;
    settingsStore.updateConversationModels({
      summaryModelId: response.data?.summary_model_id || '',
      rerankModelId: response.data?.rerank_model_id || '',
    });
    if (!selectedModelId.value) {
      selectedModelId.value = response.data?.summary_model_id || '';
    }
    ensureModelSelection();
  } catch (error) {
    console.error('Failed to load conversation config:', error);
  }
};

const loadChatModels = async () => {
  if (modelsLoading.value) return;
  modelsLoading.value = true;
  try {
    const models = await listModels('KnowledgeQA');
    availableModels.value = Array.isArray(models) ? models : [];
    ensureModelSelection();
  } catch (error) {
    console.error('Failed to load chat models:', error);
    availableModels.value = [];
  } finally {
    modelsLoading.value = false;
  }
};

const ensureModelSelection = () => {
  if (selectedModelId.value) {
    return;
  }
  if (conversationConfig.value?.summary_model_id) {
    selectedModelId.value = conversationConfig.value.summary_model_id;
    return;
  }
  if (availableModels.value.length > 0) {
    selectedModelId.value = availableModels.value[0].id || '';
  }
};

const handleGoToConversationModels = () => {
  showModelSelector.value = false;
  router.push('/platform/settings');
  setTimeout(() => {
    const event = new CustomEvent('settings-nav', {
      detail: { section: 'models', subsection: 'chat' },
    });
    window.dispatchEvent(event);
  }, 100);
};

const handleModelChange = async (value: string | number | Array<string | number> | undefined) => {
  const normalized = Array.isArray(value) ? value[0] : value;
  const val = normalized !== undefined && normalized !== null ? String(normalized) : '';

  if (!val) {
    selectedModelId.value = '';
    return;
  }
  if (val === '__add_model__') {
    selectedModelId.value = conversationConfig.value?.summary_model_id || '';
    handleGoToConversationModels();
    return;
  }
  
  // 保存到后端
  try {
    if (conversationConfig.value) {
      const updatedConfig = {
        ...conversationConfig.value,
        summary_model_id: val
      };
      const response = await updateConversationConfig(updatedConfig);
      
      // 更新本地状态
      conversationConfig.value = response.data;
      selectedModelId.value = val;
      showModelSelector.value = false;
      
      // 同步到 store
      settingsStore.updateConversationModels({
        summaryModelId: val,
        rerankModelId: conversationConfig.value?.rerank_model_id || '',
      });
      
      MessagePlugin.success(t('conversationSettings.toasts.chatModelSaved'));
    }
  } catch (error) {
    console.error('保存模型配置失败:', error);
    MessagePlugin.error(t('conversationSettings.toasts.saveFailed'));
    // 恢复到之前的值
    selectedModelId.value = conversationConfig.value?.summary_model_id || '';
  }
};

const selectedModel = computed(() => {
  return availableModels.value.find(model => model.id === selectedModelId.value);
});

const updateModelDropdownPosition = () => {
  const anchor = modelButtonRef.value;
  if (!anchor) {
    modelDropdownStyle.value = {
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)',
    };
    return;
  }
  
  // 获取按钮相对于视口的位置
  const rect = anchor.getBoundingClientRect();
  console.log('[Model Dropdown] Button rect:', {
    top: rect.top,
    bottom: rect.bottom,
    left: rect.left,
    right: rect.right,
    width: rect.width,
    height: rect.height
  });
  
  const dropdownWidth = 280;
  const offsetY = 8;
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  
  // 左对齐到触发元素的左边缘
  // 使用 Math.floor 而不是 Math.round，避免像素对齐问题
  let left = Math.floor(rect.left);
  
  // 边界处理：不超出视口左右（留 16px margin）
  const minLeft = 16;
  const maxLeft = Math.max(16, vw - dropdownWidth - 16);
  left = Math.max(minLeft, Math.min(maxLeft, left));

  // 垂直定位：紧贴按钮，使用合理的高度避免空白
  const preferredDropdownHeight = 280; // 优选高度（紧凑且够用）
  const maxDropdownHeight = 360; // 最大高度
  const minDropdownHeight = 200; // 最小高度
  const topMargin = 20; // 顶部留白
  const spaceBelow = vh - rect.bottom; // 下方剩余空间
  const spaceAbove = rect.top; // 上方剩余空间
  
  console.log('[Model Dropdown] Space check:', {
    spaceBelow,
    spaceAbove,
    windowHeight: vh
  });
  
  let actualHeight: number;
  let shouldOpenBelow: boolean;
  
  // 优先考虑下方空间
  if (spaceBelow >= minDropdownHeight + offsetY) {
    // 下方有足够空间，向下弹出
    actualHeight = Math.min(preferredDropdownHeight, spaceBelow - offsetY - 16);
    shouldOpenBelow = true;
    console.log('[Model Dropdown] Position: below button', { actualHeight });
  } else {
    // 向上弹出，优先使用 preferredHeight，必要时才扩展到 maxHeight
    const availableHeight = spaceAbove - offsetY - topMargin;
    if (availableHeight >= preferredDropdownHeight) {
      // 有足够空间显示优选高度
      actualHeight = preferredDropdownHeight;
    } else {
      // 空间不够，使用可用空间（但不小于最小高度）
      actualHeight = Math.max(minDropdownHeight, availableHeight);
    }
    shouldOpenBelow = false;
    console.log('[Model Dropdown] Position: above button', { actualHeight });
  }
  
  // 根据弹出方向使用不同的定位方式
  if (shouldOpenBelow) {
    // 向下弹出：使用 top 定位，左对齐
    const top = Math.floor(rect.bottom + offsetY);
    console.log('[Model Dropdown] Opening below, top:', top);
    modelDropdownStyle.value = {
      position: 'fixed !important',
      width: `${dropdownWidth}px`,
      left: `${left}px`,
      top: `${top}px`,
      maxHeight: `${actualHeight}px`,
      transform: 'none !important',
      margin: '0 !important',
      padding: '0 !important'
    };
  } else {
    // 向上弹出：使用 bottom 定位，左对齐
    const bottom = vh - rect.top + offsetY;
    console.log('[Model Dropdown] Opening above, bottom:', bottom);
    modelDropdownStyle.value = {
      position: 'fixed !important',
      width: `${dropdownWidth}px`,
      left: `${left}px`,
      bottom: `${bottom}px`,
      maxHeight: `${actualHeight}px`,
      transform: 'none !important',
      margin: '0 !important',
      padding: '0 !important'
    };
  }
  
  console.log('[Model Dropdown] Applied style:', modelDropdownStyle.value);
};

const toggleModelSelector = () => {
  if (selectedKbIds.value.length === 0) return;
  showModelSelector.value = !showModelSelector.value;
  if (showModelSelector.value) {
    if (!availableModels.value.length) {
      loadChatModels();
    }
    // 多次更新位置确保准确
    nextTick(() => {
      updateModelDropdownPosition();
      requestAnimationFrame(() => {
        updateModelDropdownPosition();
        setTimeout(() => {
          updateModelDropdownPosition();
        }, 50);
      });
    });
  }
};

const closeModelSelector = () => {
  showModelSelector.value = false;
};

// 关闭 Agent 模式选择器（点击外部）
const closeAgentModeSelector = () => {
  showAgentModeSelector.value = false;
};

// 窗口事件处理器
let resizeHandler: (() => void) | null = null;
let scrollHandler: (() => void) | null = null;

onMounted(() => {
  loadKnowledgeBases();
  loadWebSearchConfig();
  loadConversationConfig();
  loadChatModels();
  
  // 如果从知识库内部进入，自动选中该知识库
  const kbId = (route.params as any)?.kbId as string;
  if (kbId && !selectedKbIds.value.includes(kbId)) {
    settingsStore.addKnowledgeBase(kbId);
  }

  // 监听点击外部关闭下拉菜单
  document.addEventListener('click', closeAgentModeSelector);
  document.addEventListener('click', closeModelSelector);
  
  // 监听窗口大小变化和滚动，重新计算位置
  resizeHandler = () => {
    if (showModelSelector.value) {
      updateModelDropdownPosition();
    }
    if (showAgentModeSelector.value) {
      updateAgentModeDropdownPosition();
    }
  };
  scrollHandler = () => {
    if (showModelSelector.value) {
      updateModelDropdownPosition();
    }
    if (showAgentModeSelector.value) {
      updateAgentModeDropdownPosition();
    }
  };
  
  window.addEventListener('resize', resizeHandler, { passive: true });
  window.addEventListener('scroll', scrollHandler, { passive: true, capture: true });
});

onUnmounted(() => {
  document.removeEventListener('click', closeAgentModeSelector);
  document.removeEventListener('click', closeModelSelector);
  if (resizeHandler) {
    window.removeEventListener('resize', resizeHandler);
  }
  if (scrollHandler) {
    window.removeEventListener('scroll', scrollHandler, { capture: true });
  }
});

// 监听路由变化
watch(() => route.params.kbId, (newKbId) => {
  if (newKbId && typeof newKbId === 'string' && !selectedKbIds.value.includes(newKbId)) {
    settingsStore.addKnowledgeBase(newKbId);
  }
});

watch(() => uiStore.showSettingsModal, (visible, prevVisible) => {
  if (prevVisible && !visible) {
    loadWebSearchConfig();
  }
});

watch(selectedKbIds, (ids) => {
  if (!ids.length) {
    closeModelSelector();
  }
}, { deep: true });

const emit = defineEmits(['send-msg', 'stop-generation']);

const createSession = (val: string) => {
  if (!val.trim()) {
    MessagePlugin.info(t('input.messages.enterContent'));
    return;
  }
  if (selectedKbIds.value.length === 0) {
    MessagePlugin.warning(t('input.messages.selectKnowledge'));
    return;
  }
  if (props.isReplying) {
    return MessagePlugin.error(t('input.messages.replying'));
  }
  emit('send-msg', val, selectedModelId.value);
  clearvalue();
}

const updateAgentModeDropdownPosition = () => {
  const anchor = agentModeButtonRef.value;
  
  if (!anchor) {
    agentModeDropdownStyle.value = {
      position: 'fixed',
      top: '50%',
      left: '50%',
      transform: 'translate(-50%, -50%)'
    };
    return;
  }

  const rect = anchor.getBoundingClientRect();
  const dropdownWidth = 200;
  const offsetY = 8;
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  
  // 水平位置：左对齐
  let left = Math.floor(rect.left);
  const minLeft = 16;
  const maxLeft = Math.max(16, vw - dropdownWidth - 16);
  left = Math.max(minLeft, Math.min(maxLeft, left));
  
  // 垂直位置：紧贴按钮，使用合理的高度避免空白
  const preferredDropdownHeight = 140; // Agent 模式选择器内容较少，用更小的优选高度
  const maxDropdownHeight = 150;
  const minDropdownHeight = 100;
  const topMargin = 20;
  const spaceBelow = vh - rect.bottom;
  const spaceAbove = rect.top;
  
  console.log('[Agent Dropdown] Space check:', {
    spaceBelow,
    spaceAbove,
    windowHeight: vh
  });
  
  let actualHeight: number;
  
  // 优先考虑下方空间
  if (spaceBelow >= minDropdownHeight + offsetY) {
    // 下方有足够空间，向下弹出
    actualHeight = Math.min(preferredDropdownHeight, spaceBelow - offsetY - 16);
    const top = Math.floor(rect.bottom + offsetY);
    
    agentModeDropdownStyle.value = {
      position: 'fixed !important',
      width: `${dropdownWidth}px`,
      left: `${left}px`,
      top: `${top}px`,
      maxHeight: `${actualHeight}px`,
      transform: 'none !important',
      margin: '0 !important',
      padding: '0 !important',
    };
    console.log('[Agent Dropdown] Position: below button', { actualHeight });
  } else {
    // 向上弹出，使用 bottom 定位确保紧贴按钮
    const availableHeight = spaceAbove - offsetY - topMargin;
    if (availableHeight >= preferredDropdownHeight) {
      actualHeight = preferredDropdownHeight;
    } else {
      actualHeight = Math.max(minDropdownHeight, availableHeight);
    }
    
    const bottom = vh - rect.top + offsetY;
    
    agentModeDropdownStyle.value = {
      position: 'fixed !important',
      width: `${dropdownWidth}px`,
      left: `${left}px`,
      bottom: `${bottom}px`, // 使用 bottom 定位，确保紧贴按钮
      maxHeight: `${actualHeight}px`,
      transform: 'none !important',
      margin: '0 !important',
      padding: '0 !important',
    };
    console.log('[Agent Dropdown] Position: above button', { actualHeight, bottom });
  }
};

const toggleAgentModeSelector = () => {
  // 如果 Agent 未就绪，显示提示
  if (!settingsStore.isAgentReady && !isAgentEnabled.value) {
    toggleAgentMode();
    return;
  }
  
  showAgentModeSelector.value = !showAgentModeSelector.value;
  if (showAgentModeSelector.value) {
    // 多次更新位置确保准确
    nextTick(() => {
      updateAgentModeDropdownPosition();
      requestAnimationFrame(() => {
        updateAgentModeDropdownPosition();
        setTimeout(() => {
          updateAgentModeDropdownPosition();
        }, 50);
      });
    });
  }
}

const selectAgentMode = (mode: 'normal' | 'agent') => {
  if (mode === 'agent' && !settingsStore.isAgentReady) {
    toggleAgentMode();
    showAgentModeSelector.value = false;
    return;
  }
  
  const shouldEnableAgent = mode === 'agent';
  if (shouldEnableAgent !== isAgentEnabled.value) {
    settingsStore.toggleAgent(shouldEnableAgent);
    MessagePlugin.success(shouldEnableAgent ? t('input.messages.agentSwitchedOn') : t('input.messages.agentSwitchedOff'));
  }
  showAgentModeSelector.value = false;
}

const clearvalue = () => {
  query.value = "";
}

const onKeydown = (val: string, event: { e: { preventDefault(): unknown; keyCode: number; shiftKey: any; ctrlKey: any; }; }) => {
  if ((event.e.keyCode == 13 && event.e.shiftKey) || (event.e.keyCode == 13 && event.e.ctrlKey)) {
    return;
  }
  if (event.e.keyCode == 13) {
    event.e.preventDefault();
    createSession(val)
  }
}

const handleGoToWebSearchSettings = () => {
  uiStore.openSettings('websearch');
  if (route.path !== '/platform/settings') {
    router.push('/platform/settings');
  }
};

const handleGoToAgentSettings = () => {
  // 使用 uiStore 打开设置并跳转到 agent 部分
  uiStore.openSettings('agent');
  // 如果当前不在设置页面，导航到设置页面
  if (route.path !== '/platform/settings') {
    router.push('/platform/settings');
  }
}

// 获取 Agent 不就绪的原因
const getAgentNotReadyReasons = (): string[] => {
  const reasons: string[] = []
  const config = settingsStore.agentConfig || { allowedTools: [] }
  const models = settingsStore.conversationModels || { summaryModelId: '', rerankModelId: '' }
  
  if (!config.allowedTools || config.allowedTools.length === 0) {
    reasons.push(t('input.agentMissingAllowedTools'))
  }
  if (!models.summaryModelId || models.summaryModelId.trim() === '') {
    reasons.push(t('input.agentMissingSummaryModel'))
  }
  if (!models.rerankModelId || models.rerankModelId.trim() === '') {
    reasons.push(t('input.agentMissingRerankModel'))
  }
  
  return reasons
}

const toggleAgentMode = () => {
  // 如果要启用 Agent，先检查是否就绪
  // 注意：isAgentReady 是从 store 中计算的，需要确保 store 中的配置是最新的
  if (!isAgentEnabled.value) {
    // 尝试启用 Agent，先检查是否就绪
    const agentReady = settingsStore.isAgentReady
    if (!agentReady) {
      const reasons = getAgentNotReadyReasons()
      const reasonsText = reasons.join('、')
      
      // 创建带跳转链接的自定义消息
      const messageContent = h('div', { style: 'display: flex; flex-direction: column; gap: 8px; max-width: 320px;' }, [
        h('span', { style: 'color: #333; line-height: 1.5;' }, t('input.messages.agentNotReadyDetail', { reasons: reasonsText })),
        h('a', {
          href: '#',
          onClick: (e: Event) => {
            e.preventDefault();
            handleGoToAgentSettings();
          },
          style: 'color: #07C05F; text-decoration: none; font-weight: 500; cursor: pointer; align-self: flex-start;',
          onMouseenter: (e: Event) => {
            (e.target as HTMLElement).style.textDecoration = 'underline';
          },
          onMouseleave: (e: Event) => {
            (e.target as HTMLElement).style.textDecoration = 'none';
          }
        }, t('input.goToSettings'))
      ]);
      
      MessagePlugin.warning({
        content: () => messageContent,
        duration: 5000
      });
      return
    }
  }
  
  // 正常切换 Agent 状态
  settingsStore.toggleAgent(!isAgentEnabled.value);
  const message = isAgentEnabled.value ? t('input.messages.agentEnabled') : t('input.messages.agentDisabled');
  MessagePlugin.success(message);
}

const toggleWebSearch = () => {
  if (!isWebSearchConfigured.value) {
    const messageContent = h('div', { style: 'display: flex; flex-direction: column; gap: 6px; max-width: 280px;' }, [
      h('span', { style: 'color: #333; line-height: 1.5;' }, t('input.messages.webSearchNotConfigured')),
      h('a', {
        href: '#',
        onClick: (e: Event) => {
          e.preventDefault();
          handleGoToWebSearchSettings();
        },
        style: 'color: #07C05F; text-decoration: none; font-weight: 500; cursor: pointer; align-self: flex-start;',
        onMouseenter: (e: Event) => {
          (e.target as HTMLElement).style.textDecoration = 'underline';
        },
        onMouseleave: (e: Event) => {
          (e.target as HTMLElement).style.textDecoration = 'none';
        }
      }, t('input.goToSettings'))
    ]);
    MessagePlugin.warning({
      content: () => messageContent,
      duration: 5000
    });
    return;
  }

  const currentValue = settingsStore.isWebSearchEnabled;
  const newValue = !currentValue;
  settingsStore.toggleWebSearch(newValue);
  MessagePlugin.success(newValue ? t('input.messages.webSearchEnabled') : t('input.messages.webSearchDisabled'));
};

const toggleKbSelector = () => {
  showKbSelector.value = !showKbSelector.value;
}

const removeKb = (kbId: string) => {
  settingsStore.removeKnowledgeBase(kbId);
}

const handleStop = async () => {
  if (!props.sessionId) {
    MessagePlugin.warning(t('input.messages.sessionMissing'));
    return;
  }
  
  if (!props.assistantMessageId) {
    console.error('[Stop] Assistant message ID is empty');
    MessagePlugin.warning(t('input.messages.messageMissing'));
    return;
  }
  
  console.log('[Stop] Stopping generation for message:', props.assistantMessageId);
  
  // 发送 stop 事件，通知父组件立即清除 loading 状态
  emit('stop-generation');
  
  try {
    await stopSession(props.sessionId, props.assistantMessageId);
    MessagePlugin.success(t('input.messages.stopSuccess'));
  } catch (error) {
    console.error('Failed to stop session:', error);
    MessagePlugin.error(t('input.messages.stopFailed'));
  }
}

onBeforeRouteUpdate((to, from, next) => {
  clearvalue()
  next()
})

</script>
<template>
  <div class="answers-input">
    <t-textarea v-model="query" :placeholder="$t('input.placeholder')" name="description" :autosize="true" @keydown="onKeydown" />
    
    <!-- 控制栏 -->
    <div class="control-bar">
      <!-- 左侧控制按钮 -->
      <div class="control-left">
        <!-- Agent 模式切换按钮 -->
        <div 
          ref="agentModeButtonRef"
          class="control-btn agent-mode-btn"
          :class="{ 
            'active': isAgentEnabled,
            'agent-active': isAgentEnabled
          }"
          @click.stop="toggleAgentModeSelector"
        >
          <img 
            v-if="isAgentEnabled"
            :src="getImgSrc('agent-active.svg')" 
            :alt="$t('input.agentMode')" 
            class="control-icon agent-icon"
          />
          <svg 
            v-else
            width="18" 
            height="18" 
            viewBox="0 0 24 24" 
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
            class="control-icon normal-mode-icon"
          >
            <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
          </svg>
          <span class="agent-mode-text">
            {{ isAgentEnabled ? $t('input.agentMode') : $t('input.normalMode') }}
          </span>
          <svg 
            width="12" 
            height="12" 
            viewBox="0 0 12 12" 
            fill="currentColor"
            class="dropdown-arrow"
            :class="{ 'rotate': showAgentModeSelector }"
          >
            <path d="M2.5 4.5L6 8L9.5 4.5H2.5Z"/>
          </svg>
        </div>

        <!-- Agent 模式选择下拉菜单 -->
        <Teleport to="body">
          <div v-if="showAgentModeSelector" class="agent-mode-selector-overlay" @click="closeAgentModeSelector">
            <div 
              class="agent-mode-selector-dropdown"
              :style="agentModeDropdownStyle"
              @click.stop
            >
              <div 
                class="agent-mode-option"
                :class="{ 'selected': !isAgentEnabled }"
                @click="selectAgentMode('normal')"
              >
                <div class="agent-mode-option-main">
                  <span class="agent-mode-option-name">{{ $t('input.normalMode') }}</span>
                  <span class="agent-mode-option-desc">{{ $t('input.normalModeDesc') }}</span>
                </div>
                <svg 
                  v-if="!isAgentEnabled"
                  width="16" 
                  height="16" 
                  viewBox="0 0 16 16" 
                  fill="currentColor"
                  class="check-icon"
                >
                  <path d="M13.5 4.5L6 12L2.5 8.5L3.5 7.5L6 10L12.5 3.5L13.5 4.5Z"/>
                </svg>
              </div>
              <div 
                class="agent-mode-option"
                :class="{ 
                  'selected': isAgentEnabled,
                  'disabled': !settingsStore.isAgentReady && !isAgentEnabled 
                }"
                @click="selectAgentMode('agent')"
              >
                <div class="agent-mode-option-main">
                  <span class="agent-mode-option-name">{{ $t('input.agentMode') }}</span>
                  <span class="agent-mode-option-desc">{{ $t('input.agentModeDesc') }}</span>
                </div>
                <svg 
                  v-if="isAgentEnabled"
                  width="16" 
                  height="16" 
                  viewBox="0 0 16 16" 
                  fill="currentColor"
                  class="check-icon"
                >
                  <path d="M13.5 4.5L6 12L2.5 8.5L3.5 7.5L6 10L12.5 3.5L13.5 4.5Z"/>
                </svg>
                <div v-if="!settingsStore.isAgentReady && !isAgentEnabled" class="agent-mode-warning">
                  <t-tooltip :content="$t('input.agentNotReadyTooltip')" placement="left">
                    <t-icon name="error-circle" class="warning-icon" />
                  </t-tooltip>
                </div>
              </div>
              <div v-if="!settingsStore.isAgentReady && !isAgentEnabled" class="agent-mode-footer">
                <a 
                  href="#"
                  @click.prevent="handleGoToAgentSettings"
                  class="agent-mode-link"
                >
                  {{ $t('input.goToSettings') }}
                </a>
              </div>
            </div>
          </div>
        </Teleport>

        <!-- WebSearch 开关按钮 -->
        <t-tooltip placement="top">
          <template #content>
            <span v-if="isWebSearchConfigured">{{ isWebSearchEnabled ? $t('input.webSearch.toggleOff') : $t('input.webSearch.toggleOn') }}</span>
            <div v-else class="websearch-tooltip-disabled">
              <span>{{ $t('input.webSearch.notConfigured') }}</span>
              <a href="#" @click.prevent="handleGoToWebSearchSettings">{{ $t('input.goToSettings') }}</a>
            </div>
          </template>
          <div 
            class="control-btn websearch-btn"
            :class="{ 'active': isWebSearchEnabled && isWebSearchConfigured, 'disabled': !isWebSearchConfigured }"
            @click.stop="toggleWebSearch"
          >
            <svg 
              width="18" 
              height="18" 
              viewBox="0 0 18 18" 
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
              class="control-icon websearch-icon"
              :class="{ 'active': isWebSearchEnabled && isWebSearchConfigured }"
            >
              <circle cx="9" cy="9" r="7" stroke="currentColor" stroke-width="1.2" fill="none"/>
              <path d="M 9 2 A 3.5 7 0 0 0 9 16" stroke="currentColor" stroke-width="1.2" fill="none"/>
              <path d="M 9 2 A 3.5 7 0 0 1 9 16" stroke="currentColor" stroke-width="1.2" fill="none"/>
              <line x1="2.94" y1="5.5" x2="15.06" y2="5.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
              <line x1="2.94" y1="12.5" x2="15.06" y2="12.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
            </svg>
          </div>
        </t-tooltip>

        <!-- @ 知识库选择按钮 -->
        <div 
          ref="atButtonRef"
          class="control-btn kb-btn"
          :class="{ 'active': selectedKbIds.length > 0 }"
          @click="toggleKbSelector"
        >
          <img :src="getImgSrc('at-icon.svg')" alt="@" class="control-icon" />
          <span class="kb-btn-text">
            {{ selectedKbIds.length > 0 ? $t('input.knowledgeBaseWithCount', { count: selectedKbIds.length }) : $t('input.knowledgeBase') }}
          </span>
          <svg 
            width="12" 
            height="12" 
            viewBox="0 0 12 12" 
            fill="currentColor"
            class="dropdown-arrow"
            :class="{ 'rotate': showKbSelector }"
          >
            <path d="M2.5 4.5L6 8L9.5 4.5H2.5Z"/>
          </svg>
        </div>

        <!-- 已选择的知识库标签 -->
        <div v-if="displayedKbs.length > 0" class="kb-tags">
          <div 
            v-for="kb in displayedKbs" 
            :key="kb.id" 
            class="kb-tag"
          >
            <span class="kb-tag-text">{{ kb.name }}</span>
            <span class="kb-tag-remove" @click.stop="removeKb(kb.id)">×</span>
          </div>
          <div v-if="remainingCount > 0" class="kb-tag more-tag">
            +{{ remainingCount }}
          </div>
        </div>

        <!-- 模型显示 -->
        <div class="model-display">
          <div
            ref="modelButtonRef"
            class="model-selector-trigger"
            :class="{ disabled: selectedKbIds.length === 0 }"
            @click.stop="toggleModelSelector"
          >
            <span class="model-selector-name">
              {{ selectedModel?.name || $t('input.notConfigured') }}
            </span>
            <svg 
              width="12" 
              height="12" 
              viewBox="0 0 12 12" 
              fill="currentColor"
              class="model-dropdown-arrow"
              :class="{ 'rotate': showModelSelector }"
            >
              <path d="M2.5 4.5L6 8L9.5 4.5H2.5Z"/>
            </svg>
          </div>
        </div>
      </div>

      <Teleport to="body">
        <div v-if="showModelSelector" class="model-selector-overlay" @click="closeModelSelector">
            <div class="model-selector-dropdown" :style="modelDropdownStyle" @click.stop>
            <div class="model-selector-header">
              <span>{{ $t('conversationSettings.models.chatGroupLabel') }}</span>
              <button class="model-selector-add" type="button" @click="handleModelChange('__add_model__')">
                <span class="add-icon">+</span>
                  <span class="add-text">{{ $t('input.addModel') }}</span>
              </button>
            </div>
            <div class="model-selector-content">
              <div
                v-for="model in availableModels"
                :key="model.id"
                class="model-option"
                :class="{ selected: model.id === selectedModelId }"
                @click="handleModelChange(model.id || '')"
              >
                <div class="model-option-main">
                  <span class="model-option-name">{{ model.name }}</span>
                  <span v-if="model.source === 'remote'" class="model-badge-remote">{{ $t('input.remote') }}</span>
                  <span v-else-if="model.parameters?.parameter_size" class="model-badge-local">
                    {{ model.parameters.parameter_size }}
                  </span>
                </div>
                <div v-if="model.description" class="model-option-desc">
                  {{ model.description }}
                </div>
              </div>
              <div v-if="availableModels.length === 0" class="model-option empty">
                {{ $t('input.noModel') }}
              </div>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- 右侧控制按钮组 -->
      <div class="control-right">
        <!-- 停止按钮（仅在回复中时显示） -->
        <t-tooltip 
          v-if="isReplying"
          :content="$t('input.stopGeneration')"
          placement="top"
        >
          <div 
            @click="handleStop" 
            class="control-btn stop-btn"
          >
            <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor">
              <rect x="5" y="5" width="6" height="6" rx="1" />
            </svg>
          </div>
        </t-tooltip>

        <!-- 发送按钮 -->
      <div 
          v-if="!isReplying"
        @click="createSession(query)" 
        class="control-btn send-btn"
        :class="{ 'disabled': !query.length || selectedKbIds.length === 0 }"
      >
        <img src="../assets/img/sending-aircraft.svg" :alt="$t('input.send')" />
        </div>
      </div>
    </div>

    <!-- 知识库选择下拉（使用 Teleport 传送到 body，避免父容器定位影响） -->
    <Teleport to="body">
    <KnowledgeBaseSelector
      v-model:visible="showKbSelector"
        :anchorEl="atButtonRef"
      @close="showKbSelector = false"
    />
    </Teleport>
  </div>
</template>
<script lang="ts">
const getImgSrc = (url: string) => {
  return new URL(`/src/assets/img/${url}`, import.meta.url).href;
}
</script>
<style scoped lang="less">
.answers-input {
  position: absolute;
  z-index: 99;
  bottom: 60px;
  left: 50%;
  transform: translateX(-400px);
}

:deep(.t-textarea__inner) {
  width: 100%;
  width: 800px;
  max-height: 250px !important;
  min-height: 112px !important;
  resize: none;
  color: #000000e6;
  font-size: 16px;
  font-weight: 400;
  line-height: 24px;
  font-family: "PingFang SC";
  padding: 16px 12px 72px 16px;  /* 增加底部padding为控制栏腾出更多空间（原52px -> 72px） */
  border-radius: 12px;
  border: 1px solid #E7E7E7;
  box-sizing: border-box;
  background: #FFF;
  box-shadow: 0 6px 6px 0 #0000000a, 0 12px 12px -1px #00000014;

  &:focus {
    border: 1px solid #07C05F;
  }

  &::placeholder {
    color: #00000066;
    font-family: "PingFang SC";
    font-size: 16px;
    font-weight: 400;
    line-height: 24px;
  }
}

/* 控制栏 */
.control-bar {
  position: absolute;
  bottom: 12px;
  left: 16px;
  right: 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  flex-wrap: wrap;  /* 允许换行，避免内容过多时挤压 */
  max-height: 56px;  /* 限制最大高度为两行 */
  z-index: 10;  /* 提高z-index，确保在textarea滚动内容之上 */
  background: linear-gradient(to bottom, rgba(255, 255, 255, 0.6) 0%, rgba(255, 255, 255, 0.95) 40%, rgba(255, 255, 255, 1) 60%);  /* 更强的渐变背景，从半透明逐渐变为完全不透明 */
  pointer-events: auto;  /* 确保可以点击 */
  padding-top: 8px;  /* 增加上边距，给渐变更多空间 */
}

.control-left {
  display: flex;
  align-items: center;
  gap: 8px;
  flex: 1;
  overflow: hidden;
  flex-wrap: wrap;  /* 允许内部元素换行 */
  min-width: 0;  /* 允许缩小 */
}

.control-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 4px;
  padding: 6px 10px;
  border-radius: 6px;
  background: #f5f5f5;
  cursor: pointer;
  transition: background 0.12s;
  user-select: none;
  flex-shrink: 0;

  &:hover {
    background: #e6e6e6;
  }

  &.disabled {
    opacity: 0.5;
    cursor: not-allowed;
    
    &:hover {
      background: #f5f5f5;
    }
  }
}

.agent-mode-btn {
  height: 28px;
  padding: 0 10px;
  min-width: auto;
  font-weight: 500;
  border: 1px solid transparent;
  transition: background 0.12s, border-color 0.12s;
  position: relative;
  
  &.active,
  &.agent-active {
    background: linear-gradient(135deg, rgba(16, 185, 129, 0.15) 0%, rgba(16, 185, 129, 0.1) 100%);
    border-color: rgba(16, 185, 129, 0.4);
    box-shadow: 0 2px 6px rgba(16, 185, 129, 0.12);
    
    .agent-mode-text {
      color: #07C05F;
      font-weight: 600;
    }
    
    .agent-icon {
      filter: brightness(0) saturate(100%) invert(58%) sepia(87%) saturate(1234%) hue-rotate(95deg) brightness(98%) contrast(89%);
    }
    
    .dropdown-arrow {
      color: #07C05F;
    }
    
    &:hover {
      background: linear-gradient(135deg, rgba(16, 185, 129, 0.2) 0%, rgba(16, 185, 129, 0.15) 100%);
      border-color: rgba(16, 185, 129, 0.6);
    }
  }
  
  &:not(.agent-active) {
    background: rgba(255, 255, 255, 0.8);
    border-color: #e0e0e0;
    
    .agent-mode-text {
      color: #666;
    }
    
    .normal-mode-icon {
      color: #666;
    }
    
    &:hover {
      background: rgba(255, 255, 255, 1);
      border-color: #b0b0b0;
    }
  }
}

.agent-icon {
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.agent-mode-text {
  font-size: 13px;
  color: #666;
  font-weight: 500;
  white-space: nowrap;
  margin: 0 4px;
}

.control-icon {
  width: 18px;
  height: 18px;
}

.kb-btn {
  height: 28px;
  padding: 0 10px;
  min-width: auto;
  
  &.active {
    background: rgba(16, 185, 129, 0.1);
    color: #07C05F;
    
    &:hover {
      background: rgba(16, 185, 129, 0.15);
    }
  }
}

.kb-btn-text {
  font-size: 13px;
  color: #666;
  font-weight: 500;
  white-space: nowrap;
}

.kb-btn.active .kb-btn-text {
  color: #07C05F;
}

.websearch-btn {
  width: 28px;
  height: 28px;
  padding: 0;
  min-width: auto;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &.active {
    background: rgba(16, 185, 129, 0.1);
    
    .websearch-icon {
      color: #07C05F;
    }
    
    &:hover {
      background: rgba(16, 185, 129, 0.15);
    }
  }
  
  &:not(.active) {
    .websearch-icon {
      color: #666;
    }
    
    &:hover {
      background: #f0f0f0;
      
      .websearch-icon {
        color: #333;
      }
    }
  }
}

:global(.websearch-tooltip-disabled) {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 220px;
  font-size: 12px;
  color: #666;
}

:global(.websearch-tooltip-disabled a) {
  color: #07C05F;
  font-weight: 500;
  text-decoration: none;
}

:global(.websearch-tooltip-disabled a:hover) {
  text-decoration: underline;
}

.websearch-icon {
  width: 18px;
  height: 18px;
}

.dropdown-arrow {
  width: 10px;
  height: 10px;
  margin-left: 2px;
  transition: transform 0.12s;
  
  &.rotate {
    transform: rotate(180deg);
  }
}

.kb-tags {
  display: flex;
  align-items: center;
  gap: 6px;
  flex: 1;
  overflow-x: auto;
  scrollbar-width: none;

  &::-webkit-scrollbar {
    display: none;
  }
}

.kb-tag {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: rgba(16, 185, 129, 0.1);
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 4px;
  font-size: 12px;
  color: #10b981;
  white-space: nowrap;
  transition: background 0.12s;
  
  &:hover {
    background: rgba(16, 185, 129, 0.15);
  }
}

.kb-tag-text {
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
}

.kb-tag-remove {
  cursor: pointer;
  font-weight: bold;
  font-size: 16px;
  line-height: 1;
  opacity: 0.7;
  
  &:hover {
    opacity: 1;
  }
}

.more-tag {
  background: rgba(0, 0, 0, 0.05);
  border-color: rgba(0, 0, 0, 0.1);
  color: #666;
  
  &:hover {
    background: rgba(0, 0, 0, 0.08);
  }
}

.control-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.stop-btn {
  width: 28px;
  height: 28px;
  padding: 0;
  background: rgba(16, 185, 129, 0.08);
  color: #07C05F;
  border: 1.5px solid rgba(16, 185, 129, 0.2);
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  
  &:hover {
    background: rgba(16, 185, 129, 0.12);
    border-color: #07C05F;
  }
  
  &:active {
    background: rgba(16, 185, 129, 0.15);
  }
  
  svg {
    display: none;
  }
  
  &::before {
    content: '';
    width: 12px;
    height: 12px;
    background: #07C05F;
    border-radius: 50%;
    display: block;
  }
}

.send-btn {
  width: 28px;
  height: 28px;
  padding: 0;
  background-color: #07C05F;
  
  &:hover:not(.disabled) {
    background-color: #059669;
  }
  
  &.disabled {
    background-color: #b5eccf;
  }
  
  img {
    width: 16px;
    height: 16px;
  }
}

/* 模型显示样式 */
.model-display {
  display: flex;
  align-items: center;
  margin-left: auto;  /* 推到最右边，但仍在 control-left 内 */
  flex-shrink: 0;
}

.model-selector-trigger {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 2px 8px;
  min-width: 100px;
  height: 22px;
  border-radius: 6px;
  border: 1px solid rgba(16, 185, 129, 0.3);
  background: rgba(16, 185, 129, 0.1);
  transition: background 0.12s, border-color 0.12s;
  cursor: pointer;
}

.model-selector-trigger:hover {
  background: rgba(16, 185, 129, 0.15);
  border-color: rgba(16, 185, 129, 0.45);
}

.model-selector-trigger.disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.model-selector-trigger.disabled:hover {
  background: rgba(16, 185, 129, 0.1);
  border-color: rgba(16, 185, 129, 0.3);
}

.model-selector-name {
  flex: 1;
  font-size: 12px;
  font-weight: 600;
  color: #07C05F;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.model-dropdown-arrow {
  width: 10px;
  height: 10px;
  color: #07C05F;
  flex-shrink: 0;
  transition: transform 0.12s;
  
  &.rotate {
    transform: rotate(180deg);
  }
}

.model-selector-trigger.disabled .model-dropdown-arrow {
  color: rgba(16, 185, 129, 0.4);
}

.model-selector-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
  background: transparent;
  touch-action: none;
}

.model-selector-dropdown {
  position: fixed !important;
  z-index: 9999;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 6px 28px rgba(15, 23, 42, 0.08);
  border: 1px solid #e7e9eb;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  margin: 0 !important;
  padding: 0 !important;
  transform: none !important;
}

.model-selector-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  border-bottom: 1px solid #f2f4f5;
  background: #fafcfc;
  font-size: 12px;
  font-weight: 600;
  color: #222;
}

.model-selector-content {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overscroll-behavior: contain;
  -webkit-overflow-scrolling: touch;
  padding: 6px 8px;
}

.model-selector-add {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 8px;
  border-radius: 6px;
  border: 1px solid #e1e5e6;
  background: #fff;
  color: #52575a;
  font-size: 11px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.12s;
}

.model-selector-add .add-icon {
  font-size: 12px;
  line-height: 1;
}

.model-selector-add:hover {
  border-color: #10b981;
  color: #10b981;
  background: #f0fdf6;
}

.model-option {
  padding: 6px 8px;
  cursor: pointer;
  transition: background 0.12s;
  border-radius: 6px;
  margin-bottom: 4px;
  
  &:last-child {
    margin-bottom: 0;
  }
  
  &:hover {
    background: #f6f8f7;
  }
  
  &.selected {
    background: #eefdf5;
    
    .model-option-name {
      color: #10b981;
      font-weight: 600;
    }
  }
  
  &.empty {
    color: #9aa0a6;
    cursor: default;
    text-align: center;
    padding: 20px 8px;
    
    &:hover {
      background: transparent;
    }
  }
}

.model-option-main {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 1px;
}

.model-option-name {
  font-size: 12px;
  color: #222;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  line-height: 1.4;
}

.model-option-desc {
  font-size: 11px;
  color: #8b9196;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  margin-top: 1px;
}

.model-badge-remote,
.model-badge-local {
  display: inline-block;
  padding: 1px 5px;
  font-size: 10px;
  border-radius: 3px;
  font-weight: 500;
  flex-shrink: 0;
}

.model-badge-remote {
  background: rgba(16, 185, 129, 0.1);
  color: #10b981;
}

.model-badge-local {
  background: rgba(139, 145, 150, 0.1);
  color: #52575a;
}

/* Agent 模式选择下拉菜单 */
.agent-mode-selector-overlay {
  position: fixed;
  inset: 0;
  z-index: 9998;
  background: transparent;
  touch-action: none;
}

.agent-mode-selector-dropdown {
  position: fixed !important;
  z-index: 9999;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 6px 28px rgba(15, 23, 42, 0.08);
  border: 1px solid #e7e9eb;
  overflow: hidden;
  padding: 6px 8px;
  min-width: 200px;
  display: flex;
  flex-direction: column;
  margin: 0 !important;
  padding: 0 !important;
  transform: none !important;
}

.agent-mode-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 10px;
  cursor: pointer;
  transition: background 0.12s;
  border-radius: 6px;
  position: relative;
  margin: 4px 6px;
  
  &:hover:not(.disabled) {
    background: #f6f8f7;
  }
  
  &.disabled {
    opacity: 0.6;
    cursor: not-allowed;
    
    &:hover {
      background: transparent;
    }
  }
  
  &.selected {
    background: #eefdf5;
    
    .agent-mode-option-name {
      color: #10b981;
      font-weight: 700;
    }
  }
}

.agent-mode-option-main {
  display: flex;
  flex-direction: column;
  gap: 1px;
  flex: 1;
  min-width: 0;
}

.agent-mode-option-name {
  font-size: 12px;
  font-weight: 600;
  color: #222;
  line-height: 1.4;
  transition: color 0.12s;
}

.agent-mode-option-desc {
  font-size: 11px;
  color: #8b9196;
  line-height: 1.3;
}

.check-icon {
  width: 14px;
  height: 14px;
  color: #10b981;
  flex-shrink: 0;
  margin-left: 6px;
}

.agent-mode-warning {
  display: flex;
  align-items: center;
  margin-left: 6px;
  
  .warning-icon {
    color: #ff9800;
    font-size: 14px;
  }
}

.agent-mode-footer {
  padding: 6px 10px;
  border-top: 1px solid #f2f4f5;
  margin-top: 2px;
  background: #fafcfc;
}

.agent-mode-link {
  color: #10b981;
  text-decoration: none;
  font-size: 11px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 3px;
  transition: all 0.12s;
  
  &:hover {
    color: #059669;
    text-decoration: underline;
  }
}
</style>


