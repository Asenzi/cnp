<template>
  <view class="detail-page">
    <scroll-view class="detail-scroll" :class="{ 'detail-scroll-self': isSelfPost }" scroll-y :show-scrollbar="false">
      <view class="detail-main">
        <view v-if="loading && !post.post_code" class="status-wrap">
          <text class="status-text">加载中...</text>
        </view>

        <view v-else-if="loadError && !post.post_code" class="status-wrap">
          <text class="status-text">{{ loadError }}</text>
          <button class="retry-btn" hover-class="retry-btn-active" @tap="fetchDetail">重新加载</button>
        </view>

        <template v-else>
          <view class="publisher-card">
            <view class="publisher-left">
              <view class="avatar-wrap">
                <image class="avatar" :src="authorAvatar" mode="aspectFill" />
              </view>
              <view class="publisher-main">
                <view class="name-row">
                  <text class="publisher-name">{{ authorName }}</text>
                  <view v-if="authorVerified" class="verified-dot"></view>
                </view>
                <text class="publisher-role">{{ authorRole }}</text>
              </view>
            </view>
            <button
              v-if="isSelfPost"
              class="publisher-share-btn"
              hover-class="publisher-share-btn-active"
              open-type="share"
              @tap="onShare"
            >
              <image class="publisher-share-icon" src="/static/icon/share.png" mode="aspectFit" />
            </button>
            <button v-else class="profile-btn" hover-class="profile-btn-active" @tap="onTapProfile">查看主页</button>
          </view>

          <view class="content-card">
            <view class="content-head">
              <view class="tag-row">
                <text class="tag tag-primary">{{ modeText }}</text>
                <text v-if="post.industry_label" class="tag">{{ post.industry_label }}</text>
                <text class="tag">{{ sceneTag }}</text>
              </view>

              <text class="detail-title">{{ post.title || '' }}</text>

              <view class="detail-body">
                <text v-for="(line, index) in descLines" :key="`line-${index}`" class="detail-line">{{ line }}</text>
              </view>
            </view>

            <view v-if="imageList.length" class="gallery">
              <image
                class="gallery-image gallery-image-main"
                mode="aspectFill"
                :src="imageList[0]"
                @tap="previewImage(0)"
              />
              <image
                v-for="(url, index) in subImages"
                :key="`img-${index}`"
                class="gallery-image gallery-image-sub"
                mode="aspectFill"
                :src="url"
                @tap="previewImage(index + 1)"
              />
            </view>

            <view class="stats-wrap">
              <view class="stats-top">
                <view class="stats-left">
                  <view class="stat-item">
                    <image class="stat-icon" src="/static/icon/see.png" mode="aspectFit" />
                    <text class="stat-text">{{ formatNumber(post.view_count) }}</text>
                  </view>
                  <view class="stat-item">
                    <image class="stat-icon" src="/static/icon/like.png" mode="aspectFit" />
                    <text class="stat-text">{{ formatNumber(post.like_count) }}</text>
                  </view>
                </view>
                <text class="publish-time">发布于 {{ publishDateText }}</text>
              </view>

              <view class="expire-card">
                <view class="expire-row">
                  <view class="stat-icon-clock">
                    <view class="clock-face"></view>
                    <view class="clock-hand-hour"></view>
                    <view class="clock-hand-minute"></view>
                  </view>
                  <text class="expire-text">有效期至：{{ expireDateText }} (剩余{{ remainDays }}天)</text>
                </view>
              </view>
            </view>
          </view>

          <!-- 相关资源推荐 - 待后端接口实现 -->
          <!-- <view class="recommend-wrap">
            <text class="recommend-title">相关资源推荐</text>
            <view class="recommend-card">
              <view class="recommend-icon">AI</view>
              <view class="recommend-main">
                <text class="recommend-name">寻求智能视觉识别方案</text>
                <text class="recommend-from">来自：平台推荐</text>
              </view>
              <text class="recommend-arrow">›</text>
            </view>
          </view> -->
        </template>
      </view>
    </scroll-view>

    <view v-if="!isSelfPost" class="bottom-nav">
      <button class="bottom-btn bottom-btn-plain" open-type="share" hover-class="bottom-btn-hover" @tap="onShare">
        <image class="btn-icon-image" src="/static/icon/share.png" mode="aspectFit" />
        <text class="btn-label">分享</text>
      </button>
      <button class="bottom-btn bottom-btn-primary" hover-class="bottom-btn-hover" @tap="onChat">
        <image class="btn-icon-image btn-icon-image-primary" src="/static/icon/chat-he.png" mode="aspectFit" />
        <text class="btn-label-primary">联系方式</text>
      </button>
    </view>

    <view v-if="cardPopupVisible" class="card-popup-mask" @tap="closeCardPopup">
      <view class="card-popup-sheet" @tap.stop>
        <view class="card-popup-handle"></view>
        <view class="card-popup-head">
          <text class="card-popup-title">用户名片</text>
          <text class="card-popup-close" @tap="closeCardPopup">关闭</text>
        </view>

        <view v-if="cardLoading" class="card-loading-wrap">
          <text class="card-loading-text">名片加载中...</text>
        </view>

        <template v-else>
          <view class="business-card">
            <view class="business-card-top">
              <image class="business-card-avatar" :src="cardAvatar" mode="aspectFill" />
              <view class="business-card-main">
                <view class="business-card-name-row">
                  <text class="business-card-name">{{ cardName }}</text>
                  <text v-if="cardVerified" class="business-card-verified">已认证</text>
                </view>
                <text class="business-card-role">{{ cardRole }}</text>
                <text v-if="cardIntro" class="business-card-intro">{{ cardIntro }}</text>
              </view>
            </view>

            <view class="contact-list">
              <view v-if="visibleContactRows.length" class="contact-list-inner">
                <view
                  v-for="row in visibleContactRows"
                  :key="row.key"
                  class="contact-row"
                  hover-class="contact-row-hover"
                  @tap="copyContact(row.value, row.copyText)"
                >
                  <text class="contact-label">{{ row.label }}</text>
                  <text class="contact-value">{{ row.value }}</text>
                  <text class="contact-copy">复制</text>
                </view>
              </view>
              <view v-else class="contact-locked">
                <text class="contact-locked-title">{{ cardLockedTitle }}</text>
                <text class="contact-locked-desc">{{ cardLockedDesc }}</text>
              </view>
            </view>
          </view>

          <view class="card-popup-actions">
            <button class="card-action-btn card-action-secondary" hover-class="card-action-hover" @tap="onTapProfile">
              查看主页
            </button>
            <button class="card-action-btn card-action-primary" hover-class="card-action-hover" @tap="goChatFromCard">
              发消息
            </button>
          </view>
        </template>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onPullDownRefresh, onShareAppMessage } from '@dcloudio/uni-app'
