<template>
  <view class="page">
    <scroll-view class="page-scroll" scroll-y :show-scrollbar="false">
      <view class="page-content">
        <view v-if="loading" class="loading-state">
          <view class="loading-line loading-line-wide"></view>
          <view class="loading-line"></view>
          <view class="loading-card"></view>
        </view>

        <view v-else-if="loadError" class="error-state">
          <image
            class="error-icon"
            src="https://cos.cnptec.site/static/icon/help.png"
            mode="aspectFit"
          />
          <text class="error-title">页面加载失败</text>
          <text class="error-desc">{{ loadError }}</text>
          <button class="retry-btn" hover-class="button-active" @tap="loadOverview">重新加载</button>
        </view>

        <template v-else>
          <view class="hero" :class="{ 'hero-opened': overview.is_circle_owner }">
            <text class="hero-eyebrow">CIRCLE OWNER</text>
            <text class="hero-title">{{ overview.is_circle_owner ? '您已是圈主' : '成为圈主，建立自己的行业圈层' }}</text>
            <text class="hero-desc">
              {{ overview.is_circle_owner
                ? '圈主身份永久有效，现在可以创建并运营自己的圈子。'
                : '一次付费，无需审核。支付成功后即可创建圈子，长期沉淀成员与行业资源。' }}
            </text>
          </view>

          <view class="section">
            <text class="section-title">圈主专属能力</text>
            <view class="benefit-list">
              <view v-for="item in benefits" :key="item.title" class="benefit-row">
                <view class="benefit-icon-wrap">
                  <image class="benefit-icon" :src="item.icon" mode="aspectFit" />
                </view>
                <view class="benefit-copy">
                  <text class="benefit-title">{{ item.title }}</text>
                  <text class="benefit-desc">{{ item.desc }}</text>
                </view>
              </view>
            </view>
          </view>

          <view v-if="overview.is_circle_owner" class="opened-card">
            <view class="opened-mark">
              <text class="opened-check">✓</text>
            </view>
            <view class="opened-copy">
              <text class="opened-title">圈主能力已解锁</text>
              <text class="opened-desc">身份永久有效，不续费、不失效</text>
            </view>
          </view>

          <template v-else>
            <view class="section">
              <text class="section-title">开通说明</text>
              <view class="purchase-card">
                <view class="purchase-row">
                  <text class="purchase-label">开通方式</text>
                  <text class="purchase-value">一次性购买</text>
                </view>
                <view class="purchase-row purchase-row-last">
                  <text class="purchase-label">有效期限</text>
                  <text class="purchase-value purchase-highlight">永久有效</text>
                </view>
              </view>
            </view>

            <view class="instant-note">
              <image
                class="instant-icon"
                src="https://cos.cnptec.site/static/icon/safe.png"
                mode="aspectFit"
              />
              <text class="instant-text">支付成功即刻生效，无需提交资料或等待人工审核</text>
            </view>
          </template>

          <text class="agreement-note">支付即表示您同意平台付费服务相关规则</text>
        </template>
      </view>
    </scroll-view>

    <view v-if="!loading && !loadError" class="bottom-bar">
      <button
        v-if="overview.is_circle_owner"
        class="primary-btn"
        hover-class="button-active"
        @tap="goCreateCircle"
      >
        创建圈子
      </button>
      <button
        v-else
        class="primary-btn"
        :class="{ 'primary-btn-disabled': submitting || !planEnabled }"
        :disabled="submitting || !planEnabled"
        hover-class="button-active"
        @tap="purchase"
      >
        {{ purchaseButtonText }}
      </button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import {
  confirmMemberOrderPayment,
  getCircleOwnerOverview,
  getMemberOrderStatus,
  purchaseCircleOwner
} from '../../../../api/payment'
import { getCurrentUserProfile } from '../../../../api/user'

