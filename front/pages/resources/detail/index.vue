<template>
  <view class="detail-page">
    <scroll-view class="detail-scroll" scroll-y :show-scrollbar="false">
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
            <button class="profile-btn" hover-class="profile-btn-active" @tap="onTapProfile">查看主页</button>
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
                    <ProfileSymbol name="visibility" :size="16" color="#94a3b8" />
                    <text class="stat-text">{{ formatNumber(post.view_count) }}</text>
                  </view>
                  <view class="stat-item">
                    <text class="stat-icon-heart">♥</text>
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

          <view class="recommend-wrap">
            <text class="recommend-title">相关资源推荐</text>
            <view class="recommend-card">
              <view class="recommend-icon">AI</view>
              <view class="recommend-main">
                <text class="recommend-name">寻求智能视觉识别方案</text>
                <text class="recommend-from">来自：平台推荐</text>
              </view>
              <text class="recommend-arrow">›</text>
            </view>
          </view>
        </template>
      </view>
    </scroll-view>

    <view class="bottom-nav">
      <button class="bottom-btn bottom-btn-plain" open-type="share" hover-class="bottom-btn-hover" @tap="onShare">
        <image class="btn-icon-image" src="/static/icon/share.png" mode="aspectFit" />
        <text class="btn-label">分享</text>
      </button>
      <button class="bottom-btn bottom-btn-plain" hover-class="bottom-btn-hover" @tap="onChat">
        <image class="btn-icon-image" src="/static/icon/wechat-call.png" mode="aspectFit" />
        <text class="btn-label">联系方式</text>
      </button>
      <button class="bottom-btn bottom-btn-primary" hover-class="bottom-btn-hover" @tap="onConnectNow">
        <image class="btn-icon-image btn-icon-image-primary" src="/static/icon/chat-he.png" mode="aspectFit" />
        <text class="btn-label-primary">联系他</text>
      </button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onPullDownRefresh, onShareAppMessage } from '@dcloudio/uni-app'
import { getResourceDetail, reportResourceView } from '../../../api/post'
import ProfileSymbol from '../../me/card/components/ProfileSymbol.vue'

const postCode = ref('')
const post = ref({})
const loading = ref(false)
const loadError = ref('')

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
const modeText = computed(() => {
  const mode = String(post.value?.mode || '').trim()
  if (mode === 'resource') {
    return '找资源'
  }
  if (mode === 'venue') {
    return '场地发布'
  }
  return '找合作'
})

