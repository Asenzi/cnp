<template>
  <view class="member-page">
    <scroll-view class="page-scroll" scroll-y :show-scrollbar="false">
      <view class="page-content">
        <MemberStatusCard :status="memberStatus" />

        <!-- 积分功能暂时隐藏 -->
        <!-- <view class="points-summary-card">
          <view class="points-summary-main">
            <text class="points-summary-label">当前可用积分</text>
            <text class="points-summary-value">{{ availablePointsText }}</text>
            <text class="points-summary-desc">积分仅用于会员开通抵扣，不支持提现、转赠或兑换现金。</text>
          </view>
          <view class="points-summary-side">
            <text class="points-summary-side-label">冻结积分</text>
            <text class="points-summary-side-value">{{ frozenPointsText }}</text>
          </view>
        </view> -->

        <view class="section">
          <text class="section-title">会员专属权益</text>
          <MemberBenefitGrid :items="benefits" />
        </view>

        <view class="section">
          <text class="section-title section-title-plan">选择订阅方案</text>

          <!-- 积分功能暂时隐藏 -->
          <!-- <view v-if="selectedPlanOffer" class="points-offer-card">
            <view class="points-offer-copy">
              <text class="points-offer-title">{{ pointsOfferTitle }}</text>
              <text class="points-offer-desc">{{ pointsOfferDescription }}</text>
              <text class="points-offer-price">实付 ¥{{ payableAmountText }}</text>
            </view>

            <view class="points-offer-action">
              <switch
                v-if="selectedPlanOffer.enabled && selectedPlanOffer.canUse"
                :checked="usePointsDiscount"
                color="#1a57db"
                @change="onTogglePointsDiscount"
              />
              <button
                v-else
                class="points-offer-link"
                hover-class="points-offer-link-active"
                @tap="goPointsCenter"
              >
                去赚积分
              </button>
            </view>
          </view> -->

          <view class="plan-list">
            <MemberPlanCard
              v-for="plan in plans"
              :key="plan.id"
              :plan="plan"
              :selected="selectedPlanId === plan.id"
              @select="onSelectPlan"
            />
          </view>
        </view>

        <view v-if="showContactPackageSection" class="section">
          <view class="section-head">
            <text class="section-title section-title-plan">人群包订阅</text>
          </view>

          <view v-if="contactPackagePlans.length" class="plan-list">
            <MemberPlanCard
              v-for="plan in contactPackagePlans"
              :key="plan.id"
              :plan="plan"
              :selected="selectedPlanId === plan.id"
              @select="onSelectPlan"
            />
          </view>
        </view>

        <view class="notice-wrap">
          <text class="notice-text">订阅即表示您同意《会员服务协议》和《隐私政策》。</text>
          <!-- 积分功能暂时隐藏：规则提示 -->
        </view>
      </view>
    </scroll-view>

    <view class="bottom-bar">
      <button
        class="open-btn"
        :class="{ 'open-btn-disabled': isSubmitting || isLoading || !selectedPlan }"
        :disabled="isSubmitting || isLoading || !selectedPlan"
        hover-class="open-btn-active"
        @tap="onTapOpenSelectedPlan"
      >
        <view class="open-btn-content">
          <text>{{ displaySubmitButtonTextSafe }}</text>
        </view>
      </button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import {
  confirmMemberOrderPayment,
  getMemberCenterOverview,
  getMemberOrderStatus,
  subscribeMemberPlan
} from '../../../api/payment'
import { getCurrentUserProfile } from '../../../api/user'
import MemberBenefitGrid from './components/MemberBenefitGrid.vue'
import MemberPlanCard from './components/MemberPlanCard.vue'
import MemberStatusCard from './components/MemberStatusCard.vue'
import { DEFAULT_BENEFITS, DEFAULT_PLANS, resolveMemberStatus } from './modules/member-center-data'

