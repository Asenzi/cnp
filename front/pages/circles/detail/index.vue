<template>
  <view class="detail-page">
    <view class="content-wrap">
      <CircleDetailHero :detail="detail" />
      <CircleDetailActions :detail="detail" :interested="isInterested" :disabled="!isOwner && (joinActionDisabled || isJoined)" :action-text="isOwner ? '管理圈子' : isJoined ? '已加入' : joinActionText" @interest="isLoggedIn() ? onToggleInterest() : onInterestBeforeLogin()" @join="isOwner ? onEditCircle() : onApplyJoin()" @owner="onMemberDetail({user_id:detail.owner.userId})"/>


      <CircleContentTabs :tabs="tabs" :active-index="activeTabIndex" @change="onTabChange" />

      <view class="list-wrap">
        <template v-if="activeTabKey === 'resource'">
          <view class="event-list">
            <CircleResourceCard
              v-for="post in posts"
              :key="post.id"
              :post="post"
              @detail="onPostDetail"
            />
          </view>
          <AppEmptyState v-if="!posts.length"><template #title>暂无圈子资源</template></AppEmptyState>
        </template>
        <template v-else-if="activeTabKey === 'member'">
          <view class="member-list">
            <CircleMemberCard
              v-for="member in members"
              :key="member.user_id || member.id"
              :member="member"
              @detail="onMemberDetail"
            />
          </view>
          <AppEmptyState v-if="!members.length"><template #title>暂无圈子成员</template></AppEmptyState>
        </template>
        <AppEmptyState v-else><template #title>{{ activeTabLabel }}模块开发中</template></AppEmptyState>
      </view>
    </view>


  </view>
</template>

<script setup>
import AppEmptyState from '../../../components/AppEmptyState/AppEmptyState.vue'

