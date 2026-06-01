<template>
  <view class="recharge-page">
    <scroll-view class="recharge-scroll" scroll-y :show-scrollbar="false">
      <view class="page-content">
        <view class="section">
          <text class="section-title">选择充值金额</text>
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
        </view>

        <view class="section">
          <text class="section-title">自定义金额</text>
          <view class="custom-input-wrap" :class="{ 'custom-input-wrap-active': selectedPreset === 0 }">
            <text class="custom-yuan">¥</text>
            <input
              class="custom-input"
              type="digit"
              placeholder="请输入充值金额"
              :value="customText"
              @input="onCustomInput"
            />
          </view>
          <text class="tip-text">单笔充值金额 0.01 - 200000 元</text>
        </view>

        <view class="section pay-summary">
          <view class="summary-row">
            <text class="summary-label">支付方式</text>
            <view class="summary-value-wrap">
              <image class="summary-icon" src="/static/me-icons/payments-green.png" mode="aspectFit" />
              <text class="summary-value">微信支付</text>
            </view>
          </view>
          <view class="summary-row">
            <text class="summary-label">应付金额</text>
            <text class="summary-amount">¥{{ displayAmount }}</text>
          </view>
        </view>

        <view class="safe-tip">
          <image class="safe-icon" src="/static/me-icons/shield-person-primary.png" mode="aspectFit" />
          <text class="safe-text">支付全程加密，充值成功后余额实时到账</text>
        </view>
      </view>
    </scroll-view>

    <view class="bottom-bar">
      <button
        class="submit-btn"
        :disabled="submitDisabled"
        :class="{ 'submit-btn-disabled': submitDisabled }"
        @tap="onSubmit"
      >
        <text>{{ submitButtonText }}</text>
      </button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { confirmWalletRechargePayment, createWalletRecharge, getWalletRechargeStatus } from '../../../../api/payment'

const MIN_AMOUNT = 0.01
const MAX_AMOUNT = 200000
const presetAmounts = [50, 100, 200, 500, 1000]

const selectedPreset = ref(50)
const customText = ref('')
const submitting = ref(false)

const customAmount = computed(() => {
  const value = Number(customText.value || 0)
  if (!Number.isFinite(value)) {
    return 0
  }
  return Number(value.toFixed(2))
})

const selectedAmount = computed(() => {
  if (selectedPreset.value > 0) {
    return Number(selectedPreset.value)
  }
  return Number(customAmount.value)
})

const isValidAmount = computed(() => {
  const amount = Number(selectedAmount.value || 0)
  return Number.isFinite(amount) && amount >= MIN_AMOUNT && amount <= MAX_AMOUNT
})

const displayAmount = computed(() => {
  return isValidAmount.value ? selectedAmount.value.toFixed(2) : '0.00'
})

const submitDisabled = computed(() => submitting.value || !isValidAmount.value)

const submitButtonText = computed(() => {
  if (submitting.value) {
    return '支付处理中...'
  }
  return `确认支付 ¥${displayAmount.value}`
})

const normalizeInputAmount = (rawValue) => {
  const source = String(rawValue || '')
  let result = source.replace(/[^\d.]/g, '')
  const firstDot = result.indexOf('.')
  if (firstDot >= 0) {
    result =
      result.slice(0, firstDot + 1) +
      result
        .slice(firstDot + 1)
        .replace(/\./g, '')
        .slice(0, 2)
  }
  if (result.startsWith('.')) {
    result = `0${result}`
  }
  return result
}

const onSelectPreset = (amount) => {
  selectedPreset.value = Number(amount || 0)
  customText.value = ''
}

const onCustomInput = (event) => {
  const value = normalizeInputAmount(event?.detail?.value)
  customText.value = value
  if (value.trim()) {
    selectedPreset.value = 0
  }
}

