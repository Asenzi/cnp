<template>
  <view class="detail-page">
    <view class="content-wrap">
      <CircleDetailHero :detail="detail" />
      <CircleOwnerCard :owner="detail.owner" @dm="onPrivateMessage" />
      <view v-if="isOwner" class="owner-action-wrap">
        <button class="owner-edit-btn" hover-class="owner-edit-btn-active" @tap="onEditCircle">
          编辑圈子资料
        </button>
      </view>
      <CircleNoticeCard :notice="detail.notice" @more="onMoreNotice" />

      <CircleContentTabs :tabs="tabs" :active-index="activeTabIndex" @change="onTabChange" />

      <view class="list-wrap">
        <template v-if="activeTabKey === 'resource'">
          <view v-if="isOwner && pendingSyncs.length" class="review-section">
            <view class="review-section-head">
              <text class="review-section-title">待审核同步资源</text>
              <text class="review-section-sub">{{ pendingSyncs.length }} 条待处理</text>
            </view>
            <view v-for="item in pendingSyncs" :key="item.sync_id" class="review-card">
              <text class="review-card-title">{{ item.title }}</text>
              <text class="review-card-meta">{{ item.author?.nickname || '匿名用户' }} · {{ item.author?.company_name || item.author?.job_title || '资源发布者' }}</text>
              <text class="review-card-desc">{{ item.description }}</text>
              <view class="review-card-actions">
                <button class="review-btn review-btn-reject" hover-class="review-btn-reject-active" @tap="onReviewSync(item, 'reject')">
                  拒绝
                </button>
                <button class="review-btn review-btn-approve" hover-class="review-btn-approve-active" @tap="onReviewSync(item, 'approve')">
                  通过
                </button>
              </view>
            </view>
          </view>
          <CircleResourceCard v-for="post in posts" :key="post.post_code || post.id" :post="post" @detail="onPostDetail" />
          <view v-if="!posts.length && !pendingSyncs.length" class="empty-wrap">
            <text class="empty-title">暂无圈子资源</text>
            <text class="empty-sub">资源同步通过后会展示在这里</text>
          </view>
        </template>
        <view v-else class="empty-wrap">
          <text class="empty-title">{{ activeTabLabel }}模块开发中</text>
          <text class="empty-sub">后续会接入真实业务数据</text>
        </view>
      </view>
    </view>

    <CircleBottomBar v-if="!isOwner" :price="detail.price" @apply="onApplyJoin" @join="onJoinNow" />
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { getCircleDetail, getCirclePosts, getPendingCirclePostSyncs, reviewCirclePostSync } from '../../../api/circle'
import CircleBottomBar from './components/CircleBottomBar.vue'
import CircleContentTabs from './components/CircleContentTabs.vue'
import CircleDetailHero from './components/CircleDetailHero.vue'
import CircleNoticeCard from './components/CircleNoticeCard.vue'
import CircleOwnerCard from './components/CircleOwnerCard.vue'
import CircleResourceCard from './components/CircleResourceCard.vue'
import { circleDetailData, detailTabs } from './modules/detail-data'

const detail = ref(circleDetailData)
const tabs = detailTabs
const posts = ref([])
const pendingSyncs = ref([])
const circleCode = ref('')
const currentUserId = ref('')
const shouldRefreshOnShow = ref(false)

const activeTabIndex = ref(0)

const activeTab = computed(() => tabs[activeTabIndex.value] || tabs[0] || { key: 'resource', label: '资源' })
const activeTabKey = computed(() => activeTab.value.key)
const activeTabLabel = computed(() => activeTab.value.label)
const isOwner = computed(() => {
  const ownerUserId = String(detail.value?.owner?.userId || '').trim()
  return Boolean(ownerUserId) && ownerUserId === currentUserId.value
})

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
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
    bannerImage: serverDetail.cover_url || detail.value.bannerImage,
    logoImage: serverDetail.avatar_url || serverDetail.cover_url || detail.value.logoImage,
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
    }
  }
}

const loadCircleDetail = async (circleCode) => {
  try {
    const serverDetail = await getCircleDetail(circleCode)
    applyServerDetail(serverDetail)
    loadPendingSyncs(circleCode)
  } catch (err) {
    showToast(err?.message || '圈子详情加载失败')
  }
}

const loadCirclePosts = async (circleCode) => {
  try {
    const payload = await getCirclePosts(circleCode, { limit: 50 })
    posts.value = Array.isArray(payload?.items) ? payload.items : []
  } catch (err) {
    posts.value = []
    showToast(err?.message || '圈子资源加载失败')
  }
}

const loadPendingSyncs = async (circleCode) => {
  if (!isOwner.value) {
    pendingSyncs.value = []
    return
  }
  try {
    const payload = await getPendingCirclePostSyncs(circleCode)
    pendingSyncs.value = Array.isArray(payload?.items) ? payload.items : []
  } catch {
    pendingSyncs.value = []
  }
}