const memberStatus = ref(resolveMemberStatus({}))
const benefits = ref([...DEFAULT_BENEFITS])
const plans = ref([])
const contactPackagePlans = ref([])
const contactPackageState = ref({
  displayEnabled: false,
  remainingViews: 0,
  usedViews: 0,
  purchasedViews: 0
})
const selectedPlanId = ref('')
const paymentChannel = ref('wallet')
const pointsOverview = ref({
  balance: 0,
  available_balance: 0,
  frozen_balance: 0
})
const usePointsDiscount = ref(false)
const initialPlanId = ref('')
const isLoading = ref(false)
const isSubmitting = ref(false)

const formatAmount = (value) => {
  const amount = Number(value || 0)
  if (!Number.isFinite(amount) || amount <= 0) {
    return '0'
  }
  return Number.isInteger(amount) ? `${amount}` : amount.toFixed(2)
}

const formatCount = (value) => {
  return Number(value || 0).toLocaleString('zh-CN')
}

const normalizeBenefitList = (list) => {
  if (!Array.isArray(list)) {
    return []
  }
  return list
    .map((item, index) => ({
      key: String(item?.key || `benefit_${index + 1}`).trim(),
      title: String(item?.title || '').trim(),
      desc: String(item?.desc || '').trim(),
      iconPath: String(item?.icon_path || item?.iconPath || '').trim(),
      iconText: String(item?.icon_text || item?.iconText || '').trim() || 'V',
      wide: Boolean(item?.wide)
    }))
    .filter((item) => item.key && item.title)
}

const normalizePointsOffer = (offer) => {
  if (!offer || typeof offer !== 'object') {
    return null
  }
  const discountedPrice = Number(offer.discounted_price ?? offer.discountedPrice ?? 0)
  const savedAmount = Number(offer.saved_amount ?? offer.savedAmount ?? 0)
  return {
    enabled: Boolean(offer.enabled),
    requiredPoints: Number(offer.required_points ?? offer.requiredPoints ?? 0),
    discountRate: Number(offer.discount_rate ?? offer.discountRate ?? 1),
    discountText: String(offer.discount_text ?? offer.discountText ?? '').trim(),
    canUse: Boolean(offer.can_use ?? offer.canUse),
    missingPoints: Number(offer.missing_points ?? offer.missingPoints ?? 0),
    discountedPrice: Number.isFinite(discountedPrice) ? discountedPrice : 0,
    savedAmount: Number.isFinite(savedAmount) ? savedAmount : 0,
    savedAmountText: formatAmount(savedAmount)
  }
}

const isYearlyPlan = (plan = {}) => {
  const id = String(plan?.id || '').trim().toLowerCase()
  const name = String(plan?.name || '').trim()
  const durationDays = Number(plan?.duration_days ?? plan?.durationDays ?? 0)
  return id === 'yearly' || name.includes('年度') || durationDays >= 360
}

const normalizePlanList = (list) => {
  const source = Array.isArray(list) && list.length ? list : DEFAULT_PLANS
  const normalized = source
    .map((item, index) => ({
      id: String(item?.id || `plan_${index + 1}`).trim(),
      name: String(item?.name || '').trim(),
      subtitle: String(item?.subtitle || '').trim(),
      price: Number(item?.price || 0),
      originalPrice: Number(item?.original_price ?? item?.originalPrice ?? 0),
      durationDays: Number(item?.duration_days ?? item?.durationDays ?? 0),
      recommended: Boolean(item?.recommended),
      badgeText: String(item?.badge_text || item?.badgeText || '').trim(),
      pointsOffer: normalizePointsOffer(item?.points_offer ?? item?.pointsOffer)
    }))
    .filter((item) => item.id && item.name)
    .filter((item) => isYearlyPlan(item))

  if (normalized.length) {
    return normalized
  }

  return DEFAULT_PLANS
    .map((item, index) => ({
      id: String(item?.id || `plan_${index + 1}`).trim(),
      name: String(item?.name || '').trim(),
      subtitle: String(item?.subtitle || '').trim(),
      price: Number(item?.price || 0),
      originalPrice: Number(item?.original_price ?? item?.originalPrice ?? 0),
      durationDays: Number(item?.duration_days ?? item?.durationDays ?? 0),
      recommended: Boolean(item?.recommended),
      badgeText: String(item?.badge_text || item?.badgeText || '').trim(),
      pointsOffer: normalizePointsOffer(item?.points_offer ?? item?.pointsOffer)
    }))
    .filter((item) => item.id && item.name)
    .filter((item) => isYearlyPlan(item))
}