import { reportActivity } from '../../../utils/activity-notification'
import { computed, ref } from 'vue'
import { onLoad, onShow, onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'
import {
  confirmCircleJoinPayment,
  getCircleDetail,
  getCircleJoinOrderStatus,
  getCircleMembers,
  getCirclePosts,
  submitCircleJoinRequest,
  toggleCircleCollection
} from '../../../api/circle'
import CircleDetailActions from './components/CircleDetailActions.vue'
import CircleContentTabs from './components/CircleContentTabs.vue'
import CircleDetailHero from './components/CircleDetailHero.vue'
import CircleMemberCard from './components/CircleMemberCard.vue'
import CircleResourceCard from './components/CircleResourceCard.vue'
import { circleDetailData, detailTabs } from './modules/detail-data'
import { reportMemberPaymentClientError } from '../../../api/payment'
import { publishCircleInterestChange } from '../../../utils/circle-interest'
import { refreshWechatSessionForPayment } from '../../../utils/payment-session'

const detail = ref(circleDetailData)
const tabs = computed(() => detailTabs.map(tab => ({...tab,label: `${tab.label}（${tab.key === 'member' ? detail.value.memberCount || 0 : detail.value.resourceCount || 0}）`})))
const allPosts = ref([])
const members = ref([])
const circleCode = ref('')
const currentUserId = ref('')
const shouldRefreshOnShow = ref(false)
const joinSubmitting = ref(false)
const interestSubmitting = ref(false)

const activeTabIndex = ref(0)

const posts = computed(() => activeTabKey.value === 'resource' ? allPosts.value : [])

const activeTab = computed(() => tabs.value[activeTabIndex.value] || tabs.value[0] || { key: 'resource', label: '资源' })
const activeTabKey = computed(() => activeTab.value.key)
const activeTabLabel = computed(() => activeTab.value.label)
const isOwner = computed(() => {
  const ownerUserId = String(detail.value?.owner?.userId || '').trim()
  return Boolean(ownerUserId) && ownerUserId === currentUserId.value
})
const isInterested = computed(() => Boolean(detail.value?.isInterested))
const isJoined = computed(() => Boolean(detail.value?.isJoined))
const joinRequestStatus = computed(() => String(detail.value?.joinRequestStatus || '').trim())
const joinPaymentStatus = computed(() => String(detail.value?.joinPaymentStatus || '').trim())
const joinActionText = computed(() => {
  if (joinSubmitting.value) return '处理中...'
  if (joinRequestStatus.value === 'pending' && joinPaymentStatus.value === 'paid') {
    return '等待圈主处理'
  }
  if (joinRequestStatus.value === 'approved') return '已加入'
  if (joinRequestStatus.value === 'rejected') return '重新申请'
  return '申请加入'
})
const joinActionDisabled = computed(() => {
  return joinSubmitting.value
    || joinRequestStatus.value === 'approved'
    || (joinRequestStatus.value === 'pending' && joinPaymentStatus.value === 'paid')
})

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const wait = (delay) => new Promise((resolve) => setTimeout(resolve, delay))

const requestWithGatewayRetry = async (requestFn, maxRetries = 2) => {
  let lastError = null
  for (let attempt = 0; attempt <= maxRetries; attempt += 1) {
    try {
      return await requestFn()
    } catch (error) {
      lastError = error
      const statusCode = Number(error?.statusCode || 0)
      if (![502, 503].includes(statusCode) || attempt >= maxRetries) {
        throw error
      }
      await wait(400 * (attempt + 1))
    }
  }
  throw lastError
}

const isLoggedIn = () => {
  return Boolean(String(uni.getStorageSync('token') || '').trim())
}

const onTabChange = (index) => {
  activeTabIndex.value = index
}


const mapJoinTypeTag = (joinType, joinPrice = 0) => {
  if (joinType === 'paid' && Number(joinPrice || 0) > 0) {
    return '付费圈'
  }
  if (joinType === 'review') {
    return '审核制'
  }
  return '免费圈'
}

const resolveCurrentUserId = () => {
  const userInfo = uni.getStorageSync('userInfo')
  if (!userInfo || typeof userInfo !== 'object') {
    return ''
  }
  return String(userInfo?.user_id || userInfo?.userId || '').trim()
}

const sanitizeCircleImage = (value) => {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return 'https://cos.cnptec.site/static/logo.png'
  }
  if (/^(https?:\/\/tmp\/|wxfile:\/\/|file:\/\/|blob:|data:image\/)/i.test(normalized)) {
    return 'https://cos.cnptec.site/static/logo.png'
  }
  return normalized
}

const resolveShareImageUrl = () => {
  return String(detail.value?.shareImage || '').trim()
}

const applyServerDetail = (serverDetail) => {
  if (!serverDetail || typeof serverDetail !== 'object') {
    return
  }
  const memberCountText = `${serverDetail.member_count || 0} 成员`
  const postCountText = `${serverDetail.post_count || 0} 资源`
  const priceNumber = Number(serverDetail.join_price || 0)

  detail.value = {
    ...detail.value,
    id: serverDetail.circle_code || detail.value.id,
    bannerImage: sanitizeCircleImage(serverDetail.cover_url || detail.value.bannerImage),
    logoImage: sanitizeCircleImage(serverDetail.avatar_url || serverDetail.cover_url || detail.value.logoImage),
    shareImage: String(serverDetail.share_image_url || '').trim(),
    title: serverDetail.name || detail.value.title,
    category: serverDetail.industry_label || serverDetail.category_name || '',
    createdDate: String(serverDetail.created_at || '').slice(0,10),
    memberCount: Number(serverDetail.member_count || 0),
    resourceCount: Number(serverDetail.post_count || 0),
    levelTag: mapJoinTypeTag(serverDetail.join_type, priceNumber),
    membersText: memberCountText,
    postsText: postCountText,
    description: serverDetail.description || detail.value.description,
    owner: {
      ...detail.value.owner,
      userId: serverDetail?.owner?.user_id || detail.value.owner?.userId || '',
      name: serverDetail?.owner?.nickname || detail.value.owner?.name,
      role: '圈主',
      verified: Boolean(serverDetail?.owner?.is_verified),
      intro: `用户ID：${serverDetail?.owner?.user_id || ''}`,
      avatar: serverDetail?.owner?.avatar_url || detail.value.owner?.avatar
    },
    price: {
      current: priceNumber > 0 ? priceNumber.toFixed(2) : '0.00',
      original: detail.value?.price?.original || ''
    },
    isInterested: Boolean(
      serverDetail.is_collected
      ?? serverDetail.collected
      ?? serverDetail.is_interested
      ?? serverDetail.interested
    ),
    collectCount: Number(serverDetail.collect_count ?? serverDetail.favorite_count ?? 0),
    isJoined: Boolean(serverDetail.is_joined),
    joinRequestStatus: String(serverDetail.join_request_status || ''),
    joinPaymentStatus: String(serverDetail.join_payment_status || ''),
    joinAutoApproveAt: serverDetail.join_auto_approve_at || null
  }
}

