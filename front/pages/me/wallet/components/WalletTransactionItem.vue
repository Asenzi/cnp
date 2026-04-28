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
  padding: 24rpx 28rpx;
  border-radius: 20rpx;
  background: #ffffff;
  border: 1rpx solid #f1f5f9;
  box-shadow: 0 2rpx 12rpx rgba(15, 23, 42, 0.04);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 20rpx;
  transition: all 0.2s ease;
}

.tx-left {
  min-width: 0;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.tx-icon-wrap {
  width: 72rpx;
  height: 72rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  position: relative;
  overflow: hidden;
}

.tx-icon-wrap::before {
  content: '';
  position: absolute;
  inset: 0;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0.5) 0%, transparent 100%);
  opacity: 0.3;
}

.icon-bg-blue {
  background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
}

.icon-bg-orange {
  background: linear-gradient(135deg, #fed7aa 0%, #fdba74 100%);
}

.icon-bg-slate {
  background: linear-gradient(135deg, #f1f5f9 0%, #e2e8f0 100%);
}

.tx-icon {
  width: 40rpx;
  height: 40rpx;
  position: relative;
  z-index: 1;
}

.tx-main {
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.tx-title {
  color: #0f172a;
  font-size: 28rpx;
  font-weight: 600;
  line-height: 1.3;
}

.tx-time {
  color: #64748b;
  font-size: 22rpx;
  line-height: 1.2;
  font-weight: 500;
}

.tx-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 6rpx;
}

.tx-amount {
  font-size: 30rpx;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: 0.5rpx;
}

.tx-amount-income {
  color: #1a57db;
}

.tx-amount-expense {
  color: #e11d48;
}

.tx-status {
  padding: 4rpx 12rpx;
  border-radius: 12rpx;
  font-size: 18rpx;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5rpx;
}

.tx-status-income {
  color: #1a57db;
  background: rgba(26, 87, 219, 0.1);
}

.tx-status-expense {
  color: #e11d48;
  background: rgba(225, 29, 72, 0.1);
}

.tx-status-pending {
  color: #ea580c;
  background: rgba(234, 88, 12, 0.1);
}

@media (prefers-color-scheme: dark) {
  .tx-item {
    background: #1e293b;
    border-color: #334155;
    box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.2);
  }

  .icon-bg-blue {
    background: linear-gradient(135deg, #1e3a8a 0%, #1e40af 100%);
  }

  .icon-bg-orange {
    background: linear-gradient(135deg, #9a3412 0%, #c2410c 100%);
  }

  .icon-bg-slate {
    background: linear-gradient(135deg, #334155 0%, #475569 100%);
  }

  .tx-title {
    color: #f1f5f9;
  }

  .tx-time {
    color: #94a3b8;
  }

  .tx-amount-income {
    color: #60a5fa;
  }

  .tx-amount-expense {
    color: #fb7185;
  }

  .tx-status-income {
    color: #60a5fa;
    background: rgba(96, 165, 250, 0.15);
  }

  .tx-status-expense {
    color: #fb7185;
    background: rgba(251, 113, 133, 0.15);
  }

  .tx-status-pending {
    color: #fb923c;
    background: rgba(251, 146, 60, 0.15);
  }
}
</style>
