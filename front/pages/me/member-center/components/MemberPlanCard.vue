<template>
  <view
    class="plan-card"
    :class="{ 'is-selected': selected }"
    hover-class="plan-hover"
    @tap="$emit('select', plan)"
  >
    <view v-if="plan.recommended && plan.badgeText" class="recommend-tag">
      {{ plan.badgeText }}
    </view>

    <view class="card-body">
      <view class="plan-header">
        <text class="plan-name">{{ plan.name }}</text>
        <text v-if="plan.subtitle" class="plan-subtitle">{{ plan.subtitle }}</text>
      </view>

      <view class="plan-pricing">
        <view class="price-main">
          <text class="currency">¥</text>
          <text class="amount">{{ formatAmount(plan.price) }}</text>
        </view>
        <text v-if="showOriginalPrice" class="price-original">
          原价 ¥{{ formatAmount(plan.originalPrice) }}
        </text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  plan: {
    type: Object,
    default: () => ({})
  },
  selected: {
    type: Boolean,
    default: false
  }
})

defineEmits(['select'])

const showOriginalPrice = computed(() => {
  const original = Number(props.plan?.originalPrice || 0)
  const current = Number(props.plan?.price || 0)
  return Number.isFinite(original) && original > 0 && original > current
})

const formatAmount = (value) => {
  const n = Number(value)
  if (!Number.isFinite(n) || n <= 0) {
    return '0'
  }
  if (Number.isInteger(n)) {
    return `${n}`
  }
  return n.toFixed(2)
}
</script>

<style scoped>
.plan-card {
  position: relative;
  background: #ffffff;
  border: 2rpx solid #e5e7eb;
  border-radius: 16rpx;
  padding: 32rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.04), 0 1rpx 2rpx rgba(0, 0, 0, 0.02);
  transition: all 0.3s ease;
}

.plan-hover {
  transform: translateY(-4rpx);
  box-shadow: 0 8rpx 20rpx rgba(0, 0, 0, 0.1), 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}

.is-selected {
  border-color: #1a57db;
  border-width: 3rpx;
  background: linear-gradient(to bottom, #ffffff 0%, #f0f7ff 100%);
  box-shadow: 0 4rpx 16rpx rgba(26, 87, 219, 0.25), 0 2rpx 8rpx rgba(26, 87, 219, 0.15), inset 0 1rpx 0 rgba(26, 87, 219, 0.05);
}

.recommend-tag {
  position: absolute;
  left: 32rpx;
  top: -14rpx;
  padding: 6rpx 20rpx;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  border-radius: 8rpx;
  color: #78350f;
  font-size: 22rpx;
  line-height: 28rpx;
  font-weight: 600;
  box-shadow: 0 4rpx 12rpx rgba(251, 191, 36, 0.35), 0 2rpx 4rpx rgba(251, 191, 36, 0.2);
}

.card-body {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 32rpx;
}

.plan-header {
  flex: 1;
  min-width: 0;
}

.plan-name {
  display: block;
  color: #111827;
  font-size: 32rpx;
  line-height: 40rpx;
  font-weight: 600;
  margin-bottom: 8rpx;
}

.plan-subtitle {
  display: block;
  color: #6b7280;
  font-size: 24rpx;
  line-height: 32rpx;
}

.plan-pricing {
  text-align: right;
  flex-shrink: 0;
}

.price-main {
  display: flex;
  align-items: baseline;
  justify-content: flex-end;
  gap: 4rpx;
  margin-bottom: 6rpx;
}

.currency {
  color: #111827;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.amount {
  color: #111827;
  font-size: 48rpx;
  line-height: 56rpx;
  font-weight: 700;
  letter-spacing: -0.02em;
}

.is-selected .currency,
.is-selected .amount {
  color: #1a57db;
}

.price-original {
  display: block;
  color: #9ca3af;
  font-size: 22rpx;
  line-height: 28rpx;
  text-decoration: line-through;
}
</style>