import { getResourceDetail, reportResourceFeedback, reportResourceView } from '../../../api/post'
import { getUserProfileById } from '../../../api/user'

const postCode = ref('')
const post = ref({})
const loading = ref(false)
const loadError = ref('')
const cardPopupVisible = ref(false)
const cardLoading = ref(false)
const cardProfile = ref({})
const cardProfileUserId = ref('')
const cardLoadError = ref('')

const imageList = computed(() => {
  return Array.isArray(post.value?.images)
    ? post.value.images.map((item) => String(item || '').trim()).filter(Boolean)
    : []
})

const subImages = computed(() => imageList.value.slice(1, 3))
const authorName = computed(() => String(post.value?.author?.nickname || '未命名用户').trim())
const authorAvatar = computed(() => String(post.value?.author?.avatar_url || '/static/logo.png').trim() || '/static/logo.png')
const authorRole = computed(() => {
  const companyName = String(post.value?.author?.company_name || '').trim()
  const jobTitle = String(post.value?.author?.job_title || '').trim()
  const fallbackRole = String(post.value?.author?.role || '商务人士').trim()
  const parts = [companyName, jobTitle].filter(Boolean)
  return parts.length ? parts.join(' | ') : fallbackRole
})
const authorVerified = computed(() => Boolean(post.value?.author?.is_verified))
const authorUserId = computed(() => {
  return String(
    post.value?.author?.user_id ||
    post.value?.author?.userId ||
    post.value?.author?.business_user_id ||
    ''
  ).trim()
})
const currentUserId = computed(() => {
  const userInfo = uni.getStorageSync('userInfo') || {}
  return String(userInfo?.user_id || userInfo?.userId || '').trim()
})
const isSelfPost = computed(() => {
  const authorId = authorUserId.value
  const selfId = currentUserId.value
  return Boolean(authorId && selfId && authorId === selfId)
})
const cardSource = computed(() => {
  const profile = cardProfile.value && typeof cardProfile.value === 'object' ? cardProfile.value : {}
  const author = post.value?.author && typeof post.value.author === 'object' ? post.value.author : {}
  return {
    ...author,
    ...profile
  }
})
const cardName = computed(() => String(cardSource.value?.nickname || authorName.value || '未命名用户').trim())
const cardAvatar = computed(() => String(cardSource.value?.avatar_url || authorAvatar.value || '/static/logo.png').trim() || '/static/logo.png')
const cardVerified = computed(() => Boolean(cardSource.value?.is_verified || authorVerified.value))
const cardRole = computed(() => {
  const companyName = String(cardSource.value?.company_name || '').trim()
  const jobTitle = String(cardSource.value?.job_title || '').trim()
  const industry = String(cardSource.value?.industry_label || cardSource.value?.role || '').trim()
  const parts = [companyName, jobTitle].filter(Boolean)
  return parts.length ? parts.join(' | ') : industry || '商务人士'
})
const cardIntro = computed(() => String(cardSource.value?.intro || '').trim())
const visibleContactRows = computed(() => {
  if (!cardSource.value?.contact_visible) {
    return []
  }
  return [
    {
      key: 'wechat',
      label: '微信',
      value: String(cardSource.value?.display_wechat || '').trim(),
      copyText: '微信已复制'
    },
    {
      key: 'phone',
      label: '手机',
      value: String(cardSource.value?.display_phone || '').trim(),
      copyText: '手机号已复制'
    },
    {
      key: 'email',
      label: '邮箱',
      value: String(cardSource.value?.display_email || cardSource.value?.email || '').trim(),
      copyText: '邮箱已复制'
    }
  ].filter((item) => item.value)
})
const cardLockedTitle = computed(() => {
  return String(cardSource.value?.contact_locked_reason || cardLoadError.value || '').trim() || '暂无法查看联系方式'
})
const cardLockedDesc = computed(() => {
  if (cardSource.value?.target_has_contact === false) {
    return '对方暂未公开联系方式'
  }
  if (cardLoadError.value) {
    return '可先查看主页，或稍后重试'
  }
  return '请根据平台权限规则查看完整联系方式'
})
const modeText = computed(() => {
  const mode = String(post.value?.mode || '').trim()
  if (mode === 'resource') {
    return '找资源'
  }
  if (mode === 'venue') {
    return '发布活动'
  }
  return '找合作'
})

