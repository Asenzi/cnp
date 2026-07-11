<template>
  <view
    class="plan-card"
    :class="{ 'is-selected': selected }"
    hover-class="plan-hover"
    @tap="$emit('select', plan)"
  >
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
  border: 0;
  border-radius: 16rpx;
  padding: 32rpx;
  box-shadow: none;
  transition: all 0.3s ease;
}

.plan-hover {
  transform: translateY(-4rpx);
  box-shadow: none;
}

.is-selected {
  border: 0;
  background: linear-gradient(to bottom, #ffffff 0%, #f4f8ff 100%);
  box-shadow: none;
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
  font-size: 28rpx;
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
  color: #2f5fbd;
}

.price-original {
  display: block;
  color: #9ca3af;
  font-size: 22rpx;
  line-height: 28rpx;
  text-decoration: line-through;
}
</style>
