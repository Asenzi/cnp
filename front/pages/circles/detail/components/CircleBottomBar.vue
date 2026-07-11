<template>
  <view class="bottom-bar">
    <view class="price-wrap">
      <view class="price-row">
        <text class="price-main">¥{{ price.current }}</text>
        <text class="price-unit">/年</text>
      </view>
      <text class="price-note">{{ Number(price.current || 0) > 0 ? '拒绝申请将退回费用' : '无需支付费用' }}</text>
    </view>

    <view class="actions-row">
      <button
        class="interest-btn"
        hover-class="button-pressed"
        @tap="emit('interest')"
      >
        {{ interested ? '已收藏' : '去收藏' }}
      </button>
      <button
        class="apply-btn"
        :class="{ 'apply-btn-disabled': disabled }"
        :disabled="disabled"
        hover-class="button-pressed"
        @tap="emit('apply')"
      >
        {{ actionText }}
      </button>
    </view>
  </view>
</template>

<script setup>
defineProps({
  price: {
    type: Object,
    default: () => ({ current: '0.00' })
  },
  interested: {
    type: Boolean,
    default: false
  },
  actionText: {
    type: String,
    default: '申请加入'
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['interest', 'apply'])
</script>

<style scoped>
.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 40;
  padding: 16rpx 32rpx calc(16rpx + env(safe-area-inset-bottom));
  border-top: 1rpx solid #edf1f5;
  background: rgba(255, 255, 255, 0.96);
  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.price-wrap {
  min-width: 172rpx;
  display: flex;
  flex-direction: column;
}

.price-row {
  display: flex;
  align-items: flex-end;
  gap: 4rpx;
}

.price-main {
  color: #dc2626;
  font-size: 36rpx;
  line-height: 40rpx;
  font-weight: 700;
}

.price-unit {
  padding-bottom: 2rpx;
  color: #64748b;
  font-size: 21rpx;
  line-height: 30rpx;
}

.price-note {
  margin-top: 4rpx;
  color: #94a3b8;
  font-size: 19rpx;
  line-height: 28rpx;
}

.actions-row {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.interest-btn,
.apply-btn {
  flex: 1;
  height: 76rpx;
  margin: 0;
  border: 0;
  border-radius: 12rpx;
  padding: 0 24rpx;
  font-size: 25rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 0;
}

.interest-btn::after,
.apply-btn::after {
  border: 0;
}

.interest-btn {
  background: #f1f5f9;
  color: #475569;
}

.apply-btn {
  background: #2563eb;
  color: #ffffff;
}

.apply-btn-disabled {
  background: #cbd5e1;
  color: #ffffff;
}

.button-pressed {
  opacity: 0.82;
}
</style>