const sceneTag = computed(() => {
  const mode = String(post.value?.mode || '').trim()
  if (mode === 'resource') {
    return '资源匹配'
  }
  if (mode === 'venue') {
    return '活动对接'
  }
  return '合作对接'
})

const descLines = computed(() => {
  const raw = String(post.value?.description || '').trim()
  if (!raw) {
    return []
  }
  return raw.split(/\n+/).filter(Boolean)
})

const publishDateText = computed(() => {
  const raw = String(post.value?.created_at || '').trim()
  if (!raw) {
    return '--'
  }
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) {
    return '--'
  }
  const y = date.getFullYear()
  const m = `${date.getMonth() + 1}`.padStart(2, '0')
  const d = `${date.getDate()}`.padStart(2, '0')
  return `${y}-${m}-${d}`
})

const expireDateText = computed(() => {
  const raw = String(post.value?.created_at || '').trim()
  if (!raw) {
    return '--'
  }
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) {
    return '--'
  }
  const expire = new Date(date.getTime() + 180 * 24 * 60 * 60 * 1000)
  const y = expire.getFullYear()
  const m = `${expire.getMonth() + 1}`.padStart(2, '0')
  const d = `${expire.getDate()}`.padStart(2, '0')
  return `${y}-${m}-${d}`
})

