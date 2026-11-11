<template>
  <view class="page">
    <scroll-view class="page-scroll" scroll-y :show-scrollbar="false">
      <view class="page-content">
        <view class="hero">
          <text class="hero-eyebrow">CITY PARTNER</text>
          <text class="hero-title">成为城市合伙人，共建本地商务网络</text>
          <text class="hero-desc">在你的城市连接企业家与行业伙伴，共同建设商务社交网络，并通过推荐会员获得分佣。</text>
        </view>

        <view class="section">
          <text class="section-title">合伙人专属能力</text>
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

        <view class="section">
          <text class="section-title">开通与分佣</text>
          <view class="purchase-card">
            <view class="purchase-row">
              <text class="purchase-label">城市合伙人开通费</text>
              <text class="purchase-value purchase-highlight">¥10,000</text>
            </view>
            <view class="purchase-row">
              <text class="purchase-label">会员推荐分佣</text>
              <text class="purchase-value purchase-highlight">直接引流 60% · 下属沙龙引流 30%</text>
            </view>
            <view class="purchase-row purchase-row-last">
              <text class="purchase-label">适用人群</text>
              <text class="purchase-value">城市资源组织者</text>
            </view>
          </view>
        </view>

        <view class="commission-card">
          <text class="commission-title">推荐会员，获得持续回报</text>
          <text class="commission-desc">直接邀请用户首次开通会员，城市合伙人获得60%，平台获得40%；所属沙龙主理人引流，城市合伙人获得30%、沙龙主理人获得40%、平台获得30%。首次成交确定归属，后续续费沿用。</text>
          <text v-if="overview.plan.availability_message && !overview.is_partner" class="availability-note">{{ overview.plan.availability_message }}</text>
          <text v-if="overview.plan.availability_message && !overview.is_partner" class="availability-note">{{ overview.plan.availability_message }}</text>
          <button v-if="overview.is_partner && overview.invite_code" class="share-btn" open-type="share">分享我的推荐入口</button>
        </view>

        <view v-if="overview.is_partner" class="opened-card">
          <text class="opened-title">城市合伙人身份已开通</text>
          <text class="opened-desc">推荐码：{{ overview.invite_code }}</text>
        </view>

        <view class="instant-note">
          <image class="instant-icon" src="https://cos.cnptec.site/static/icon/safe.png" mode="aspectFit" />
          <text class="instant-text">合作身份开通与会员分佣以平台确认及订单结算结果为准</text>
        </view>
        <text class="agreement-note">会员分佣按会员实际支付金额计算；推荐关系与结算以平台规则为准。</text>
      </view>
    </scroll-view>

    <view class="bottom-bar">
      <button class="primary-btn" :disabled="submitting || overview.is_partner || hasOtherPartner || !overview.plan.enabled" :class="{ 'primary-btn-disabled': submitting || overview.is_partner || hasOtherPartner || !overview.plan.enabled }" hover-class="button-active" @tap="apply">{{ buttonText }}</button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShareAppMessage, onShow } from '@dcloudio/uni-app'
import { getPartnerOverview } from '../../../../api/payment'
import { openPartnerIdentity } from '../../../../utils/partner-purchase'

const submitting = ref(false)
const overview = ref({
  is_partner: false,
  invite_code: '',
  plan: { price: 10000, commission_rate: 0.3, enabled: false },
  payment: { channels: [] }
})
const commissionPercent = computed(() => Math.round(Number(overview.value?.plan?.commission_rate ?? 0.3) * 100))
const hasOtherPartner = computed(() => Boolean(overview.value.active_partner_type && overview.value.active_partner_type !== 'city_partner'))
const payChannel = computed(() => {
  const channels = Array.isArray(overview.value?.payment?.channels) ? overview.value.payment.channels : []
  return channels.some((item) => item?.key === 'virtualpay' && item?.enabled)
    ? 'virtualpay'
    : channels.some((item) => item?.key === 'mock' && item?.enabled) ? 'mock' : 'virtualpay'
})
const buttonText = computed(() => {
  if (overview.value.is_partner) return '已开通城市合伙人'
  if (hasOtherPartner.value) return '账号已开通其他合作身份'
  if (submitting.value) return '支付处理中...'
  if (!overview.value.plan.enabled) return overview.value.plan.availability_message || '暂未开放支付'
  return `立即开通 · ¥${Number(overview.value.plan.price || 10000).toLocaleString('zh-CN')}`
})

const loadOverview = async () => {
  try {
    overview.value = await getPartnerOverview('city_partner')
  } catch (error) {
    uni.showToast({ title: error?.message || '开通信息加载失败', icon: 'none' })
  }
}

const benefits = [
  { icon: '/static/icon/city-partner.svg', title: '运营城市网络', desc: '在本地组织并连接高质量商务伙伴' },
  { icon: 'https://cos.cnptec.site/static/icon/3.png', title: '拓展城市资源', desc: '聚合企业、机构与行业活动资源' },
  { icon: 'https://cos.cnptec.site/static/icon/1.png', title: '获得平台支持', desc: '获得活动展示与平台运营支持' }
]

