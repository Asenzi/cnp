<template>
  <view class="tx-item">
    <view class="tx-left">
      <view class="tx-icon-wrap" :class="item.iconBgClass || 'icon-bg-slate'">
        <image v-if="item.iconPath" class="tx-icon" mode="aspectFit" :src="item.iconPath" />
      </view>
      <view class="tx-main">
        <text class="tx-title">{{ item.title }}</text>
        <text class="tx-time">{{ item.timeText }}</text>
      </view>
    </view>

    <view class="tx-right">
      <text class="tx-amount" :class="amountClass">{{ amountText }}</text>
      <text class="tx-status" :class="statusClass">{{ item.statusText || '--' }}</text>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { formatMoney } from '../modules/wallet-view-model'

const props = defineProps({
  item: {
    type: Object,
    default: () => ({})
  }
})

const amountValue = computed(() => Number(props.item?.amount || 0))

const amountText = computed(() => {
  const amount = amountValue.value
  const prefix = amount >= 0 ? '+ ' : '- '
  return `${prefix}¥${formatMoney(Math.abs(amount), 2)}`
})

const amountClass = computed(() => {
  if (amountValue.value >= 0) {
    return 'tx-amount-income'
  }
  return 'tx-amount-expense'
})

const statusClass = computed(() => {
  const text = String(props.item?.statusText || '').trim()
  if (text.includes('失败')) {
    return 'tx-status-expense'
  }
  if (text.includes('处理')) {
    return 'tx-status-pending'
  }
  return 'tx-status-income'
})
</script>

<style scoped>
.tx-item {
  padding: 24rpx;
  border-radius: 24rpx;
  background: #ffffff;
  box-shadow: 0 2rpx 10rpx rgba(15, 23, 42, 0.05);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
}

.tx-left {
  min-width: 0;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.tx-icon-wrap {
  width: 68rpx;
  height: 68rpx;
  border-radius: 16rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-bg-blue {
  background: #eff6ff;
}

.icon-bg-orange {
  background: #fff7ed;
}

.icon-bg-slate {
  background: #f1f5f9;
}

.tx-icon {
  width: 38rpx;
  height: 38rpx;
}

.tx-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.tx-title {
  color: #0f172a;
  font-size: 26rpx;
  font-weight: 700;
  line-height: 1.3;
}

.tx-time {
  color: #64748b;
  font-size: 22rpx;
  line-height: 1.2;
}

.tx-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4rpx;
}

.tx-amount {
  font-size: 28rpx;
  font-weight: 700;
  line-height: 1.2;
}

.tx-amount-income {
  color: #1a57db;
}

.tx-amount-expense {
  color: #e11d48;
}

.tx-status {
  font-size: 18rpx;
  font-weight: 700;
  text-transform: uppercase;
}

.tx-status-income {
  color: rgba(26, 87, 219, 0.6);
}

.tx-status-expense {
  color: rgba(225, 29, 72, 0.6);
}

.tx-status-pending {
  color: rgba(234, 88, 12, 0.72);
}

@media (prefers-color-scheme: dark) {
  .tx-item {
    background: #0f172a;
    box-shadow: none;
  }

  .tx-title {
    color: #e2e8f0;
  }

  .tx-time {
    color: #94a3b8;
  }
}
</style>