const remainDays = computed(() => {
  const raw = String(post.value?.created_at || '').trim()
  if (!raw) {
    return 0
  }
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) {
    return 0
  }
  const expire = new Date(date.getTime() + 180 * 24 * 60 * 60 * 1000)
  const now = new Date()
  const days = Math.ceil((expire.getTime() - now.getTime()) / (24 * 60 * 60 * 1000))
  return Math.max(days, 0)
})

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const reportDetailFeedback = (eventType, ext = {}) => {
  const normalizedCode = String(postCode.value || post.value?.post_code || '').trim()
  const normalizedEvent = String(eventType || '').trim()
  if (!normalizedCode || !normalizedEvent || isSelfPost.value) {
    return
  }
  reportResourceFeedback({
    post_code: normalizedCode,
    event_type: normalizedEvent,
    tab: String(post.value?.mode || 'cooperate').trim() || 'cooperate',
    ext: {
      source: 'resource_detail',
      ...ext
    }
  }).catch(() => {
    // 推荐反馈失败不影响详情页操作。
  })
}

const formatNumber = (value) => {
  const num = Number(value || 0)
  if (!Number.isFinite(num) || num <= 0) {
    return '0'
  }
  if (num >= 10000) {
    return `${(num / 10000).toFixed(1)}w`
  }
  return `${Math.round(num)}`
}

const fetchDetail = async () => {
  if (!postCode.value) {
    loadError.value = '资源编号缺失'
    return
  }

  loading.value = true
  loadError.value = ''
  try {
    const data = await getResourceDetail(postCode.value)
    post.value = data || {}

    const viewData = await reportResourceView(postCode.value)
    if (typeof viewData?.view_count !== 'undefined') {
      post.value = {
        ...post.value,
        view_count: Number(viewData.view_count || post.value.view_count || 0)
      }
    }
  } catch (err) {
    loadError.value = err?.message || '资源详情加载失败'
    showToast(loadError.value)
  } finally {
    loading.value = false
  }
}

const previewImage = (index) => {
  if (!imageList.value.length) {
    return
  }
  uni.previewImage({
    urls: imageList.value,
    current: imageList.value[Math.max(Number(index || 0), 0)] || imageList.value[0]
  })
}

const onTapProfile = () => {
  const targetUserId = authorUserId.value
  if (!targetUserId) {
    showToast('作者信息缺失')
    return
  }
  cardPopupVisible.value = false
  uni.navigateTo({
    url: `/pages/me/card/index?userId=${encodeURIComponent(targetUserId)}`
  })
}

const onShare = () => {
  reportDetailFeedback('share')
  if (typeof uni.showShareMenu === 'function') {
    uni.showShareMenu({
      withShareTicket: false
    })
  }
}

const loadCardProfile = async (targetUserId) => {
  if (!targetUserId || cardProfileUserId.value === targetUserId) {
    return
  }
  cardProfile.value = {}
  cardProfileUserId.value = ''
  cardLoading.value = true
  cardLoadError.value = ''
  try {
    const profile = await getUserProfileById(targetUserId)
    cardProfile.value = profile || {}
    cardProfileUserId.value = targetUserId
  } catch (err) {
    cardLoadError.value = err?.message || '名片加载失败'
  } finally {
    cardLoading.value = false
  }
}

const closeCardPopup = () => {
  cardPopupVisible.value = false
}

const onChat = async () => {
  const targetUserId = authorUserId.value
  if (!targetUserId) {
    showToast('作者信息缺失')
    return
  }
  reportDetailFeedback('contact')
  cardPopupVisible.value = true
  await loadCardProfile(targetUserId)
}

const goChatFromCard = () => {
  const targetUserId = authorUserId.value
  if (!targetUserId) {
    showToast('作者信息缺失')
    return
  }
  reportDetailFeedback('chat_start')
  cardPopupVisible.value = false
  const name = encodeURIComponent(cardName.value)
  const avatar = encodeURIComponent(cardAvatar.value)
  uni.navigateTo({
    url: `/pages/messages/chat/index?targetUserId=${encodeURIComponent(targetUserId)}&name=${name}&avatar=${avatar}`
  })
}

const copyContact = (value, title) => {
  const normalized = String(value || '').trim()
  if (!normalized) {
    return
  }
  uni.setClipboardData({
    data: normalized,
    success: () => {
      showToast(title || '已复制')
    }
  })
}

onShareAppMessage(() => ({
  title: String(post.value?.title || '资源详情').trim(),
  path: `/pages/resources/detail/index?postCode=${encodeURIComponent(postCode.value)}`,
  imageUrl: imageList.value[0] || ''
}))

