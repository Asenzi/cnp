<template>
  <view class="composer-wrap">
    <view class="composer-bar">
      <button class="icon-btn" hover-class="icon-btn-active">
        <ChatGlyph name="smile" :size="22" color="#64748b" />
      </button>

      <view class="input-wrap">
        <input
          class="text-input"
          :value="modelValue"
          :maxlength="2000"
          type="text"
          confirm-type="send"
          placeholder="输入消息..."
          placeholder-class="input-placeholder"
          @input="onInput"
          @confirm="$emit('send')"
        />
      </view>

      <button class="icon-btn" hover-class="icon-btn-active" @tap="$emit('primary-action')">
        <ChatGlyph
          :name="hasText ? 'send' : 'plus-circle'"
          :size="24"
          :color="hasText ? '#1a57db' : '#64748b'"
        />
      </button>
    </view>

    <scroll-view
      v-if="showQuickPanel"
      class="quick-panel"
      scroll-x
      :show-scrollbar="false"
    >
      <view class="quick-list">
        <button
          v-for="item in actions"
          :key="item.key"
          class="quick-item"
          hover-class="quick-item-active"
          @tap="$emit('tap-action', item)"
        >
          <view class="quick-icon-box">
            <ChatGlyph :name="item.icon" :size="20" color="#475569" />
          </view>
          <text class="quick-label">{{ item.label }}</text>
        </button>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import ChatGlyph from './ChatGlyph.vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: ''
  },
  sending: {
    type: Boolean,
    default: false
  },
  showQuickPanel: {
    type: Boolean,
    default: true
  },
  actions: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['update:modelValue', 'send', 'primary-action', 'tap-action'])

const hasText = computed(() => Boolean(String(props.modelValue || '').trim()) && !props.sending)

const onInput = (event) => {
  emit('update:modelValue', String(event?.detail?.value || ''))
}
</script>

<style scoped>
.composer-wrap {
  border-top: 1rpx solid #e5e7eb;
  background: rgba(255, 255, 255, 0.96);
  padding: 14rpx 16rpx calc(10rpx + env(safe-area-inset-bottom));
}

.composer-bar {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.icon-btn {
  width: 64rpx;
  height: 64rpx;
  border: 0;
  border-radius: 999rpx;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  margin: 0;
  padding: 0;
}

.icon-btn::after {
  border: 0;
}

.icon-btn-active {
  opacity: 0.76;
}

.input-wrap {
  flex: 1;
  height: 68rpx;
  border-radius: 999rpx;
  background: #f1f5f9;
  padding: 0 20rpx;
  display: flex;
  align-items: center;
}

.text-input {
  flex: 1;
  height: 68rpx;
  color: #0f172a;
  font-size: 30rpx;
}

.input-placeholder {
  color: #94a3b8;
}

.quick-panel {
  margin-top: 12rpx;
}

.quick-list {
  display: inline-flex;
  align-items: flex-start;
  gap: 10rpx;
  padding: 0 4rpx 8rpx;
}

.quick-item {
  width: 108rpx;
  border: 0;
  background: transparent;
  margin: 0;
  padding: 0;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.quick-item::after {
  border: 0;
}

.quick-item-active {
  opacity: 0.8;
}

.quick-icon-box {
  width: 72rpx;
  height: 72rpx;
  border-radius: 16rpx;
  background: #f1f5f9;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.quick-label {
  color: #64748b;
  font-size: 19rpx;
  line-height: 26rpx;
}

@media (prefers-color-scheme: dark) {
  .composer-wrap {
    border-top-color: #1f2937;
    background: rgba(15, 23, 42, 0.96);
  }

  .input-wrap,
  .quick-icon-box {
    background: #1f2937;
  }

  .text-input {
    color: #f8fafc;
  }

  .input-placeholder,
  .quick-label {
    color: #94a3b8;
  }
}
</style>