const normalizeContactPackageList = (list) => {
  if (!Array.isArray(list)) {
    return []
  }
  const normalized = list
    .map((item, index) => ({
      id: String(item?.id || `contact_package_${index + 1}`).trim(),
      name: String(item?.name || '').trim(),
      subtitle: String(item?.subtitle || '').trim(),
      price: Number(item?.price || 0),
      originalPrice: Number(item?.original_price ?? item?.originalPrice ?? 0),
      recommended: Boolean(item?.recommended),
      badgeText: String(item?.badge_text || item?.badgeText || '').trim(),
      productType: String(item?.product_type || item?.productType || 'contact_package').trim(),
      viewCount: Number(item?.view_count ?? item?.viewCount ?? 0)
    }))
    .filter((item) => item.id && item.name)

  if (!normalized.some((item) => item.recommended) && normalized.length) {
    normalized[0].recommended = true
  }
  return normalized
}

const allPurchasablePlans = computed(() => {
  return [...plans.value, ...contactPackagePlans.value]
})

const selectedPlan = computed(() => {
  const all = allPurchasablePlans.value || []
  return all.find((item) => item.id === selectedPlanId.value) || all[0] || null
})

const selectedPlanOffer = computed(() => {
  if (selectedPlan.value?.productType === 'contact_package') {
    return null
  }
  return selectedPlan.value?.pointsOffer || null
})

const selectedProductType = computed(() => {
  return String(selectedPlan.value?.productType || 'member').trim()
})

const showContactPackageSection = computed(() => {
  return Boolean(contactPackagePlans.value.length)
})

const availablePointsText = computed(() => {
  return formatCount(pointsOverview.value?.available_balance || 0)
})

const frozenPointsText = computed(() => {
  return formatCount(pointsOverview.value?.frozen_balance || 0)
})

const effectiveUsePointsDiscount = computed(() => {
  // 积分功能暂时隐藏
  return false
})

const selectedPayableAmount = computed(() => {
  if (effectiveUsePointsDiscount.value) {
    return Number(selectedPlanOffer.value?.discountedPrice || 0)
  }
  return Number(selectedPlan.value?.price || 0)
})

const payableAmountText = computed(() => {
  return formatAmount(selectedPayableAmount.value)
})

const effectiveOpenButtonText = computed(() => {
  if (selectedProductType.value === 'contact_package') {
    return '立即购买人群包'
  }
  return memberStatus.value?.opened ? '立即续费会员' : '立即开通会员'
})

const pointsOfferTitle = computed(() => {
  const offer = selectedPlanOffer.value
  if (!offer?.enabled) {
    return '当前套餐暂不支持积分抵扣'
  }
  return `${offer.requiredPoints}积分可享${offer.discountText}`
})

const pointsOfferDescription = computed(() => {
  const offer = selectedPlanOffer.value
  if (!offer?.enabled) {
    return '该套餐当前仅支持原价开通。'
  }
  if (offer.canUse) {
    return `启用后立减 ¥${offer.savedAmountText}，仅消耗积分，不影响其他会员权益。`
  }
  return `当前可用积分 ${availablePointsText.value}，还差 ${offer.missingPoints} 积分可使用该抵扣。`
})

const openButtonText = computed(() => {
  return memberStatus.value?.opened ? '立即续费会员' : '立即开通会员'
})

