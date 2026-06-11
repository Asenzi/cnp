<template>
  <view class="detail-page">
    <view class="content-wrap">
      <CircleDetailHero :detail="detail" />
      <view class="section-gap">
        <CircleNoticeCard :notice="detail.notice" @more="onMoreNotice" />
      </view>
      <CircleOwnerCard :owner="detail.owner" />

      <view v-if="isOwner" class="owner-action-wrap">
        <button class="owner-edit-btn" hover-class="owner-edit-btn-active" @tap="onEditCircle">
          编辑圈子资料
        </button>
      </view>

      <CircleContentTabs :tabs="tabs" :active-index="activeTabIndex" @change="onTabChange" />

      <view class="list-wrap">
        <template v-if="activeTabKey === 'event'">
          <view class="event-list">
            <VenueEventCard
              v-for="post in posts"
              :key="post.id"
              :item="post"
              @detail="onPostDetail"
            />
          </view>
          <view v-if="!posts.length" class="empty-wrap">
            <text class="empty-text">暂无圈子活动</text>
          </view>
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
          <view v-if="!members.length" class="empty-wrap">
            <text class="empty-text">暂无圈子成员</text>
          </view>
        </template>
        <view v-else class="empty-wrap">
          <text class="empty-text">{{ activeTabLabel }}模块开发中</text>
        </view>
      </view>
    </view>

    <CircleBottomBar
      v-if="!isOwner && !isJoined"
      :price="detail.price"
      :interested="isInterested"
      :action-text="joinActionText"
      :disabled="joinActionDisabled"
      @interest="onToggleInterest"
      @apply="onApplyJoin"
    />
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow, onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'
import {
  confirmCircleJoinPayment,
  getCircleDetail,
  getCircleJoinOrderStatus,
  getCircleMembers,
  getCirclePosts,
  submitCircleJoinRequest,
  toggleCircleInterest
} from '../../../api/circle'
import CircleBottomBar from './components/CircleBottomBar.vue'
import CircleContentTabs from './components/CircleContentTabs.vue'
import CircleDetailHero from './components/CircleDetailHero.vue'
import CircleNoticeCard from './components/CircleNoticeCard.vue'
import CircleOwnerCard from './components/CircleOwnerCard.vue'
import CircleMemberCard from './components/CircleMemberCard.vue'
import VenueEventCard from '../../tab/resources/components/VenueEventCard.vue'
import { mapProfilePostItem } from '../../me/card/modules/profile-home-view-model'
import { circleDetailData, detailTabs } from './modules/detail-data'

const detail = ref(circleDetailData)
const tabs = detailTabs
const allPosts = ref([])
const members = ref([])
const circleCode = ref('')
const currentUserId = ref('')
const shouldRefreshOnShow = ref(false)
const joinSubmitting = ref(false)

const activeTabIndex = ref(0)

const posts = computed(() => {
  if (activeTabKey.value === 'event') {
    return allPosts.value
      .filter((post) => {
        const mode = String(post?.mode || '').trim()
        return mode === 'venue'
      })
      .map((post) => mapProfilePostItem(post))
  }
  return []
})

const activeTab = computed(() => tabs[activeTabIndex.value] || tabs[0] || { key: 'event', label: '活动' })
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

const isLoggedIn = () => {
  return Boolean(String(uni.getStorageSync('token') || '').trim())
}

const onTabChange = (index) => {
  activeTabIndex.value = index
}

const formatCountText = (value) => {
  const count = Number(value || 0)
  if (count >= 10000) {
    return `${(count / 10000).toFixed(1)}w`
  }
  return `${Math.max(0, Math.floor(count))}`
}