const loading = ref(true)
const submitting = ref(false)
const loadError = ref('')
const selectedPaymentChannel = ref('')
const overview = ref({
  is_circle_owner: false,
  lifetime: true,
  wallet_balance: 0,
  member: {
    opened: false,
    plan_id: ''
  },
  plan: {
    price: 0,
    original_price: 0,
    enabled: true
  },
  payment: {
    default_channel: 'wxpay',
    channels: []
  }
})

const benefits = [
  {
    icon: 'https://cos.cnptec.site/static/icon/1.png',
    title: '创建并管理圈子',
    desc: '建立专属行业圈子，自主管理成员与圈子内容'
  },
  {
    icon: 'https://cos.cnptec.site/static/icon/3.png',
    title: '沉淀行业资源',
    desc: '持续聚合同领域伙伴，让资源连接更高效'
  },
  {
    icon: 'https://cos.cnptec.site/static/icon/5.png',
    title: '永久圈主身份',
    desc: '一次开通长期有效，无需续费或重复申请'
  }
]

const formatMoney = (value) => {
  const amount = Number(value || 0)
  if (!Number.isFinite(amount)) return '0'
  return Number.isInteger(amount) ? String(amount) : amount.toFixed(2)
}

const priceText = computed(() => formatMoney(overview.value?.plan?.price))
const originalPriceText = computed(() => formatMoney(overview.value?.plan?.original_price))
const walletBalanceText = computed(() => formatMoney(overview.value?.wallet_balance))
const showOriginalPrice = computed(() => {
  return Number(overview.value?.plan?.original_price || 0) > Number(overview.value?.plan?.price || 0)
})
const planEnabled = computed(() => Boolean(overview.value?.plan?.enabled))
const isYearlyMemberOpened = computed(() => {
  const member = overview.value?.member || {}
  const opened = Boolean(member.opened || member.is_member || member.member_opened)
  const planId = String(member.plan_id || member.member_plan_id || '').trim().toLowerCase()
  return opened && planId === 'yearly'
})
const walletInsufficient = computed(() => {
  return Number(overview.value?.wallet_balance || 0) < Number(overview.value?.plan?.price || 0)
})
const enabledPaymentChannels = computed(() => {
  const channels = Array.isArray(overview.value?.payment?.channels)
    ? overview.value.payment.channels
    : []
  return channels.filter((item) => Boolean(item?.enabled))
})
const selectedPaymentLabel = computed(() => {
  const current = enabledPaymentChannels.value.find(
    (item) => String(item?.key || '') === selectedPaymentChannel.value
  )
  return String(current?.label || '微信支付')
})
const purchaseButtonText = computed(() => {
  if (submitting.value) return '处理中...'
  if (!planEnabled.value) return '暂不可开通'
  if (!isYearlyMemberOpened.value) return '年度会员后开通'
  return `支付 ¥${priceText.value} 永久开通`
})

const showToast = (title) => {
  uni.showToast({ title, icon: 'none' })
}

const syncPaymentChannel = () => {
  const channels = enabledPaymentChannels.value
  if (!channels.length) {
    selectedPaymentChannel.value = ''
    return
  }
  const defaultChannel = String(overview.value?.payment?.default_channel || '').trim()
  const wxpay = channels.find((item) => item.key === 'wxpay')
  const defaultItem = channels.find((item) => item.key === defaultChannel)
  selectedPaymentChannel.value = String(wxpay?.key || defaultItem?.key || channels[0]?.key || '')
}

const loadOverview = async () => {
  loading.value = true
  loadError.value = ''
  try {
    const data = await getCircleOwnerOverview()
    overview.value = data || overview.value
    syncPaymentChannel()
  } catch (err) {
    loadError.value = err?.message || '请检查网络后重试'
  } finally {
    loading.value = false
  }
}

const choosePaymentChannel = () => {
  const channels = enabledPaymentChannels.value
  if (channels.length <= 1) return
  uni.showActionSheet({
    itemList: channels.map((item) => String(item?.label || '支付方式')),
    success: ({ tapIndex }) => {
      selectedPaymentChannel.value = String(channels[tapIndex]?.key || '')
    }
  })
}

