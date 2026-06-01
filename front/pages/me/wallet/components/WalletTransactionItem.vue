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
  padding: 32rpx 0;
  border-bottom: 1rpx solid #f3f4f6;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.tx-left {
  min-width: 0;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.tx-icon-wrap {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
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
  background: #f9fafb;
}

.tx-icon {
  width: 44rpx;
  height: 44rpx;
}

.tx-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.tx-title {
  color: #111827;
  font-size: 30rpx;
  font-weight: 400;
  line-height: 1.3;
}

.tx-time {
  color: #9ca3af;
  font-size: 26rpx;
  line-height: 1.2;
  font-weight: 400;
}

.tx-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8rpx;
}

.tx-amount {
  font-size: 32rpx;
  font-weight: 500;
  line-height: 1.2;
}

.tx-amount-income {
  color: #111827;
}

.tx-amount-expense {
  color: #111827;
}

.tx-status {
  padding: 6rpx 16rpx;
  border-radius: 6rpx;
  font-size: 22rpx;
  font-weight: 400;
}

.tx-status-income {
  color: #059669;
  background: #d1fae5;
}

.tx-status-expense {
  color: #dc2626;
  background: #fee2e2;
}

.tx-status-pending {
  color: #d97706;
  background: #fef3c7;
}

@media (prefers-color-scheme: dark) {
  .tx-item {
    background: #111827;
    border-bottom-color: #1f2937;
  }

  .icon-bg-blue {
    background: rgba(37, 99, 235, 0.12);
  }

  .icon-bg-orange {
    background: rgba(249, 115, 22, 0.12);
  }

  .icon-bg-slate {
    background: #1f2937;
  }

  .tx-title {
    color: #f9fafb;
  }

  .tx-time {
    color: #6b7280;
  }

  .tx-amount-income {
    color: #f9fafb;
  }

  .tx-amount-expense {
    color: #f9fafb;
  }

  .tx-status-income {
    color: #34d399;
    background: rgba(52, 211, 153, 0.12);
  }

  .tx-status-expense {
    color: #f87171;
    background: rgba(248, 113, 113, 0.12);
  }

  .tx-status-pending {
    color: #fbbf24;
    background: rgba(251, 191, 36, 0.12);
  }
}
</style>