const mapJoinTypeTag = (joinType) => {
  if (joinType === 'paid') {
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
  return String(detail.value?.logoImage || detail.value?.bannerImage || '').trim()
}

const applyServerDetail = (serverDetail) => {
  if (!serverDetail || typeof serverDetail !== 'object') {
    return
  }
  const memberCountText = `${formatCountText(serverDetail.member_count)} 位成员`
  const postCountText = `${formatCountText(serverDetail.post_count)} 条动态`
  const priceNumber = Number(serverDetail.join_price || 0)

  detail.value = {
    ...detail.value,
    id: serverDetail.circle_code || detail.value.id,
    bannerImage: sanitizeCircleImage(serverDetail.cover_url || detail.value.bannerImage),
    logoImage: sanitizeCircleImage(serverDetail.avatar_url || serverDetail.cover_url || detail.value.logoImage),
    title: serverDetail.name || detail.value.title,
    levelTag: mapJoinTypeTag(serverDetail.join_type),
    membersText: memberCountText,
    postsText: postCountText,
    description: serverDetail.description || detail.value.description,
    notice: String(serverDetail.rules_text || '').trim() || '暂无公告',
    owner: {
      ...detail.value.owner,
      userId: serverDetail?.owner?.user_id || detail.value.owner?.userId || '',
      name: serverDetail?.owner?.nickname || detail.value.owner?.name,
      role: '圈主',
      intro: `用户ID：${serverDetail?.owner?.user_id || ''}`,
      avatar: serverDetail?.owner?.avatar_url || detail.value.owner?.avatar
    },
    price: {
      current: priceNumber > 0 ? priceNumber.toFixed(2) : '0.00',
      original: detail.value?.price?.original || '299'
    },
    isInterested: Boolean(serverDetail.is_interested),
    isJoined: Boolean(serverDetail.is_joined),
    joinRequestStatus: String(serverDetail.join_request_status || ''),
    joinPaymentStatus: String(serverDetail.join_payment_status || ''),
    joinAutoApproveAt: serverDetail.join_auto_approve_at || null
  }
}

const loadCircleDetail = async (circleCode) => {
  try {
    const serverDetail = await getCircleDetail(circleCode)
    applyServerDetail(serverDetail)
  } catch (err) {
    showToast(err?.message || '圈子详情加载失败')
  }
}

const loadCirclePosts = async (circleCode) => {
  try {
    const payload = await getCirclePosts(circleCode, { limit: 50 })
    allPosts.value = Array.isArray(payload?.items) ? payload.items : []
  } catch (err) {
    allPosts.value = []
    showToast(err?.message || '圈子资源加载失败')
  }
}

const loadCircleMembers = async (circleCode) => {
  try {
    const payload = await getCircleMembers(circleCode, { offset: 0, limit: 50 })
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
  if (!shouldRefreshOnShow.value || !circleCode.value) {
    return
  }
  shouldRefreshOnShow.value = false
  loadCircleDetail(circleCode.value)
  loadCirclePosts(circleCode.value)
  loadCircleMembers(circleCode.value)
})

onShareAppMessage(() => {
  const title = String(detail.value?.title || '圈子详情').trim()
  const memberCount = detail.value?.membersText || ''
  // 优先使用封面图（更大更美观），其次使用logo
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

const onMoreNotice = () => showToast('查看公告')
const onPostDetail = (post) => {
  const postCode = String(post?.post_code || post?.postCode || '').trim()
  if (!postCode) {
    showToast('活动编号缺失')
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
  try {
    const result = await toggleCircleInterest(circleCode.value)
    detail.value = {
      ...detail.value,
      isInterested: Boolean(result?.is_interested ?? result?.interested)
    }
    showToast(detail.value.isInterested ? '已标记感兴趣' : '已取消感兴趣')
  } catch (err) {
    showToast(err?.message || '操作失败')
  }
}

const invokeJoinPayment = async (result) => {
  const orderNo = String(result?.order_no || '').trim()
  const wxpay = result?.wxpay || {}
  if (!orderNo || !wxpay.timeStamp || !wxpay.nonceStr || !wxpay.package || !wxpay.signType || !wxpay.paySign) {
    throw new Error('支付参数异常')
  }
  const payResult = await new Promise((resolve, reject) => {
    uni.requestPayment({
      timeStamp: String(wxpay.timeStamp),
      nonceStr: String(wxpay.nonceStr),
      package: String(wxpay.package),
      signType: String(wxpay.signType),
      paySign: String(wxpay.paySign),
      success: (res) => resolve(res || {}),
      fail: (err) => reject({ ...(err || {}), order_no: orderNo })
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
    const result = await submitCircleJoinRequest(circleCode.value, {
      pay_channel: amount > 0 ? 'wxpay' : undefined
    })
    if (String(result?.action || '') === 'wxpay_required') {
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
      showToast(err?.message || '申请加入失败')
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

<style scoped>
.detail-page {
  min-height: 100vh;
  background: #ffffff;
}

.content-wrap {
  padding-bottom: calc(120rpx + env(safe-area-inset-bottom));
}

.section-gap {
  padding: 16rpx 0;
}

.owner-action-wrap {
  padding: 20rpx 32rpx;
  border-bottom: 1rpx solid #f3f4f6;
}

.owner-edit-btn {
  width: 100%;
  height: 80rpx;
  border-radius: 6rpx;
  border: 0;
  background: #2563eb;
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 500;
  display: flex;
  align-items: center;
  justify-content: center;
}

.owner-edit-btn-active {
  opacity: 0.8;
}

.list-wrap {
  background: #ffffff;
}

.event-list {
  padding: 0 32rpx;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.member-list {
  padding: 0 32rpx;
}

.empty-wrap {
  padding: 120rpx 32rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.empty-text {
  color: #9ca3af;
  font-size: 26rpx;
  line-height: 36rpx;
}

@media (prefers-color-scheme: dark) {
  .detail-page {
    background: #111827;
  }

  .owner-action-wrap {
    border-bottom-color: #1f2937;
  }

  .list-wrap {
    background: #111827;
  }

  .empty-text {
    color: #6b7280;
  }
}
</style>