const loadCircleDetail = async (circleCode) => {
  try {
    const serverDetail = await requestWithGatewayRetry(() => getCircleDetail(circleCode))
    applyServerDetail(serverDetail)
  } catch (err) {
    showToast(err?.message || '圈子详情加载失败')
  }
}

const loadCirclePosts = async (circleCode) => {
  try {
    const payload = await requestWithGatewayRetry(() => getCirclePosts(circleCode, { limit: 50 }))
    allPosts.value = Array.isArray(payload?.items) ? payload.items : []
  } catch (err) {
    allPosts.value = []
    showToast(err?.message || '圈子资源加载失败')
  }
}

const loadCircleMembers = async (circleCode) => {
  try {
    const payload = await requestWithGatewayRetry(() => getCircleMembers(circleCode, { offset: 0, limit: 50 }))
    members.value = Array.isArray(payload?.items) ? payload.items : []
  } catch (err) {
    members.value = []
    showToast(err?.message || '成员列表加载失败')
  }
}

onLoad((options = {}) => {
  circleCode.value = String(options?.code || '').trim()
  currentUserId.value = resolveCurrentUserId()
  if (!circleCode.value) {
    return
  }
  loadCircleDetail(circleCode.value)
  loadCirclePosts(circleCode.value)
  loadCircleMembers(circleCode.value)
})

onShow(() => {
  currentUserId.value = resolveCurrentUserId()

  // 登录后完成进入登录页前发起的收藏操作。
  const pendingCircleCode = uni.getStorageSync('pendingCircleCollectCode')
    || uni.getStorageSync('pendingInterestCircleCode')
  const currentCircleCode = String(circleCode.value || '').trim()

  if (isLoggedIn() && pendingCircleCode && pendingCircleCode === currentCircleCode) {
    performPendingInterest()
  }

  if (!shouldRefreshOnShow.value || !circleCode.value) {
    return
  }
  shouldRefreshOnShow.value = false
  loadCircleDetail(circleCode.value)
  loadCirclePosts(circleCode.value)
  loadCircleMembers(circleCode.value)
})

const performPendingInterest = async () => {
  try {
    const code = String(circleCode.value || '').trim()
    if (!code) {
      uni.removeStorageSync('pendingCircleCollectCode')
      uni.removeStorageSync('pendingInterestCircleCode')
      return
    }

    const result = await toggleCircleCollection(code, true)
    const nextInterested = Boolean(result?.is_collected ?? result?.collected ?? result?.is_interested ?? result?.interested)
    detail.value = {
      ...detail.value,
      isInterested: nextInterested,
      collectCount: Number(result?.collect_count ?? result?.favorite_count ?? detail.value?.collectCount ?? 0)
    }
    publishCircleInterestChange(code, nextInterested)
    showToast('已收藏')
    uni.removeStorageSync('pendingCircleCollectCode')
    uni.removeStorageSync('pendingInterestCircleCode')
  } catch (error) {
    console.error('Pending circle collection failed:', error)
    showToast('收藏失败，请稍后重试')
    uni.removeStorageSync('pendingCircleCollectCode')
    uni.removeStorageSync('pendingInterestCircleCode')
  }
}