const confirmPurchase = () => {
  return new Promise((resolve) => {
    uni.showModal({
      title: '开通永久圈主',
      content: `确认支付 ¥${priceText.value} 开通永久圈主身份吗？支付成功后即可创建圈子。`,
      confirmText: '确认支付',
      cancelText: '取消',
      success: (res) => resolve(Boolean(res?.confirm)),
      fail: () => resolve(false)
    })
  })
}

const invokeWxpayAndConfirm = async (result) => {
  const orderNo = String(result?.order_no || '').trim()
  const virtualPayment = result?.virtual_payment || {}
  if (!orderNo || !virtualPayment?.signData || !virtualPayment?.paySig || !virtualPayment?.signature || !virtualPayment?.mode) {
    throw new Error('小程序虚拟支付参数异常')
  }

  const payResult = await new Promise((resolve, reject) => {
    uni.requestVirtualPayment({
      signData: String(virtualPayment.signDataJson || JSON.stringify(virtualPayment.signData)),
      mode: String(virtualPayment.mode),
      paySig: String(virtualPayment.paySig),
      signature: String(virtualPayment.signature),
      success: (res) => resolve(res || {}),
      fail: (err) => reject({ ...(err || {}), order_no: orderNo })
    })
  })

  await confirmMemberOrderPayment(orderNo, {
    transaction_id: String(payResult?.transactionId || payResult?.transaction_id || '').trim(),
    ext: payResult
  })
}

const syncUserCache = async () => {
  try {
    const profile = await getCurrentUserProfile()
    uni.setStorageSync('userInfo', profile || {})
  } catch {
    const cached = uni.getStorageSync('userInfo') || {}
    uni.setStorageSync('userInfo', { ...cached, is_circle_owner: true })
  }
}

const purchase = async () => {
  if (submitting.value || !planEnabled.value) return
  if (!isYearlyMemberOpened.value) {
    uni.showModal({
      title: '需要年度会员',
      content: '购买圈主身份前需要先开通年度会员，是否现在前往会员中心？',
      confirmText: '去开通',
      cancelText: '取消',
      success: (res) => {
        if (res?.confirm) {
          uni.navigateTo({ url: '/pages/me/member-center/index?planId=yearly' })
        }
      }
    })
    return
  }
  if (!selectedPaymentChannel.value) {
    showToast('暂无可用支付方式')
    return
  }
  if (!(await confirmPurchase())) return

  submitting.value = true
  uni.showLoading({ title: '处理中...' })
  try {
    const result = await purchaseCircleOwner({
      pay_channel: selectedPaymentChannel.value
    })
    if (String(result?.action || '') === 'virtualpay_required') {
      await invokeWxpayAndConfirm(result)
    }
    await syncUserCache()
    await loadOverview()
    uni.showToast({ title: '圈主身份已开通', icon: 'success' })
  } catch (err) {
    const message = String(err?.errMsg || err?.message || '')
    if (message.toLowerCase().includes('cancel')) {
      const orderNo = String(err?.order_no || '').trim()
      if (orderNo) {
        try {
          const status = await getMemberOrderStatus(orderNo)
          if (Boolean(status?.paid)) {
            await syncUserCache()
            await loadOverview()
            uni.showToast({ title: '圈主身份已开通', icon: 'success' })
            return
          }
        } catch {
          // Keep the original cancel result.
        }
      }
      showToast('已取消支付')
    } else {
      showToast(err?.message || '开通失败，请稍后重试')
    }
  } finally {
    submitting.value = false
    uni.hideLoading()
  }
}

const goCreateCircle = () => {
  uni.redirectTo({ url: '/pages/circles/create/index' })
}

onShow(loadOverview)
</script>

<style scoped>
.page {
  height: 100vh;
  background: #f4f6f8;
  color: #0f172a;
  font-family: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
}

