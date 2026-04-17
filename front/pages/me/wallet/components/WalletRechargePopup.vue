<template>
  <view v-if="show" class="recharge-popup">
    <view class="popup-mask" @tap="onClose"></view>
    <view class="popup-panel" @tap.stop>
      <view class="popup-head">
        <text class="popup-title">选择充值金额</text>
        <text class="popup-close" @tap="onClose">×</text>
      </view>

      <view class="amount-grid">
        <view
          v-for="amount in presetAmounts"
          :key="amount"
          class="amount-item"
          :class="{ 'amount-item-active': selectedPreset === amount }"
          @tap="onSelectPreset(amount)"
        >
          <text class="amount-yuan">¥</text>
          <text class="amount-value">{{ amount }}</text>
        </view>
      </view>

      <view class="custom-wrap">
        <text class="custom-label">自定义金额</text>
        <view class="custom-input-wrap">
          <text class="custom-yuan">¥</text>
          <input
            class="custom-input"
            type="digit"
            placeholder="请输入充值金额"
            :value="customText"
            @input="onCustomInput"
          />
        </view>
      </view>

      <view class="submit-wrap">
        <button class="submit-btn" :disabled="loading" :class="{ 'submit-btn-disabled': loading }" @tap="onSubmit">
          <text>{{ loading ? '支付处理中...' : `确认支付 ¥${displayAmount}` }}</text>
        </button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref, watch } from 'vue'

const props = defineProps({
  show: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  presetAmounts: {
    type: Array,
    default: () => [50, 100, 200, 500, 1000]
  }
})

const emit = defineEmits(['close', 'submit'])

const selectedPreset = ref(0)
const customText = ref('')

const customAmount = computed(() => {
  const value = Number(customText.value || 0)
  if (!Number.isFinite(value)) {
    return 0
  }
  return Number(value.toFixed(2))
})

const selectedAmount = computed(() => {
  if (selectedPreset.value > 0) {
    return selectedPreset.value
  }
  return customAmount.value
})

const displayAmount = computed(() => {
  return selectedAmount.value > 0 ? selectedAmount.value.toFixed(2) : '0.00'
})

watch(
  () => props.show,
  (visible) => {
    if (!visible) {
      return
    }
    selectedPreset.value = Number(props.presetAmounts?.[0] || 0)
    customText.value = ''
  }
)

const onClose = () => {
  if (props.loading) {
    return
  }
  emit('close')
}

const onSelectPreset = (amount) => {
  selectedPreset.value = Number(amount || 0)
  customText.value = ''
}

const onCustomInput = (event) => {
  const value = String(event?.detail?.value || '')
  customText.value = value
  if (value.trim()) {
    selectedPreset.value = 0
  }
}

const onSubmit = () => {
  const amount = selectedAmount.value
  if (!Number.isFinite(amount) || amount <= 0) {
    uni.showToast({
      title: '请输入有效充值金额',
      icon: 'none'
    })
    return
  }
  emit('submit', Number(amount.toFixed(2)))
}
</script>

<style scoped>
.recharge-popup {
  position: fixed;
  inset: 0;
  z-index: 300;
}

.popup-mask {
  position: absolute;
  inset: 0;
  background: rgba(15, 23, 42, 0.45);
}

.popup-panel {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 32rpx 32rpx 0 0;
  background: #ffffff;
  padding: 28rpx 28rpx calc(28rpx + env(safe-area-inset-bottom));
}

.popup-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.popup-title {
  color: #0f172a;
  font-size: 32rpx;
  font-weight: 700;
}

.popup-close {
  color: #64748b;
  font-size: 44rpx;
  line-height: 1;
  width: 56rpx;
  text-align: center;
}

.amount-grid {
  margin-top: 24rpx;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14rpx;
}

.amount-item {
  height: 86rpx;
  border: 1rpx solid #cbd5e1;
  border-radius: 18rpx;
  display: flex;
  align-items: baseline;
  justify-content: center;
  background: #f8fafc;
}

.amount-item-active {
  border-color: #1a57db;
  background: rgba(26, 87, 219, 0.08);
}

.amount-yuan {
  font-size: 24rpx;
  color: #1e293b;
  margin-right: 4rpx;
}

.amount-value {
  font-size: 32rpx;
  color: #0f172a;
  font-weight: 700;
}

.custom-wrap {
  margin-top: 22rpx;
}

.custom-label {
  display: block;
  color: #334155;
  font-size: 24rpx;
}

.custom-input-wrap {
  margin-top: 12rpx;
  height: 84rpx;
  border: 1rpx solid #cbd5e1;
  border-radius: 16rpx;
  background: #f8fafc;
  display: flex;
  align-items: center;
  padding: 0 20rpx;
}

.custom-yuan {
  color: #0f172a;
  font-size: 30rpx;
  font-weight: 700;
}

.custom-input {
  flex: 1;
  margin-left: 8rpx;
  color: #0f172a;
  font-size: 30rpx;
}

.submit-wrap {
  margin-top: 26rpx;
}

.submit-btn {
  height: 88rpx;
  border: 0;
  border-radius: 20rpx;
  background: #1a57db;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 700;
}

.submit-btn::after {
  border: 0;
}

.submit-btn-disabled {
  opacity: 0.7;
}
</style>
