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
  background: rgba(255, 255, 255, 0.84);
  border-top: 1rpx solid #e2e8f0;
  backdrop-filter: blur(12rpx);
  padding: 14rpx 24rpx calc(14rpx + env(safe-area-inset-bottom));
}

.create-btn {
  width: 100%;
  height: 88rpx;
  border-radius: 16rpx;
  border: 0;
  background: #1a57db;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 700;
  box-shadow: 0 10rpx 20rpx rgba(26, 87, 219, 0.22);
  display: flex;
  align-items: center;
  justify-content: center;
}

.create-btn-active {
  opacity: 0.88;
}

.create-btn-disabled {
  opacity: 0.75;
}

@media (prefers-color-scheme: dark) {
  .bottom-wrap {
    background: rgba(17, 22, 33, 0.88);
    border-top-color: #1e293b;
  }
}
</style>