onLoad((query = {}) => {
  postCode.value = String(query?.postCode || '').trim()
  if (!postCode.value) {
    showToast('资源编号缺失')
    setTimeout(() => {
      uni.navigateBack()
    }, 220)
    return
  }
  fetchDetail()
})

onPullDownRefresh(async () => {
  await fetchDetail()
  uni.stopPullDownRefresh()
})
</script>

<style scoped>
.detail-page {
  height: 100vh;
  overflow: hidden;
  background: #f9fafb;
  color: #111827;
  font-family: 'Public Sans', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.detail-scroll {
  height: calc(100vh - 124rpx - env(safe-area-inset-bottom));
}

.detail-scroll-self {
  height: 100vh;
}

.detail-main {
  padding: 24rpx 32rpx 32rpx;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.publisher-card {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 28rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.publisher-left {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.avatar-wrap {
  position: relative;
  width: 96rpx;
  height: 96rpx;
  border-radius: 48rpx;
  flex-shrink: 0;
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 48rpx;
  background: #f3f6fa;
}

.publisher-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.name-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.publisher-name {
  max-width: 320rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #172033;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.verified-dot {
  width: 12rpx;
  height: 12rpx;
  border-radius: 6rpx;
  background: #2563eb;
}

.publisher-role {
  color: #66758a;
  font-size: 24rpx;
  line-height: 32rpx;
}

.profile-btn {
  border: 0;
  background: #eff6ff;
  color: #2563eb;
  font-size: 24rpx;
  line-height: 56rpx;
  font-weight: 600;
  height: 56rpx;
  padding: 0 20rpx;
  border-radius: 999rpx;
}

.profile-btn::after {
  border: 0;
}

.profile-btn-active {
  opacity: 0.82;
}

.publisher-share-btn {
  width: 72rpx;
  height: 72rpx;
  padding: 0;
  border: 0;
  border-radius: 12rpx;
  background: #f6f8fc;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.publisher-share-btn::after {
  border: 0;
}

.publisher-share-btn-active {
  opacity: 0.82;
}

.publisher-share-icon {
  width: 32rpx;
  height: 32rpx;
  display: block;
}

.content-card {
  background: #ffffff;
  border-radius: 16rpx;
  overflow: hidden;
}

.content-head {
  padding: 32rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 12rpx;
}

.tag {
  background: #f3f6fa;
  color: #66758a;
  font-size: 22rpx;
  line-height: 30rpx;
  font-weight: 600;
  border-radius: 8rpx;
  padding: 4rpx 12rpx;
}

.tag-primary {
  background: #eff6ff;
  color: #2563eb;
}

.detail-title {
  color: #172033;
  font-size: 34rpx;
  line-height: 48rpx;
  font-weight: 600;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.detail-line {
  color: #66758a;
  font-size: 28rpx;
  line-height: 44rpx;
  white-space: pre-wrap;
}

/* 图片画廊 - 标准网格布局 */
.gallery {
  padding: 0 32rpx 32rpx;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 8rpx;
}

.gallery-image {
  width: 100%;
  height: 200rpx;
  border-radius: 8rpx;
  background: #f3f6fa;
}

.gallery-image-main {
  height: 200rpx;
}

.gallery-image-sub {
  height: 200rpx;
}

.stats-wrap {
  border-top: 1rpx solid #f3f6fa;
  padding: 24rpx 32rpx 32rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.stats-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24rpx;
}

.stats-left {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 32rpx;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.stat-icon {
  width: 32rpx;
  height: 32rpx;
  display: block;
  flex-shrink: 0;
}

.stat-icon-clock {
  flex-shrink: 0;
  position: relative;
  width: 22rpx;
  height: 22rpx;
}

.clock-face {
  position: absolute;
  inset: 0;
  border-radius: 999rpx;
  background: #2563eb;
}

.clock-hand-hour,
.clock-hand-minute {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 2rpx;
  background: #ffffff;
  border-radius: 999rpx;
  transform-origin: center bottom;
}

.clock-hand-hour {
  height: 6rpx;
  transform: translate(-50%, -100%);
}

.clock-hand-minute {
  height: 7rpx;
  transform: translate(-50%, -100%) rotate(48deg);
}

.stat-text,
.publish-time {
  color: #66758a;
  font-size: 24rpx;
  line-height: 32rpx;
}

.publish-time {
  flex-shrink: 0;
  white-space: nowrap;
}

.expire-card {
  border-radius: 12rpx;
  background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%);
  padding: 16rpx 18rpx;
}

.expire-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.expire-text {
  color: #2563eb;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 600;
}

.recommend-wrap {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.recommend-title {
  color: #172033;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 600;
  padding-left: 4rpx;
}

.recommend-card {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 24rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.recommend-icon {
  width: 72rpx;
  height: 72rpx;
  border-radius: 12rpx;
  background: #eff6ff;
  color: #2563eb;
  text-align: center;
  font-size: 24rpx;
  line-height: 72rpx;
  font-weight: 700;
}

.recommend-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.recommend-name {
  color: #172033;
  font-size: 26rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.recommend-from {
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

.recommend-arrow {
  color: #cbd5e1;
  font-size: 32rpx;
  line-height: 32rpx;
}

.status-wrap {
  border-radius: 16rpx;
  background: #ffffff;
  min-height: 280rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20rpx;
}

.status-text {
  color: #66758a;
  font-size: 26rpx;
  line-height: 36rpx;
}

.retry-btn {
  min-width: 200rpx;
  height: 72rpx;
  border: 0;
  border-radius: 36rpx;
  background: #2563eb;
  color: #ffffff;
  font-size: 26rpx;
  line-height: 72rpx;
  font-weight: 600;
}

.retry-btn::after {
  border: 0;
}

.retry-btn-active {
  opacity: 0.86;
}

.bottom-nav {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  padding: 16rpx 32rpx calc(16rpx + env(safe-area-inset-bottom));
  background: #ffffff;
  border-top: 1rpx solid #e7ecf3;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.bottom-btn {
  border: 0;
  border-radius: 12rpx;
  height: 72rpx;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.bottom-btn::after {
  border: 0;
}

.bottom-btn-plain {
  min-width: 136rpx;
  padding: 0 20rpx;
  background: #f6f8fc;
  color: #66758a;
}

.bottom-btn-primary {
  flex: 1;
  background: #2563eb;
  color: #ffffff;
}

.bottom-btn-hover {
  opacity: 0.8;
}

.btn-icon-image {
  width: 32rpx;
  height: 32rpx;
  display: block;
  flex: 0 0 auto;
}

.btn-icon-image-primary {
  width: 34rpx;
  height: 34rpx;
}

.btn-label {
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 500;
  white-space: nowrap;
}

.btn-label-primary {
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 600;
  white-space: nowrap;
}

.card-popup-mask {
  position: fixed;
  inset: 0;
  z-index: 40;
  background: rgba(15, 23, 42, 0.42);
  display: flex;
  align-items: flex-end;
  justify-content: center;
}

.card-popup-sheet {
  width: 100%;
  max-width: 750rpx;
  box-sizing: border-box;
  padding: 16rpx 32rpx calc(32rpx + env(safe-area-inset-bottom));
  border-radius: 28rpx 28rpx 0 0;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.card-popup-handle {
  align-self: center;
  width: 72rpx;
  height: 8rpx;
  border-radius: 999rpx;
  background: #d8dee8;
}

.card-popup-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-popup-title {
  color: #172033;
  font-size: 32rpx;
  line-height: 44rpx;
  font-weight: 700;
}

.card-popup-close {
  color: #66758a;
  font-size: 24rpx;
  line-height: 34rpx;
  padding: 8rpx 0 8rpx 24rpx;
}

.card-loading-wrap {
  min-height: 360rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.card-loading-text {
  color: #66758a;
  font-size: 26rpx;
  line-height: 36rpx;
}

.business-card {
  border-radius: 20rpx;
  background: linear-gradient(135deg, #fbfcfe 0%, #eef5ff 100%);
  border: 1rpx solid #e7ecf3;
  padding: 28rpx;
  display: flex;
  flex-direction: column;
  gap: 28rpx;
}

.business-card-top {
  display: flex;
  gap: 20rpx;
  align-items: flex-start;
}

.business-card-avatar {
  width: 112rpx;
  height: 112rpx;
  border-radius: 24rpx;
  flex-shrink: 0;
  background: #f3f6fa;
}

.business-card-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.business-card-name-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
  min-width: 0;
}

.business-card-name {
  color: #172033;
  font-size: 34rpx;
  line-height: 44rpx;
  font-weight: 700;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.business-card-verified {
  flex-shrink: 0;
  border-radius: 999rpx;
  background: rgba(37, 99, 235, 0.1);
  color: #2563eb;
  font-size: 20rpx;
  line-height: 28rpx;
  font-weight: 600;
  padding: 2rpx 10rpx;
}

.business-card-role,
.business-card-intro {
  color: #66758a;
  font-size: 24rpx;
  line-height: 34rpx;
}

.business-card-intro {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.contact-list {
  border-radius: 16rpx;
  background: rgba(255, 255, 255, 0.78);
  overflow: hidden;
}

.contact-row {
  min-height: 72rpx;
  padding: 0 18rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
  border-bottom: 1rpx solid #edf1f6;
}

.contact-row:last-child {
  border-bottom: 0;
}

.contact-row-hover {
  background: rgba(37, 99, 235, 0.06);
}

.contact-label {
  width: 72rpx;
  color: #66758a;
  font-size: 24rpx;
  line-height: 34rpx;
}

.contact-value {
  flex: 1;
  min-width: 0;
  color: #172033;
  font-size: 26rpx;
  line-height: 36rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.contact-copy {
  flex-shrink: 0;
  color: #2563eb;
  font-size: 22rpx;
  line-height: 32rpx;
  font-weight: 600;
}

.contact-locked {
  min-height: 132rpx;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
  text-align: center;
}

.contact-locked-title {
  color: #172033;
  font-size: 26rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.contact-locked-desc {
  color: #66758a;
  font-size: 22rpx;
  line-height: 32rpx;
}

.card-popup-actions {
  display: flex;
  gap: 16rpx;
}

.card-action-btn {
  flex: 1;
  height: 72rpx;
  border: 0;
  border-radius: 12rpx;
  font-size: 26rpx;
  line-height: 72rpx;
  font-weight: 600;
}

.card-action-btn::after {
  border: 0;
}

.card-action-secondary {
  background: #f6f8fc;
  color: #66758a;
}

.card-action-primary {
  background: #2563eb;
  color: #ffffff;
}

.card-action-hover {
  opacity: 0.84;
}

/* 深色模式 */
@media (prefers-color-scheme: dark) {
  .detail-page {
    background: #0a0a0a;
  }

  .publisher-card,
  .content-card,
  .recommend-card,
  .status-wrap {
    background: #1a1a1a;
  }

  .publisher-name,
  .detail-title,
  .recommend-title,
  .recommend-name {
    color: #ffffff;
  }

  .publisher-role,
  .detail-line,
  .stat-text,
  .publish-time,
  .status-text {
    color: #8a8a8a;
  }

  .avatar,
  .gallery-image {
    background: #2a2a2a;
  }

  .profile-btn {
    background: rgba(37, 99, 235, 0.18);
  }

  .publisher-share-btn {
    background: #2a2a2a;
  }

  .tag {
    background: #2a2a2a;
    color: #8a8a8a;
  }

  .stats-wrap {
    border-top-color: #2a2a2a;
  }

  .recommend-from {
    color: #666666;
  }

  .recommend-arrow {
    color: #4a4a4a;
  }

  .bottom-nav {
    background: #1a1a1a;
    border-top-color: #2a2a2a;
  }

  .bottom-btn-plain {
    background: #2a2a2a;
    color: #8a8a8a;
  }

  .card-popup-sheet,
  .business-card,
  .contact-list {
    background: #1a1a1a;
    border-color: #2a2a2a;
  }

  .card-popup-title,
  .business-card-name,
  .contact-value,
  .contact-locked-title {
    color: #ffffff;
  }

  .card-popup-close,
  .card-loading-text,
  .business-card-role,
  .business-card-intro,
  .contact-label,
  .contact-locked-desc {
    color: #8a8a8a;
  }

  .card-popup-handle {
    background: #3a3a3a;
  }

  .contact-row {
    border-bottom-color: #2a2a2a;
  }

  .card-action-secondary {
    background: #2a2a2a;
    color: #8a8a8a;
  }
}

</style>