const submitButtonText = computed(() => {
  if (isSubmitting.value) {
    return '处理中...'
  }
  if (isLoading.value) {
    return '加载中...'
  }
  return `${openButtonText.value} ¥${payableAmountText.value}`
})
const displaySubmitButtonText = computed(() => {
  if (isSubmitting.value) {
    return '处理中...'
  }
  if (isLoading.value) {
    return '加载中...'
  }
  return `${effectiveOpenButtonText.value} ￥${payableAmountText.value}`
})

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const displaySubmitButtonTextSafe = computed(() => {
  if (isSubmitting.value) {
    return '处理中...'
  }
  if (isLoading.value) {
    return '加载中...'
  }
  return `${effectiveOpenButtonText.value} ${payableAmountText.value}元`
})

const syncSelectedPlan = () => {
  const allPlans = allPurchasablePlans.value
  if (!allPlans.length) {
    selectedPlanId.value = ''
    return
  }
  if (selectedPlanId.value && allPlans.some((item) => item.id === selectedPlanId.value)) {
    return
  }
  if (initialPlanId.value && allPlans.some((item) => item.id === initialPlanId.value)) {
    selectedPlanId.value = initialPlanId.value
    initialPlanId.value = ''
    return
  }
  const recommended = allPlans.find((item) => item.recommended)
  selectedPlanId.value = String(recommended?.id || allPlans[0].id)
}

const syncPointsToggle = () => {
  const offer = selectedPlanOffer.value
  if (!offer?.enabled || !offer.canUse) {
    usePointsDiscount.value = false
  }
}

const loadConfig = () => {
  const configuredPlans = uni.getStorageSync('member_plan_config')
  const configuredBenefits = uni.getStorageSync('member_benefit_config')
  plans.value = normalizePlanList(configuredPlans)
  benefits.value = Array.isArray(configuredBenefits) && configuredBenefits.length
    ? normalizeBenefitList(configuredBenefits)
    : [...DEFAULT_BENEFITS]
  syncSelectedPlan()
  syncPointsToggle()
}

const loadUserProfile = async () => {
  const token = String(uni.getStorageSync('token') || '').trim()
  if (!token) {
    memberStatus.value = resolveMemberStatus({})
    return
  }
  try {
    const profile = await getCurrentUserProfile()
    memberStatus.value = resolveMemberStatus(profile || {})
    uni.setStorageSync('userInfo', profile || {})
  } catch {
    memberStatus.value = resolveMemberStatus({})
  }
}

const loadMemberCenterOverview = async () => {
  const token = String(uni.getStorageSync('token') || '').trim()
  if (!token) {
    return
  }

  isLoading.value = true
  try {
    const overview = await getMemberCenterOverview()
    const serverPlans = normalizePlanList(overview?.plans)
    if (serverPlans.length) {
      plans.value = serverPlans
    }
    contactPackagePlans.value = normalizeContactPackageList(overview?.contact_package?.plans)

    const serverBenefits = normalizeBenefitList(overview?.benefits)
    if (serverBenefits.length) {
      benefits.value = serverBenefits
    }

    const status = overview?.status || {}
    const opened = Boolean(status?.opened)
    memberStatus.value = {
      opened,
      statusText: String(status?.status_text || (opened ? '已开通' : '未开通')),
      expireDateText: String(status?.expire_date_text || '--')
    }

    pointsOverview.value = {
      balance: Number(overview?.points?.balance || 0),
      available_balance: Number(overview?.points?.available_balance || 0),
      frozen_balance: Number(overview?.points?.frozen_balance || 0)
    }
    contactPackageState.value = {
      displayEnabled: Boolean(overview?.contact_package?.display_enabled),
      remainingViews: Number(overview?.contact_package?.remaining_views || 0),
      usedViews: Number(overview?.contact_package?.used_views || 0),
      purchasedViews: Number(overview?.contact_package?.purchased_views || 0)
    }
    paymentChannel.value = String(overview?.payment?.default_channel || 'wallet').trim() || 'wallet'
    syncSelectedPlan()
    syncPointsToggle()
  } catch (err) {
    showToast(err?.message || '会员信息加载失败')
  } finally {
    isLoading.value = false
  }
}