onShareAppMessage(() => {
  reportActivity('circle', circleCode.value, 'share')
  const title = String(detail.value?.title || '圈子详情').trim()
  const memberCount = detail.value?.membersText || ''
  const imageUrl = resolveShareImageUrl()

  // 构建分享标题：圈子名称 + 成员数
  let shareTitle = `邀请你加入【${title}】`
  if (memberCount) {
    shareTitle = `邀请你加入【${title}】· ${memberCount}`
  }

  return {
    title: shareTitle,
    path: `/pages/circles/detail/index?code=${encodeURIComponent(circleCode.value)}`,
    imageUrl: imageUrl || undefined
  }
})

onShareTimeline(() => {
  const title = String(detail.value?.title || '圈子详情').trim()
  const memberCount = detail.value?.membersText || ''
  const imageUrl = resolveShareImageUrl()

  // 朋友圈分享标题
  let shareTitle = `邀请你加入【${title}】`
  if (memberCount) {
    shareTitle = `邀请你加入【${title}】· ${memberCount}`
  }

  return {
    title: shareTitle,
    query: `code=${encodeURIComponent(circleCode.value)}`,
    imageUrl: imageUrl || undefined
  }
})

const onPostDetail = (post) => {
  const postCode = String(post?.post_code || post?.postCode || '').trim()
  if (!postCode) {
    showToast('资源编号缺失')
    return
  }
  uni.navigateTo({
    url: `/pages/resources/detail/index?postCode=${encodeURIComponent(postCode)}`
  })
}
const onMemberDetail = (member) => {
  const userId = String(member?.user_id || member?.userId || '').trim()
  if (!userId) {
    showToast('用户信息缺失')
    return
  }
  uni.navigateTo({
    url: `/pages/me/card/index?userId=${encodeURIComponent(userId)}`
  })
}
const onToggleInterest = async () => {
  if (!isLoggedIn()) {
    showToast('\u8bf7\u5148\u767b\u5f55')
    return
  }
  if (interestSubmitting.value) {
    return
  }

  const code = String(circleCode.value || '').trim()
  if (!code) {
    showToast('圈子信息缺失')
    return
  }

  const desired = !isInterested.value
  interestSubmitting.value = true
  try {
    const result = await toggleCircleCollection(code, desired)
    const nextInterested = Boolean(result?.is_collected ?? result?.collected ?? result?.is_interested ?? result?.interested)
    detail.value = {
      ...detail.value,
      isInterested: nextInterested,
      collectCount: Number(result?.collect_count ?? result?.favorite_count ?? detail.value?.collectCount ?? 0)
    }
    publishCircleInterestChange(code, nextInterested)
    showToast(detail.value.isInterested ? '已收藏' : '已取消收藏')
  } catch (err) {
    showToast(err?.message || '操作失败')
  } finally {
    interestSubmitting.value = false
  }
}

const onInterestBeforeLogin = () => {
  const code = String(circleCode.value || '').trim()
  if (!code) {
    showToast('圈子信息缺失')
    return
  }

  uni.setStorageSync('pendingCircleCollectCode', code)

  // 跳转到登录页
  uni.navigateTo({
    url: '/pages/auth/login/index'
  })
}

const getPaymentDebugInfo = (extra = {}) => {
  let systemInfo = {}
  try {
    systemInfo = uni.getSystemInfoSync() || {}
  } catch {
    systemInfo = {}
  }

  return {
    platform: systemInfo.platform,
    system: systemInfo.system,
    brand: systemInfo.brand,
    model: systemInfo.model,
    wechatVersion: systemInfo.version,
    SDKVersion: systemInfo.SDKVersion,
    envVersion: typeof __wxConfig !== 'undefined' ? __wxConfig?.envVersion : '',
    ...extra
  }
}