const sceneTag = computed(() => {
  const mode = String(post.value?.mode || '').trim()
  if (mode === 'resource') {
    return '资源匹配'
  }
  if (mode === 'venue') {
    return '场地对接'
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
  const targetUserId = String(post.value?.author?.user_id || post.value?.author?.userId || '').trim()
  if (!targetUserId) {
    showToast('作者信息缺失')
    return
  }
  uni.navigateTo({
    url: `/pages/me/card/index?userId=${encodeURIComponent(targetUserId)}`
  })
}

const onShare = () => {
  if (typeof uni.showShareMenu === 'function') {
    uni.showShareMenu({
      withShareTicket: false
    })
  }
}

const onChat = () => {
  const targetUserId = String(post.value?.author?.user_id || '').trim()
  if (!targetUserId) {
    showToast('作者信息缺失')
    return
  }
  const name = encodeURIComponent(String(post.value?.author?.nickname || '').trim())
  const avatar = encodeURIComponent(String(post.value?.author?.avatar_url || '').trim())
  uni.navigateTo({
    url: `/pages/messages/chat/index?targetUserId=${encodeURIComponent(targetUserId)}&name=${name}&avatar=${avatar}`
  })
}

const onConnectNow = () => {
  onChat()
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

.detail-main {
  padding: 16rpx 24rpx 32rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.publisher-card {
  background: #ffffff;
  border: 1rpx solid #f1f5f9;
  border-radius: 24rpx;
  padding: 20rpx;
  box-shadow: 0 2rpx 10rpx rgba(15, 23, 42, 0.04);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12rpx;
}

.publisher-left {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.avatar-wrap {
  position: relative;
  width: 96rpx;
  height: 96rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 999rpx;
  background: #e5e7eb;
}

.publisher-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
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
  color: #111827;
  font-size: 30rpx;
  line-height: 40rpx;
  font-weight: 700;
}

.verified-dot {
  width: 14rpx;
  height: 14rpx;
  border-radius: 999rpx;
  background: #3b82f6;
}

.publisher-role {
  color: #6b7280;
  font-size: 26rpx;
  line-height: 36rpx;
}

.profile-btn {
  border: 0;
  background: transparent;
  color: #2563eb;
  font-size: 22rpx;
  line-height: 52rpx;
  font-weight: 600;
  height: 52rpx;
  padding: 0 10rpx;
}

.profile-btn::after {
  border: 0;
}

.profile-btn-active {
  opacity: 0.82;
}

.content-card {
  background: #ffffff;
  border: 1rpx solid #f1f5f9;
  border-radius: 24rpx;
  box-shadow: 0 2rpx 10rpx rgba(15, 23, 42, 0.04);
  overflow: hidden;
}

.content-head {
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.tag-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}

.tag {
  background: #f3f4f6;
  color: #4b5563;
  font-size: 22rpx;
  line-height: 30rpx;
  font-weight: 600;
  border-radius: 6rpx;
  padding: 2rpx 10rpx;
}

.tag-primary {
  background: #eff6ff;
  color: #2563eb;
}

.detail-title {
  color: #111827;
  font-size: 42rpx;
  line-height: 60rpx;
  font-weight: 700;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.detail-line {
  color: #374151;
  font-size: 30rpx;
  line-height: 48rpx;
  white-space: pre-wrap;
}

.gallery {
  padding: 0 24rpx 24rpx;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10rpx;
}

.gallery-image {
  width: 100%;
  border-radius: 12rpx;
  background: #e5e7eb;
}

.gallery-image-main {
  grid-column: span 2;
  height: 384rpx;
}

.gallery-image-sub {
  height: 256rpx;
}

.stats-wrap {
  border-top: 1rpx solid #eef2f7;
  padding: 20rpx 24rpx 24rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
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
  gap: 26rpx;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.stat-icon-clock {
  flex-shrink: 0;
  position: relative;
}

.stat-icon-heart {
  color: #fb7185;
  font-size: 26rpx;
  line-height: 1;
  font-weight: 700;
  transform: translateY(-1rpx);
}

.stat-icon-clock {
  width: 22rpx;
  height: 22rpx;
}

.clock-face {
  position: absolute;
  inset: 0;
  border-radius: 999rpx;
  background: #4f7cff;
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
  color: #6b7280;
  font-size: 26rpx;
  line-height: 36rpx;
}

.publish-time {
  flex-shrink: 0;
  white-space: nowrap;
}

.expire-card {
  border-radius: 18rpx;
  background: linear-gradient(180deg, #f3f8ff 0%, #eef4ff 100%);
  padding: 16rpx 18rpx;
}

.expire-row {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.expire-text {
  color: #4f7cff;
  font-size: 26rpx;
  line-height: 36rpx;
  font-weight: 600;
}

.recommend-wrap {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.recommend-title {
  color: #111827;
  font-size: 26rpx;
  line-height: 36rpx;
  font-weight: 700;
  padding-left: 2rpx;
}

.recommend-card {
  background: #ffffff;
  border: 1rpx solid #f1f5f9;
  border-radius: 16rpx;
  padding: 16rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.recommend-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 10rpx;
  background: #eff6ff;
  color: #2563eb;
  text-align: center;
  font-size: 22rpx;
  line-height: 64rpx;
  font-weight: 700;
}

.recommend-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.recommend-name {
  color: #111827;
  font-size: 26rpx;
  line-height: 38rpx;
  font-weight: 700;
}

.recommend-from {
  color: #9ca3af;
  font-size: 22rpx;
  line-height: 32rpx;
}

.recommend-arrow {
  color: #d1d5db;
  font-size: 34rpx;
  line-height: 34rpx;
}

.status-wrap {
  border-radius: 16rpx;
  border: 1rpx dashed #cbd5e1;
  background: #ffffff;
  min-height: 240rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
}

.status-text {
  color: #64748b;
  font-size: 26rpx;
  line-height: 36rpx;
}

.retry-btn {
  min-width: 180rpx;
  height: 60rpx;
  border: 0;
  border-radius: 999rpx;
  background: #2563eb;
  color: #ffffff;
  font-size: 26rpx;
  line-height: 60rpx;
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
  padding: 12rpx 20rpx calc(12rpx + env(safe-area-inset-bottom));
  background: rgba(255, 255, 255, 0.96);
  border-top: 1rpx solid #e5e7eb;
  border-top-left-radius: 24rpx;
  border-top-right-radius: 24rpx;
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.bottom-btn {
  border: 0;
  border-radius: 12rpx;
  height: 80rpx;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.bottom-btn::after {
  border: 0;
}

.bottom-btn-plain {
  width: 146rpx;
  background: #ffffff;
  color: #4b5563;
}

.bottom-btn-primary {
  flex: 1;
  background: #2563eb;
  color: #ffffff;
}

.bottom-btn-hover {
  opacity: 0.86;
}

.btn-icon {
  width: 20rpx;
  height: 20rpx;
  position: relative;
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

.btn-icon-share {
  border: 2rpx solid #6b7280;
  border-radius: 4rpx;
}

.btn-icon-share::after {
  content: '';
  position: absolute;
  right: -4rpx;
  top: -4rpx;
  width: 8rpx;
  height: 8rpx;
  border-top: 2rpx solid #6b7280;
  border-right: 2rpx solid #6b7280;
}

.btn-icon-chat {
  border: 2rpx solid #6b7280;
  border-radius: 8rpx;
}

.btn-icon-chat::after {
  content: '';
  position: absolute;
  left: 4rpx;
  bottom: -4rpx;
  width: 6rpx;
  height: 6rpx;
  border-left: 2rpx solid #6b7280;
  border-bottom: 2rpx solid #6b7280;
  transform: skewX(-20deg);
}

.btn-label {
  font-size: 22rpx;
  line-height: 30rpx;
  font-weight: 600;
}

.btn-label-primary {
  font-size: 28rpx;
  line-height: 38rpx;
  font-weight: 700;
}
</style>