const invokeWxpayAndConfirm = async (createResult) => {
  const orderNo = String(createResult?.order_no || '').trim()
  const wxpay = createResult?.wxpay || {}
  if (!orderNo || !wxpay?.timeStamp || !wxpay?.nonceStr || !wxpay?.package || !wxpay?.signType || !wxpay?.paySign) {
    throw new Error('微信支付参数异常')
  }

  const payRes = await new Promise((resolve, reject) => {
    uni.requestPayment({
      timeStamp: String(wxpay.timeStamp),
      nonceStr: String(wxpay.nonceStr),
      package: String(wxpay.package),
      signType: String(wxpay.signType),
      paySign: String(wxpay.paySign),
      success: (res) => resolve(res || {}),
      fail: (err) =>
        reject({
          ...(err || {}),
          order_no: orderNo
        })
    })
  })

  try {
    await confirmWalletRechargePayment(orderNo, {
      transaction_id: String(payRes?.transactionId || payRes?.transaction_id || '').trim(),
      ext: payRes
    })
  } catch (err) {
    const status = await getWalletRechargeStatus(orderNo)
    if (!Boolean(status?.paid)) {
      throw err
    }
  }
}

const backToWallet = () => {
  setTimeout(() => {
    uni.navigateBack()
  }, 350)
}

const handlePaymentSuccess = () => {
  uni.showToast({
    title: '充值成功',
    icon: 'success'
  })
  backToWallet()
}

const onSubmit = async () => {
  if (submitting.value) {
    return
  }

  const token = String(uni.getStorageSync('token') || '').trim()
  if (!token) {
    uni.showToast({
      title: '请先登录',
      icon: 'none'
    })
    return
  }

  if (!isValidAmount.value) {
    uni.showToast({
      title: '请输入有效充值金额',
      icon: 'none'
    })
    return
  }

  submitting.value = true
  uni.showLoading({
    title: '处理中...'
  })

  try {
    const amount = Number(selectedAmount.value)
    const createResult = await createWalletRecharge({ amount })
    const action = String(createResult?.action || '').trim()

    // 微信支付流程
    if (action === 'wxpay_required') {
      const wxpay = createResult?.wxpay || {}
      if (!wxpay?.timeStamp || !wxpay?.nonceStr || !wxpay?.package || !wxpay?.signType || !wxpay?.paySign) {
        throw new Error('微信支付参数异常，请联系客服')
      }
      await invokeWxpayAndConfirm(createResult)
      handlePaymentSuccess()
      return
    }

    // 模拟支付流程（开发测试用）
    if (action === 'mock_paid') {
      handlePaymentSuccess()
      return
    }

    // 未知支付方式
    throw new Error('支付方式异常')
  } catch (err) {
    const errMsg = String(err?.errMsg || err?.message || '').toLowerCase()
    if (errMsg.includes('cancel')) {
      const orderNo = String(err?.order_no || '').trim()
      if (orderNo) {
        try {
          const status = await getWalletRechargeStatus(orderNo)
          if (Boolean(status?.paid)) {
            handlePaymentSuccess()
            return
          }
        } catch {
          // noop
        }
      }
      uni.showToast({
        title: '已取消支付',
        icon: 'none'
      })
    } else {
      uni.showToast({
        title: err?.message || '充值失败，请稍后重试',
        icon: 'none'
      })
    }
  } finally {
    submitting.value = false
    uni.hideLoading()
  }
}

onLoad(() => {
  const amountFromStorage = Number(uni.getStorageSync('__wallet_recharge_amount__') || 0)
  if (Number.isFinite(amountFromStorage) && amountFromStorage > 0) {
    selectedPreset.value = 0
    customText.value = amountFromStorage.toFixed(2)
    uni.removeStorageSync('__wallet_recharge_amount__')
  }
})
</script>

<style scoped>
.recharge-page {
  min-height: 100vh;
  height: 100vh;
  background: #fafafa;
}

.recharge-scroll {
  height: 100%;
}

.page-content {
  padding: 24rpx 32rpx calc(140rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 32rpx;
}

.section {
  background: #ffffff;
}

.section-title {
  display: block;
  color: #111827;
  font-size: 28rpx;
  font-weight: 600;
  margin-bottom: 20rpx;
}

.amount-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 16rpx;
}