const getVirtualPaymentErrorMessage = (err, fallback = '支付失败，请稍后重试') => {
  const message = String(err?.errMsg || err?.message || '')
  const code = String(err?.errCode || err?.errno || '')
  const normalized = message.toLowerCase()
  if (code === '-15005' || normalized.includes('signature_invalid')) {
    return '微信登录态已失效，请重新登录后再支付'
  }
  if (code === '-15001' || message.includes('尚未开启iOS支付')) {
    return '当前小程序尚未开启 iOS 支付，请先在微信后台开启苹果 IAP 支付'
  }
  return message || fallback
}

const invokeJoinPayment = async (result) => {
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
      fail: (err) => {
        reportMemberPaymentClientError({
          order_no: orderNo,
          scene: 'circle_join',
          err_msg: err?.errMsg,
          err_code: err?.errCode || err?.errno,
          ext: getPaymentDebugInfo({
            mode: virtualPayment.mode,
            signData: virtualPayment.signData || {}
          })
        }).catch(() => {})
        reject({ ...(err || {}), order_no: orderNo })
      }
    })
  })
  await confirmCircleJoinPayment(orderNo, {
    transaction_id: String(payResult?.transactionId || payResult?.transaction_id || '').trim()
  })
}

const onApplyJoin = async () => {
  if (!isLoggedIn()) {
    showToast('\u8bf7\u5148\u767b\u5f55')
    return
  }
  if (joinSubmitting.value || joinActionDisabled.value) return

  const amount = Number(detail.value?.price?.current || 0)
  const confirmed = await new Promise((resolve) => {
    uni.showModal({
      title: '申请加入圈子',
      content: amount > 0
        ? `需支付入圈费用 ¥${amount.toFixed(2)}。圈主拒绝将退回费用，1个工作日未处理将自动加入。`
        : '提交后圈主可审核，1个工作日未处理将自动加入。',
      confirmText: amount > 0 ? '确认支付' : '提交申请',
      cancelText: '取消',
      success: (res) => resolve(Boolean(res?.confirm)),
      fail: () => resolve(false)
    })
  })
  if (!confirmed) return

  joinSubmitting.value = true
  uni.showLoading({ title: amount > 0 ? '发起支付...' : '提交中...' })
  try {
    if (amount > 0) {
      await refreshWechatSessionForPayment()
    }
    const result = await submitCircleJoinRequest(circleCode.value, {
      pay_channel: amount > 0 ? 'virtualpay' : undefined
    })
    if (String(result?.action || '') === 'virtualpay_required') {
      await invokeJoinPayment(result)
    }
    await loadCircleDetail(circleCode.value)
    uni.showToast({ title: '申请已提交', icon: 'success' })
  } catch (err) {
    const message = String(err?.errMsg || err?.message || '')
    if (message.toLowerCase().includes('cancel')) {
      const orderNo = String(err?.order_no || '').trim()
      if (orderNo) {
        try {
          const status = await getCircleJoinOrderStatus(orderNo)
          if (Boolean(status?.paid)) {
            await loadCircleDetail(circleCode.value)
            uni.showToast({ title: '申请已提交', icon: 'success' })
            return
          }
        } catch {
          // Keep the original cancellation result.
        }
      }
      showToast('已取消支付')
    } else {
      showToast(getVirtualPaymentErrorMessage(err, '申请加入失败'))
    }
  } finally {
    joinSubmitting.value = false
    uni.hideLoading()
  }
}
const onEditCircle = () => {
  if (!circleCode.value) {
    showToast('圈子编号缺失')
    return
  }
  shouldRefreshOnShow.value = true
  uni.navigateTo({
    url: `/pages/circles/edit/index?code=${encodeURIComponent(circleCode.value)}`
  })
}
</script>

<style scoped>.detail-page{min-height:100vh;background:#f5f7ff;padding:0 10rpx 24rpx}.content-wrap{padding:0}.list-wrap{background:#fff;border-radius:0 0 24rpx 24rpx;padding:0 26rpx}.empty-wrap{padding:48rpx 20rpx;text-align:center}.empty-text{font-size:28rpx;color:#777}.owner-action-wrap{padding:16rpx}.owner-edit-btn{font-size:28rpx}</style>