const loadCircleResourceContext = async (code) => {
  if (!code) {
    return
  }
  await loadCirclePosts(code)
  await loadPendingSyncs(code)
}

onLoad((options = {}) => {
  circleCode.value = String(options?.code || '').trim()
  currentUserId.value = resolveCurrentUserId()
  if (!circleCode.value) {
    return
  }
  loadCircleDetail(circleCode.value)
  loadCircleResourceContext(circleCode.value)
})

onShow(() => {
  currentUserId.value = resolveCurrentUserId()
  if (!shouldRefreshOnShow.value || !circleCode.value) {
    return
  }
  shouldRefreshOnShow.value = false
  loadCircleDetail(circleCode.value)
  loadCircleResourceContext(circleCode.value)
})

const onPrivateMessage = () => showToast('私信功能开发中')
const onMoreNotice = () => showToast('查看公告')
const onPostDetail = (post) => {
  const postCode = String(post?.post_code || '').trim()
  if (!postCode) {
    showToast('资源编号缺失')
    return
  }
  uni.navigateTo({
    url: `/pages/resources/detail/index?postCode=${encodeURIComponent(postCode)}`
  })
}
const onApplyJoin = () => showToast('申请加入已提交')
const onJoinNow = () => showToast('立即加入圈子')
const onReviewSync = async (item, action) => {
  if (!circleCode.value || !item?.sync_id) {
    showToast('同步记录缺失')
    return
  }
  try {
    await reviewCirclePostSync(circleCode.value, item.sync_id, { action })
    showToast(action === 'approve' ? '已通过同步' : '已拒绝同步')
    loadCircleResourceContext(circleCode.value)
    loadCircleDetail(circleCode.value)
  } catch (err) {
    showToast(err?.message || '审核处理失败')
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
  background: #f6f6f8;
}

.content-wrap {
  padding-bottom: calc(150rpx + env(safe-area-inset-bottom));
}

.owner-action-wrap {
  padding: 16rpx 32rpx 0;
}

.owner-edit-btn {
  width: 100%;
  height: 80rpx;
  border-radius: 18rpx;
  border: 0;
  background: linear-gradient(135deg, #1a57db 0%, #2563eb 100%);
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 10rpx 22rpx rgba(26, 87, 219, 0.16);
}

.owner-edit-btn-active {
  opacity: 0.9;
}

.list-wrap {
  padding: 16rpx 32rpx 0;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  background: #f6f6f8;
}

.review-section {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.review-section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.review-section-title {
  color: #0f172a;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 700;
}

.review-section-sub {
  color: #64748b;
  font-size: 22rpx;
  line-height: 32rpx;
}

.review-card {
  padding: 22rpx;
  border-radius: 18rpx;
  background: #ffffff;
  border: 1rpx solid #e2e8f0;
  box-shadow: 0 4rpx 16rpx rgba(15, 23, 42, 0.04);
}

.review-card-title {
  display: block;
  color: #0f172a;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 700;
}

.review-card-meta {
  display: block;
  margin-top: 6rpx;
  color: #64748b;
  font-size: 22rpx;
  line-height: 32rpx;
}

.review-card-desc {
  display: block;
  margin-top: 12rpx;
  color: #475569;
  font-size: 24rpx;
  line-height: 34rpx;
}

.review-card-actions {
  margin-top: 18rpx;
  display: flex;
  justify-content: flex-end;
  gap: 12rpx;
}

.review-btn {
  min-width: 132rpx;
  height: 64rpx;
  border-radius: 14rpx;
  border: 0;
  font-size: 24rpx;
  line-height: 64rpx;
  font-weight: 700;
}

.review-btn::after {
  border: 0;
}

.review-btn-reject {
  background: #f1f5f9;
  color: #475569;
}

.review-btn-approve {
  background: #1a57db;
  color: #ffffff;
}

.review-btn-reject-active,
.review-btn-approve-active {
  opacity: 0.86;
}

.empty-wrap {
  margin-top: 14rpx;
  border-radius: 14rpx;
  border: 1rpx dashed #cbd5e1;
  background: #ffffff;
  min-height: 240rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.empty-title {
  color: #334155;
  font-size: 26rpx;
  line-height: 34rpx;
  font-weight: 600;
}

.empty-sub {
  margin-top: 8rpx;
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

@media (prefers-color-scheme: dark) {
  .detail-page {
    background: #111621;
  }

  .owner-edit-btn {
    box-shadow: none;
  }

  .empty-wrap {
    background: #0f172a;
    border-color: #334155;
  }

  .empty-title {
    color: #cbd5e1;
  }

  .empty-sub {
    color: #64748b;
  }
}
</style>