const onSelectPlan = (plan) => {
  const id = String(plan?.id || '').trim()
  if (!id) {
    return
  }
  selectedPlanId.value = id
  syncPointsToggle()
}

const onTogglePointsDiscount = (event) => {
  // 积分功能暂时隐藏
  usePointsDiscount.value = false
  return
  const checked = Boolean(event?.detail?.value)
  const offer = selectedPlanOffer.value
  if (checked && !(offer?.enabled && offer?.canUse)) {
    usePointsDiscount.value = false
    showToast('当前套餐积分不足，暂不能使用抵扣')
    return
  }
  usePointsDiscount.value = checked
}

const goPointsCenter = () => {
  // 积分功能暂时隐藏
}

const invokeWxpayAndConfirm = async (subscribeResult) => {
  const orderNo = String(subscribeResult?.order_no || '').trim()
  const wxpay = subscribeResult?.wxpay || {}
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
    await confirmMemberOrderPayment(orderNo, {
      transaction_id: String(payRes?.transactionId || payRes?.transaction_id || '').trim(),
      ext: payRes
    })
  } catch (err) {
    const status = await getMemberOrderStatus(orderNo)
    if (!Boolean(status?.paid)) {
      throw err
    }
  }
}

const onTapOpenMember = async () => {
  if (isSubmitting.value || isLoading.value) {
    return
  }

  const token = String(uni.getStorageSync('token') || '').trim()
  if (!token) {
    showToast('请先登录')
    return
  }

  if (!selectedPlan.value) {
    showToast('暂无可用订阅方案')
    return
  }

  const wasOpened = Boolean(memberStatus.value?.opened)
  const selected = selectedPlan.value
  const actionText = wasOpened ? '续费' : '开通'
  let pointsText = effectiveUsePointsDiscount.value
    ? `，并消耗 ${selectedPlanOffer.value?.requiredPoints || 0} 积分`
    : ''

  // 积分功能暂时隐藏
  pointsText = ''

  const confirm = await new Promise((resolve) => {
    uni.showModal({
      title: `${actionText}${selected.name}`,
      content: `确认支付 ¥${payableAmountText.value}${pointsText}${actionText}${selected.name}吗？`,
      confirmText: '确认',
      cancelText: '取消',
      success: (res) => resolve(Boolean(res?.confirm)),
      fail: () => resolve(false)
    })
  })

  if (!confirm) {
    return
  }

  isSubmitting.value = true
  uni.showLoading({
    title: '处理中...'
  })

  try {
    const result = await subscribeMemberPlan({
      plan_id: selected.id,
      pay_channel: paymentChannel.value,
      // 积分功能暂时隐藏
      use_points_discount: false
    })

    if (String(result?.action || '').trim() === 'wxpay_required') {
      await invokeWxpayAndConfirm(result)
    }

    await Promise.all([loadUserProfile(), loadMemberCenterOverview()])
    uni.showToast({
      title: `${selected.name}${wasOpened ? '续费' : '开通'}成功`,
      icon: 'success'
    })
  } catch (err) {
    const errMsg = String(err?.errMsg || err?.message || '').toLowerCase()
    if (errMsg.includes('cancel')) {
      const orderNo = String(err?.order_no || '').trim()
      if (orderNo) {
        try {
          const status = await getMemberOrderStatus(orderNo)
          if (Boolean(status?.paid)) {
            await Promise.all([loadUserProfile(), loadMemberCenterOverview()])
            uni.showToast({
              title: `${selected.name}${wasOpened ? '续费' : '开通'}成功`,
              icon: 'success'
            })
            return
          }
        } catch {
          // noop
        }
      }
      showToast('已取消支付')
    } else {
      showToast(err?.message || '开通失败，请稍后重试')
    }
  } finally {
    isSubmitting.value = false
    uni.hideLoading()
  }
}