const apply = async () => {
  if (submitting.value || overview.value.is_partner || hasOtherPartner.value || !overview.value.plan.enabled) return
  const confirmed = await new Promise((resolve) => {
    uni.showModal({
      title: '开通城市合伙人',
      content: `确认支付 ¥${Number(overview.value.plan.price || 10000).toLocaleString('zh-CN')} 开通吗？推荐会员后可获得会员实付金额的 ${commissionPercent.value}% 分佣。`,
      confirmText: '确认支付',
      success: (result) => resolve(Boolean(result?.confirm)),
      fail: () => resolve(false)
    })
  })
  if (!confirmed) return
  submitting.value = true
  uni.showLoading({ title: '正在创建订单...' })
  try {
    await openPartnerIdentity('city_partner', payChannel.value)
    await loadOverview()
    uni.showToast({ title: '城市合伙人已开通', icon: 'success' })
  } catch (error) {
    uni.showToast({ title: error?.message || '开通失败', icon: 'none' })
  } finally {
    submitting.value = false
    uni.hideLoading()
  }
}

onShow(loadOverview)
onShareAppMessage(() => ({
  title: '加入我推荐的商务会员，连接更多优质人脉',
  path: `/pages/auth/login/index?inviteCode=${encodeURIComponent(String(overview.value.invite_code || ''))}`
}))
</script>

<style scoped>
.page { height: 100vh; background: #f4f6f8; color: #0f172a; font-family: 'PingFang SC', 'Microsoft YaHei', sans-serif; }
.page-scroll { height: 100vh; }
.page-content { padding: 24rpx 30rpx calc(164rpx + env(safe-area-inset-bottom)); }
.hero { padding: 40rpx; }
.hero-eyebrow { display: block; font-size: 36rpx; line-height: 67rpx; font-weight: 600; letter-spacing: .18em; }
.hero-title { display: block; max-width: 600rpx; font-size: 40rpx; line-height: 56rpx; font-weight: 700; }
.hero-desc { display: block; margin-top: 42rpx; font-size: 25rpx; line-height: 40rpx; }
.section { margin-top: 42rpx; }
.section-title { display: block; margin: 0 4rpx 22rpx; font-size: 30rpx; line-height: 40rpx; font-weight: 600; }
.benefit-list, .purchase-card { padding: 0 28rpx; border-radius: 24rpx; background: #fff; }
.benefit-row { display: flex; align-items: center; padding: 28rpx 0; border-bottom: 1rpx solid #edf1f5; }
.benefit-row:last-child { border-bottom: 0; }
.benefit-icon-wrap { width: 72rpx; height: 72rpx; flex-shrink: 0; border-radius: 18rpx; background: #eaf5f8; display: flex; align-items: center; justify-content: center; }
.benefit-icon { width: 44rpx; height: 44rpx; }
.benefit-copy { min-width: 0; margin-left: 22rpx; }
.benefit-title, .benefit-desc { display: block; }
.benefit-title { font-size: 27rpx; line-height: 38rpx; font-weight: 600; }
.benefit-desc { margin-top: 4rpx; color: #718096; font-size: 23rpx; line-height: 34rpx; }
.purchase-row { min-height: 92rpx; display: flex; align-items: center; justify-content: space-between; border-bottom: 1rpx solid #edf1f5; }
.purchase-row-last { border-bottom: 0; }
.purchase-label { color: #64748b; font-size: 25rpx; }
.purchase-value { font-size: 25rpx; font-weight: 500; }
.purchase-highlight { color: #0676af; font-weight: 600; }
.commission-card { margin-top: 24rpx; padding: 28rpx; border-radius: 20rpx; background: #eaf5f8; }
.availability-note { display: block; margin-top: 16rpx; color: #a16207; font-size: 22rpx; line-height: 34rpx; }
.commission-title, .commission-desc { display: block; }
.commission-title { color: #155e75; font-size: 27rpx; line-height: 38rpx; font-weight: 700; }
.commission-desc { margin-top: 12rpx; color: #286477; font-size: 23rpx; line-height: 36rpx; }
.share-btn { margin: 20rpx 0 0; padding: 0 24rpx; height: 64rpx; line-height: 64rpx; border-radius: 16rpx; background: #fff; color: #0676af; font-size: 23rpx; }
.opened-card { display: flex; flex-direction: column; gap: 10rpx; margin-top: 24rpx; padding: 28rpx; border-radius: 20rpx; background: #e8f7ef; }
.opened-title { color: #137547; font-size: 27rpx; font-weight: 700; }
.opened-desc { color: #38785c; font-size: 23rpx; }
.primary-btn-disabled { opacity: .55; }
.instant-note { display: flex; align-items: flex-start; margin-top: 24rpx; padding: 22rpx 24rpx; border-radius: 18rpx; background: #e9f4f7; }
.instant-icon { width: 32rpx; height: 32rpx; flex-shrink: 0; }
.instant-text { margin-left: 14rpx; color: #286477; font-size: 23rpx; line-height: 34rpx; }
.agreement-note { display: block; margin-top: 34rpx; color: #a0aab8; font-size: 21rpx; line-height: 32rpx; text-align: center; }
.bottom-bar { position: fixed; left: 0; right: 0; bottom: 0; z-index: 20; padding: 20rpx 30rpx calc(20rpx + env(safe-area-inset-bottom)); background: rgba(255,255,255,.94); }
.primary-btn { width: 100%; height: 92rpx; line-height: 92rpx; border: 0; border-radius: 22rpx; background: #0676af; color: #fff; font-size: 30rpx; font-weight: 600; }
.primary-btn::after { border: 0; }
.button-active { opacity: .86; }
</style>