.page-scroll {
  height: 100vh;
}

.page-content {
  padding: 24rpx 30rpx calc(164rpx + env(safe-area-inset-bottom));
}

.hero {
  padding: 40rpx;
  border-radius: 28rpx;
  /* background: linear-gradient(145deg, #005d7f 0%, #0786a7 100%) ; */
  color: #111827;
}

.hero-eyebrow {
  display: block;
  color: #111827;
  font-size: 36rpx;
  line-height: 67rpx;
  font-weight: 600;
  letter-spacing: 0.18em;
}

.lifetime-tag {
  padding: 10rpx 20rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.16);
  color: #111827;
  font-size: 22rpx;
  line-height: 30rpx;
}

.hero-title {
  display: block;
  /* margin-top: 14rpx ; */
  max-width: 560rpx;
  color: #111827;
  font-size: 40rpx;
  line-height: 56rpx;
  font-weight: 700;
}

.hero-head,
.price-row,
.purchase-row,
.payment-value,
.benefit-row,
.opened-card,
.instant-note {
  display: flex;
  align-items: center;
}

.hero-head {
  justify-content: space-between;
  margin-bottom: 46rpx;
}

.hero-icon-wrap {
  width: 80rpx;
  height: 80rpx;
  border-radius: 22rpx;
  background: rgba(255, 255, 255, 0.16);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-icon {
  width: 48rpx;
  height: 48rpx;
}

.hero-desc {
  display: block;
  margin-top: 74rpx;
  color: #111827;
  font-size: 25rpx;
  line-height: 40rpx;
}

.price-row {
  margin-top: 38rpx;
  padding-top: 30rpx;
  border-top: 1rpx solid rgba(255, 255, 255, 0.18);
  align-items: flex-end;
}

.price-symbol {
  margin: 0 6rpx 8rpx 0;
  font-size: 30rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.price-value {
  font-size: 64rpx;
  line-height: 66rpx;
  font-weight: 700;
  letter-spacing: -0.04em;
}

.price-meta {
  margin: 0 0 5rpx 20rpx;
  display: flex;
  flex-direction: column;
}

.original-price {
  color: rgba(255, 255, 255, 0.48);
  font-size: 21rpx;
  line-height: 28rpx;
  text-decoration: line-through;
}

.price-note {
  margin-top: 3rpx;
  color: rgba(255, 255, 255, 0.86);
  font-size: 22rpx;
  line-height: 30rpx;
}

.section {
  margin-top: 42rpx;
}

.section-title {
  display: block;
  margin: 0 4rpx 22rpx;
  color: #0f172a;
  font-size: 30rpx;
  line-height: 40rpx;
  font-weight: 600;
}

.benefit-list,
.purchase-card {
  padding: 0 28rpx;
  border-radius: 24rpx;
  background: #ffffff;
}

.benefit-row {
  padding: 28rpx 0;
  border-bottom: 1rpx solid #edf1f5;
}

.benefit-row:last-child {
  border-bottom: 0;
}

.benefit-icon-wrap {
  width: 72rpx;
  height: 72rpx;
  flex-shrink: 0;
  border-radius: 18rpx;
  background: #eaf5f8;
  display: flex;
  align-items: center;
  justify-content: center;
}

.benefit-icon {
  width: 40rpx;
  height: 40rpx;
}

.benefit-copy {
  min-width: 0;
  margin-left: 22rpx;
}

.benefit-title {
  display: block;
  color: #111827;
  font-size: 27rpx;
  line-height: 38rpx;
  font-weight: 600;
}

.benefit-desc {
  display: block;
  margin-top: 4rpx;
  color: #718096;
  font-size: 23rpx;
  line-height: 34rpx;
}

.purchase-row {
  min-height: 92rpx;
  justify-content: space-between;
  border-bottom: 1rpx solid #edf1f5;
}

.purchase-row-last {
  border-bottom: 0;
}

.purchase-label {
  color: #64748b;
  font-size: 25rpx;
}

.purchase-value {
  color: #111827;
  font-size: 25rpx;
  font-weight: 500;
}

.purchase-highlight {
  color: #0676af;
  font-weight: 600;
}

.purchase-arrow {
  margin-left: 12rpx;
  color: #94a3b8;
  font-size: 34rpx;
}

.wallet-note {
  padding: 18rpx 0 24rpx;
  border-top: 1rpx solid #edf1f5;
  display: flex;
  justify-content: space-between;
  gap: 20rpx;
}

.wallet-note-text,
.wallet-note-warn {
  font-size: 21rpx;
  line-height: 30rpx;
}

.wallet-note-text {
  color: #94a3b8;
}

.wallet-note-warn {
  color: #d97706;
  text-align: right;
}

.instant-note {
  margin-top: 24rpx;
  padding: 22rpx 24rpx;
  border-radius: 18rpx;
  background: #e9f4f7;
  align-items: flex-start;
}

.instant-icon {
  width: 32rpx;
  height: 32rpx;
  margin-top: 2rpx;
  flex-shrink: 0;
}

.instant-text {
  margin-left: 14rpx;
  color: #286477;
  font-size: 23rpx;
  line-height: 34rpx;
}

.opened-card {
  margin-top: 28rpx;
  padding: 28rpx;
  border-radius: 22rpx;
  background: #eaf7f4;
}

.opened-mark {
  width: 58rpx;
  height: 58rpx;
  border-radius: 50%;
  background: #158b7e;
  display: flex;
  align-items: center;
  justify-content: center;
}

.opened-check {
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 700;
}

.opened-copy {
  margin-left: 20rpx;
}

.opened-title,
.opened-desc {
  display: block;
}

.opened-title {
  color: #115e59;
  font-size: 27rpx;
  line-height: 38rpx;
  font-weight: 600;
}

.opened-desc {
  margin-top: 3rpx;
  color: #5d817d;
  font-size: 22rpx;
  line-height: 32rpx;
}

.agreement-note {
  display: block;
  margin-top: 34rpx;
  color: #a0aab8;
  font-size: 21rpx;
  line-height: 32rpx;
  text-align: center;
}

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  padding: 20rpx 30rpx calc(20rpx + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.94);
  -webkit-backdrop-filter: blur(12px);
  backdrop-filter: blur(12px);
}

.primary-btn,
.retry-btn {
  border: 0;
  background: #0676af;
  color: #ffffff;
  font-weight: 600;
}

.primary-btn {
  width: 100%;
  height: 92rpx;
  line-height: 92rpx;
  border-radius: 22rpx;
  font-size: 30rpx;
}

.primary-btn::after,
.retry-btn::after {
  border: 0;
}

.primary-btn-disabled {
  opacity: 0.55;
}

.button-active {
  opacity: 0.86;
}

.loading-state,
.error-state {
  padding: 90rpx 30rpx;
}

.loading-line,
.loading-card {
  border-radius: 16rpx;
  background: #e8edf2;
}

.loading-line {
  width: 44%;
  height: 32rpx;
  margin-top: 18rpx;
}

.loading-line-wide {
  width: 72%;
  height: 44rpx;
  margin-top: 0;
}

.loading-card {
  height: 360rpx;
  margin-top: 46rpx;
}

.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.error-icon {
  width: 74rpx;
  height: 74rpx;
}

.error-title {
  margin-top: 22rpx;
  color: #172033;
  font-size: 30rpx;
  font-weight: 600;
}

.error-desc {
  margin-top: 10rpx;
  color: #718096;
  font-size: 24rpx;
  line-height: 36rpx;
}

.retry-btn {
  min-width: 220rpx;
  height: 76rpx;
  line-height: 76rpx;
  margin-top: 30rpx;
  border-radius: 18rpx;
  font-size: 26rpx;
}
</style>