const onTapOpenSelectedPlan = async () => {
  if (isSubmitting.value || isLoading.value) {
    return
  }

  const token = String(uni.getStorageSync('token') || '').trim()
  if (!token) {
    showToast('请先登录')
    return
  }

  if (!selectedPlan.value) {
    showToast('暂无可用订阅方案')
    return
  }

  const selected = selectedPlan.value
  const isContactPackage = selectedProductType.value === 'contact_package'
  const wasOpened = Boolean(memberStatus.value?.opened)
  const actionText = isContactPackage ? '购买' : (wasOpened ? '续费' : '开通')
  const confirmTitle = isContactPackage ? `购买${selected.name}` : `${actionText}${selected.name}`
  const confirmContent = isContactPackage
    ? `确认支付 ${payableAmountText.value} 元购买 ${selected.name}，获得 ${Number(selected?.viewCount || 0)} 次查看别人联系方式机会吗？`
    : `确认支付 ${payableAmountText.value} 元${actionText}${selected.name}吗？`
  const successText = isContactPackage
    ? `${selected.name}购买成功`
    : `${selected.name}${wasOpened ? '续费' : '开通'}成功`

  const confirm = await new Promise((resolve) => {
    uni.showModal({
      title: confirmTitle,
      content: confirmContent,
      confirmText: '确认',
      cancelText: '取消',
      success: (res) => resolve(Boolean(res?.confirm)),
      fail: () => resolve(false)
    })
  })

  if (!confirm) {
    return
  }

  isSubmitting.value = true
  uni.showLoading({
    title: '处理中...'
  })

  try {
    const result = await subscribeMemberPlan({
      plan_id: selected.id,
      pay_channel: paymentChannel.value,
      use_points_discount: false
    })

    if (String(result?.action || '').trim() === 'wxpay_required') {
      await invokeWxpayAndConfirm(result)
    }

    await Promise.all([loadUserProfile(), loadMemberCenterOverview()])
    uni.showToast({
      title: successText,
      icon: 'success'
    })
  } catch (err) {
    const errMsg = String(err?.errMsg || err?.message || '').toLowerCase()
    if (errMsg.includes('cancel')) {
      const orderNo = String(err?.order_no || '').trim()
      if (orderNo) {
        try {
          const status = await getMemberOrderStatus(orderNo)
          if (Boolean(status?.paid)) {
            await Promise.all([loadUserProfile(), loadMemberCenterOverview()])
            uni.showToast({
              title: successText,
              icon: 'success'
            })
            return
          }
        } catch {
          // noop
        }
      }
      showToast('已取消支付')
      return
    }
    showToast(err?.message || '订阅失败，请稍后重试')
  } finally {
    isSubmitting.value = false
    uni.hideLoading()
  }
}

onLoad((options) => {
  initialPlanId.value = String(options?.planId || options?.plan_id || '').trim()
  loadConfig()
})

onShow(async () => {
  loadConfig()
  await loadUserProfile()
  await loadMemberCenterOverview()
})
</script>

<style scoped>
.member-page {
  height: 100vh;
  background: #f6f6f8;
  --member-body-font: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  --member-heading-font: 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
  --member-block-space: 48rpx;
  --member-card-space: 24rpx;
  font-family: var(--member-body-font);
}

.page-scroll {
  height: 100vh;
}

.page-content {
  padding: 32rpx 32rpx calc(144rpx + env(safe-area-inset-bottom));
}

