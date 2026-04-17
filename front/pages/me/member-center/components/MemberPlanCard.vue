<template>
  <view
    class="plan-card"
    :class="[
      plan.recommended ? 'plan-card-recommended' : '',
      selected ? 'plan-card-selected' : ''
    ]"
    hover-class="plan-card-active"
    @tap="$emit('select', plan)"
  >
    <view v-if="plan.recommended && plan.badgeText" class="plan-badge">
      <text class="plan-badge-text">{{ plan.badgeText }}</text>
    </view>

    <view class="plan-main">
      <view>
        <text class="plan-name">{{ plan.name }}</text>
        <text v-if="plan.subtitle" class="plan-subtitle">{{ plan.subtitle }}</text>
        <text v-if="pointsOfferText" class="plan-points-offer">{{ pointsOfferText }}</text>
      </view>

      <view class="price-wrap">
        <text class="price-main">¥{{ formatAmount(plan.price) }}</text>
        <text v-if="showOriginalPrice" class="price-origin">¥{{ formatAmount(plan.originalPrice) }}</text>
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

const pointsOfferText = computed(() => {
  const offer = props.plan?.pointsOffer
  if (!offer || !offer.enabled) {
    return ''
  }
  const requiredPoints = Number(offer.required_points || offer.requiredPoints || 0)
  const discountText = String(offer.discount_text || offer.discountText || '').trim()
  if (!requiredPoints || !discountText) {
    return ''
  }
  const missingPoints = Number(offer.missing_points || offer.missingPoints || 0)
  if (offer.can_use || offer.canUse) {
    return `${requiredPoints}积分可享${discountText}`
  }
  if (missingPoints > 0) {
    return `${requiredPoints}积分可享${discountText}，还差${missingPoints}积分`
  }
  return `${requiredPoints}积分可享${discountText}`
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
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  padding: 20px;
}

.plan-card-recommended {
  border: 2px solid #d4af37;
  background: rgba(212, 175, 55, 0.05);
}

.plan-card-selected {
  border-color: #1a57db;
  box-shadow: 0 0 0 2px rgba(26, 87, 219, 0.14);
}

.plan-card-active {
  opacity: 0.9;
}

.plan-badge {
  position: absolute;
  right: 0;
  top: 0;
  border-radius: 0 3px 0 8px;
  background: #d4af37;
  padding: 4px 10px;
  z-index: 2;
}

.plan-badge-text {
  color: #111621;
  font-size: 11px;
  line-height: 14px;
  font-weight: 700;
}

.plan-main {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 14px;
}

.plan-card-recommended .plan-main {
  margin-top: 26px;
}

.plan-name {
  display: block;
  color: #0f172a;
  font-size: 19px;
  line-height: 26px;
  font-weight: 700;
}

.plan-subtitle {
  display: block;
  margin-top: 4px;
  color: #64748b;
  font-size: 13px;
  line-height: 18px;
}

.plan-points-offer {
  display: block;
  margin-top: 8px;
  color: #1d4ed8;
  font-size: 12px;
  line-height: 17px;
  font-weight: 700;
}

.price-wrap {
  text-align: right;
}

.price-main {
  display: block;
  color: #0f172a;
  font-size: 25px;
  line-height: 32px;
  font-weight: 800;
}

.plan-card-recommended .price-main {
  color: #d4af37;
}

.price-origin {
  display: block;
  color: #94a3b8;
  font-size: 15px;
  line-height: 20px;
  text-decoration: line-through;
}

@media (prefers-color-scheme: dark) {
  .plan-card {
    background: #0f172a;
    border-color: #1e293b;
  }

  .plan-card-recommended {
    border-color: #d4af37;
    background: rgba(212, 175, 55, 0.12);
  }

  .plan-name,
  .price-main {
    color: #e2e8f0;
  }

  .plan-subtitle,
  .price-origin {
    color: #94a3b8;
  }
}
</style>
