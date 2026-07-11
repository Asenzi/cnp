<template>
  <view class="action-card">
    <button class="create-btn" :class="{ 'create-btn-disabled': loading }" :disabled="loading"
      hover-class="create-btn-active" @tap="emit('submit')">
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
.action-card {
  margin: 0;
  /* background: #ffffff; */
  padding: 24rpx 32rpx;
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
  .action-card {
    background: #0f172a;
  }

  .create-btn {
    background: #3b82f6;
  }
}
</style>