.points-summary-card {
  margin-top: 18px;
  padding: 18px;
  border-radius: 16px;
  background: linear-gradient(135deg, #1a57db 0%, #2768ec 100%);
  box-shadow: 0 12px 28px rgba(26, 87, 219, 0.18);
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.points-summary-main {
  flex: 1;
}

.points-summary-label {
  display: block;
  color: rgba(255, 255, 255, 0.76);
  font-size: 12px;
  line-height: 18px;
}

.points-summary-value {
  display: block;
  margin-top: 8px;
  color: #ffffff;
  font-size: 32px;
  line-height: 38px;
  font-weight: 800;
}

.points-summary-desc {
  display: block;
  margin-top: 10px;
  color: rgba(255, 255, 255, 0.84);
  font-size: 12px;
  line-height: 18px;
}

.points-summary-side {
  min-width: 86px;
  padding: 10px 12px;
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.16);
  align-self: flex-start;
}

.points-summary-side-label {
  display: block;
  color: rgba(255, 255, 255, 0.74);
  font-size: 11px;
  line-height: 16px;
}

.points-summary-side-value {
  display: block;
  margin-top: 8px;
  color: #ffffff;
  font-size: 18px;
  line-height: 24px;
  font-weight: 700;
}

.section {
  margin-top: var(--member-block-space);
}

.section-title {
  display: block;
  margin-bottom: 24rpx;
  color: #0f172a;
  font-size: 32rpx;
  line-height: 44rpx;
  font-weight: 700;
  letter-spacing: 0.02em;
}

.section-title-plan {
  font-size: 32rpx;
  line-height: 44rpx;
  font-weight: 700;
  letter-spacing: 0.02em;
  font-family: var(--member-heading-font);
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
  margin-bottom: 24rpx;
}

.points-offer-card {
  margin-bottom: 18px;
  padding: 18px;
  border-radius: 16px;
  background: #ffffff;
  border: 1px solid #dbeafe;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 18px;
}

.points-offer-copy {
  flex: 1;
}

.points-offer-title {
  display: block;
  color: #1d4ed8;
  font-size: 16px;
  line-height: 24px;
  font-weight: 700;
}

.points-offer-desc {
  display: block;
  margin-top: 8px;
  color: #64748b;
  font-size: 13px;
  line-height: 20px;
}

.points-offer-price {
  display: block;
  margin-top: 12px;
  color: #0f172a;
  font-size: 18px;
  line-height: 26px;
  font-weight: 700;
  font-family: var(--member-heading-font);
}

.points-offer-action {
  flex-shrink: 0;
}

.points-offer-link {
  min-width: 88px;
  height: 34px;
  line-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  border: 0;
  background: rgba(26, 87, 219, 0.1);
  color: #1a57db;
  font-size: 12px;
  font-weight: 700;
}

.points-offer-link::after {
  border: 0;
}

.points-offer-link-active {
  opacity: 0.9;
}

.plan-list {
  display: flex;
  flex-direction: column;
  gap: var(--member-card-space);
}

.notice-wrap {
  margin-top: 48rpx;
  padding: 24rpx 16rpx 0;
  text-align: center;
}

.notice-text {
  display: block;
  color: #94a3b8;
  font-size: 24rpx;
  line-height: 36rpx;
  letter-spacing: 0.02em;
}

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  padding: 24rpx 32rpx calc(24rpx + env(safe-area-inset-bottom));
  border-top: 1rpx solid #e2e8f0;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(10px);
}

.open-btn {
  width: 100%;
  height: 96rpx;
  line-height: 96rpx;
  border: 0;
  border-radius: 24rpx;
  background: #1a57db;
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 700;
  letter-spacing: 0.02em;
  font-family: var(--member-body-font);
  box-shadow: 0 8rpx 24rpx rgba(26, 87, 219, 0.2);
}

.open-btn::after {
  border: 0;
}

.open-btn-content {
  display: inline-flex;
  align-items: center;
  gap: 16rpx;
}

.open-btn-active {
  opacity: 0.9;
}

.open-btn-disabled {
  opacity: 0.7;
}

@media (prefers-color-scheme: dark) {
  .member-page {
    background: #111621;
  }

  .section-title,
  .points-offer-price,
  .points-offer-card {
    background: #0f172a;
    border-color: #1e3a8a;
  }

  .points-offer-desc,
  .notice-text {
    color: #94a3b8;
  }

  .bottom-bar {
    background: rgba(17, 22, 33, 0.9);
    border-top-color: #1e293b;
  }
}
</style>