.amount-item {
  position: relative;
  height: 96rpx;
  border: 2rpx solid #e5e7eb;
  border-radius: 8rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 2rpx;
  background: #ffffff;
  text-align: center;
}

.amount-item-active {
  border-color: #2563eb;
  background: #eff6ff;
}

.amount-yuan {
  color: #6b7280;
  font-size: 24rpx;
  line-height: 1;
}

.amount-item-active .amount-yuan {
  color: #2563eb;
}

.amount-value {
  color: #111827;
  font-size: 36rpx;
  font-weight: 600;
  line-height: 1;
}

.amount-item-active .amount-value {
  color: #2563eb;
}

.custom-input-wrap {
  height: 96rpx;
  border: 2rpx solid #e5e7eb;
  border-radius: 8rpx;
  background: #ffffff;
  padding: 0 24rpx;
  display: flex;
  align-items: center;
}

.custom-input-wrap-active {
  border-color: #2563eb;
  background: #eff6ff;
}

.custom-yuan {
  color: #111827;
  font-size: 32rpx;
  font-weight: 600;
}

.custom-input {
  flex: 1;
  margin-left: 8rpx;
  color: #111827;
  font-size: 32rpx;
  font-weight: 600;
}

.tip-text {
  display: block;
  margin-top: 12rpx;
  color: #9ca3af;
  font-size: 24rpx;
  font-weight: 400;
}

.pay-summary {
  padding: 24rpx;
  border-radius: 12rpx;
  background: #f9fafb;
  border: 2rpx solid #e5e7eb;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.summary-label {
  color: #6b7280;
  font-size: 28rpx;
  font-weight: 400;
}

.summary-value-wrap {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.summary-icon {
  width: 32rpx;
  height: 32rpx;
}

.summary-value {
  color: #111827;
  font-size: 28rpx;
  font-weight: 500;
}

.summary-amount {
  color: #111827;
  font-size: 40rpx;
  font-weight: 600;
}

.safe-tip {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  padding: 16rpx;
}

.safe-icon {
  width: 28rpx;
  height: 28rpx;
  opacity: 0.6;
}

.safe-text {
  color: #6b7280;
  font-size: 24rpx;
  font-weight: 400;
}

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 16rpx 32rpx calc(16rpx + env(safe-area-inset-bottom));
  background: #ffffff;
  border-top: 2rpx solid #e5e7eb;
}

.submit-btn {
  height: 96rpx;
  border: 0;
  border-radius: 12rpx;
  background: #2563eb;
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.submit-btn::after {
  border: 0;
}

.submit-btn-disabled {
  opacity: 0.5;
  background: #9ca3af;
}

@media (prefers-color-scheme: dark) {
  .recharge-page {
    background: #000000;
  }

  .section {
    background: #111827;
  }

  .section-title {
    color: #f9fafb;
  }

  .amount-item {
    border-color: #374151;
    background: #1f2937;
  }

  .amount-item-active {
    border-color: #3b82f6;
    background: rgba(59, 130, 246, 0.15);
  }

  .amount-yuan {
    color: #9ca3af;
  }

  .amount-item-active .amount-yuan {
    color: #60a5fa;
  }

  .amount-value {
    color: #f9fafb;
  }

  .amount-item-active .amount-value {
    color: #60a5fa;
  }

  .custom-input-wrap {
    border-color: #374151;
    background: #1f2937;
  }

  .custom-input-wrap-active {
    border-color: #3b82f6;
    background: rgba(59, 130, 246, 0.15);
  }

  .custom-yuan {
    color: #f9fafb;
  }

  .custom-input {
    color: #f9fafb;
  }

  .tip-text {
    color: #6b7280;
  }

  .pay-summary {
    background: #1f2937;
    border-color: #374151;
  }

  .summary-label {
    color: #9ca3af;
  }

  .summary-value {
    color: #f9fafb;
  }

  .summary-amount {
    color: #f9fafb;
  }

  .safe-text {
    color: #9ca3af;
  }

  .bottom-bar {
    background: #111827;
    border-top-color: #374151;
  }

  .submit-btn-disabled {
    background: #374151;
  }
}
</style>
