<template>
  <view class="bottom-wrap">
    <button
      class="create-btn"
      :class="{ 'create-btn-disabled': loading }"
      :disabled="loading"
      hover-class="create-btn-active"
      @tap="emit('submit')"
    >
      {{ loading ? loadingText : text }}
    </button>
  </view>
</template>

<script setup>
defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  loadingText: {
    type: String,
    default: '创建中...'
  },
  text: {
    type: String,
    default: '立即创建圈子'
  }
})

const emit = defineEmits(['submit'])
</script>

<style scoped>
.bottom-wrap {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 30;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(12rpx);
  padding: 12rpx 32rpx calc(12rpx + env(safe-area-inset-bottom));
}

.create-btn {
  width: 100%;
  height: 88rpx;
  border-radius: 12rpx;
  border: 0;
  background: #2563eb;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.create-btn-active {
  opacity: 0.85;
}

.create-btn-disabled {
  opacity: 0.6;
}

@media (prefers-color-scheme: dark) {
  .bottom-wrap {
    background: rgba(15, 23, 42, 0.92);
  }

  .create-btn {
    background: #3b82f6;
  }
}
</style>
