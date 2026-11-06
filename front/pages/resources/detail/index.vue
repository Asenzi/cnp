<template>
  <view class="detail-page">
    <scroll-view class="detail-scroll" :class="{ 'detail-scroll-with-bar': !!post.post_code }" scroll-y :show-scrollbar="false">
      <view class="detail-main">
        <view v-if="loading && !post.post_code" class="status-wrap">
          <text class="status-text">加载中...</text>
        </view>

        <view v-else-if="loadError && !post.post_code" class="status-wrap">
          <text class="status-text">{{ loadError }}</text>
          <button class="retry-btn" hover-class="retry-btn-active" @tap="fetchDetail">重新加载</button>
        </view>

        <template v-else>
          <view class="content-card">
            <view class="content-head">
              <text class="detail-title">{{ post.title || '' }}</text>

              <view v-if="descLines.length" class="detail-body">
                <text v-for="(line, index) in descLines" :key="`line-${index}`" class="detail-line">{{ line }}</text>
              </view>
            </view>

            <view v-if="imageList.length" class="gallery">
              <image class="gallery-image gallery-image-main" mode="aspectFill" :src="imageList[0]"
                @tap="previewImage(0)" />
              <image v-for="(url, index) in subImages" :key="`img-${index}`" class="gallery-image gallery-image-sub"
                mode="aspectFill" :src="url" @tap="previewImage(index + 1)" />
            </view>

            <view class="publisher-row" hover-class="publisher-row-hover" @tap="onTapProfile">
              <view class="publisher-left">
                <view class="avatar-wrap">
                  <image class="avatar" :src="authorAvatar" mode="aspectFill" />
                </view>
                <view class="publisher-main">
                  <view class="name-row">
                    <text class="publisher-name">{{ authorName }}</text>
                    <view v-if="authorBadges.length" class="badge-row">
                      <image
                        v-for="badge in authorBadges"
                        :key="badge.key"
                        class="identity-badge"
                        :src="badge.icon"
                        mode="aspectFit"
                      />
                    </view>
                  </view>
                  <text class="publisher-role">{{ authorRole }}</text>
                </view>
              </view>
              <view class="publisher-chevron"></view>
            </view>

            <view class="publish-meta">
              <image class="publish-clock" src="/static/icon/detail-clock.png" mode="aspectFit" />
              <text class="publish-time">发布于 {{ publishDateText }}</text>
            </view>
          </view>
        </template>
      </view>
    </scroll-view>

    <view v-if="post.post_code" class="bottom-bar">
      <view class="bottom-actions">
        <button class="icon-action" open-type="share" hover-class="icon-action-hover" @tap="onShare">
          <view class="icon-action-inner">
            <image class="icon-action-image" src="/static/icon/detail-share.png" mode="aspectFit" />
            <text class="icon-action-label">分享</text>
          </view>
        </button>
        <button class="icon-action" hover-class="icon-action-hover" @tap="onTapCollect">
          <view class="icon-action-inner">
            <image
              class="icon-action-image"
              :src="isPostInterested ? '/static/icon/detail-bookmark-on.png' : '/static/icon/detail-bookmark.png'"
              mode="aspectFit"
            />
            <text class="icon-action-label" :class="{ 'icon-action-label-active': isPostInterested }">收藏</text>
          </view>
        </button>
      </view>
      <button class="contact-btn" hover-class="contact-btn-hover" @tap="onTapProfile">查看人脉</button>
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
                <view v-for="row in visibleContactRows" :key="row.key" class="contact-row"
                  hover-class="contact-row-hover" @tap="copyContact(row.value, row.copyText)">
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
import { onLoad, onPullDownRefresh, onShareAppMessage, onShow } from '@dcloudio/uni-app'
import { getResourceDetail, reportResourceFeedback, reportResourceView, toggleResourceCollection } from '../../../api/post'
import { getUserProfileById } from '../../../api/user'

const postCode = ref('')
const post = ref({})
const loading = ref(false)
const loadError = ref('')
const isPostInterested = ref(false) // 当前资源是否已收藏，保留变量名兼容旧状态字段。
const cardPopupVisible = ref(false)
const cardLoading = ref(false)
const cardProfile = ref({})
const cardProfileUserId = ref('')
const cardLoadError = ref('')

const ACTIVE_TEXT_VALUES = new Set(['1', 'true', 'yes', 'y', 'active', 'opened', 'member', 'vip', 'paid', 'enabled', 'on', 'approved', 'verified', '已开通', '会员', '已认证', '已实名', '圈主'])
const IDENTITY_BADGE_ICONS = {
  certification: 'https://cos.cnptec.site/static/icon/certification.png',
  member: 'https://cos.cnptec.site/static/icon/mennber1.png',
  leader: 'https://cos.cnptec.site/static/icon/leader.png?v=20260623'
}

const isActiveValue = (value) => {
  if (typeof value === 'boolean') {
    return value
  }
  if (typeof value === 'number') {
    return value > 0
  }
  const text = String(value ?? '').trim().toLowerCase()
  return Boolean(text && ACTIVE_TEXT_VALUES.has(text))
}

const resolveVerified = (profile = {}) => Boolean(
  isActiveValue(profile?.is_verified) ||
  isActiveValue(profile?.real_name_verified) ||
  isActiveValue(profile?.verified) ||
  isActiveValue(profile?.verifyType) ||
  isActiveValue(profile?.verifyText) ||
  String(profile?.verified_real_name || '').trim()
)

const resolveMemberEnabled = (profile = {}) => {
  const candidateFlags = [
    profile?.is_member,
    profile?.member_opened,
    profile?.pro_member,
    profile?.vip_opened,
    profile?.vip_member
  ]
  if (candidateFlags.some(isActiveValue)) {
    return true
  }
  const statusText = String(profile?.member_status || profile?.vip_status || '').trim().toLowerCase()
  return ACTIVE_TEXT_VALUES.has(statusText)
}

const resolveCircleOwner = (profile = {}) => Boolean(
  isActiveValue(profile?.is_circle_owner) ||
  isActiveValue(profile?.circle_owner) ||
  isActiveValue(profile?.is_owner) ||
  isActiveValue(profile?.circle_owner_status) ||
  isActiveValue(profile?.owner_status)
)

const resolveIdentityBadges = (profile = {}) => {
  const badges = []
  if (resolveVerified(profile)) {
    badges.push({ key: 'certification', icon: IDENTITY_BADGE_ICONS.certification })
  }
  if (resolveMemberEnabled(profile)) {
    badges.push({ key: 'member', icon: IDENTITY_BADGE_ICONS.member })
  }
  if (resolveCircleOwner(profile)) {
    badges.push({ key: 'leader', icon: IDENTITY_BADGE_ICONS.leader })
  }
  return badges
}

const imageList = computed(() => {
  return Array.isArray(post.value?.images)
    ? post.value.images.map((item) => String(item || '').trim()).filter(Boolean)
    : []
})

const subImages = computed(() => imageList.value.slice(1, 3))
const authorName = computed(() => String(post.value?.author?.nickname || '未命名用户').trim())
const authorAvatar = computed(() => String(post.value?.author?.avatar_url || 'https://cos.cnptec.site/static/logo.png').trim() || 'https://cos.cnptec.site/static/logo.png')
const authorRole = computed(() => {
  const profile = cardProfile.value && typeof cardProfile.value === 'object' ? cardProfile.value : {}
  const author = post.value?.author && typeof post.value.author === 'object' ? post.value.author : {}
  const jobTitle = String(profile.job_title || author.job_title || '').trim()
  const cityName = String(profile.city_name || author.city_name || '').trim()
  const companyName = String(profile.company_name || author.company_name || '').trim()
  const fallbackRole = String(author.role || profile.industry_label || author.industry_label || '').trim()
  const secondary = cityName || companyName
  if (jobTitle && secondary) {
    return `${jobTitle} · ${secondary}`
  }
  if (jobTitle || secondary) {
    return jobTitle || secondary
  }
  return fallbackRole || '商务人士'
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
const authorIdentitySource = computed(() => {
  const profile = cardProfile.value && typeof cardProfile.value === 'object' ? cardProfile.value : {}
  const author = post.value?.author && typeof post.value.author === 'object' ? post.value.author : {}
  return {
    ...author,
    ...profile
  }
})
const authorBadges = computed(() => resolveIdentityBadges(authorIdentitySource.value))
const cardName = computed(() => String(cardSource.value?.nickname || authorName.value || '未命名用户').trim())
const cardAvatar = computed(() => String(cardSource.value?.avatar_url || authorAvatar.value || 'https://cos.cnptec.site/static/logo.png').trim() || 'https://cos.cnptec.site/static/logo.png')
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
  const hh = `${date.getHours()}`.padStart(2, '0')
  const mm = `${date.getMinutes()}`.padStart(2, '0')
  return `${y}-${m}-${d} ${hh}:${mm}`
})

const resourceCollectCount = computed(() => {
  return Number(post.value?.collect_count ?? post.value?.favorite_count ?? post.value?.like_count ?? 0)
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
    const targetUserId = authorUserId.value
    if (targetUserId) {
      loadCardProfile(targetUserId, { silent: true })
    }

    isPostInterested.value = Boolean(data?.is_collected ?? data?.collected ?? data?.is_interested ?? data?.interested ?? data?.liked)

    const viewData = await reportResourceView(postCode.value)
    if (typeof viewData?.view_count !== 'undefined') {
      post.value = {
        ...post.value,
        view_count: Number(viewData.view_count || post.value.view_count || 0)
      }
    }

    // 数据加载完成后，检查是否需要执行待处理的收藏操作。
    checkAndPerformPendingInterest()
  } catch (err) {
    loadError.value = err?.message || '资源详情加载失败'
    showToast(loadError.value)
  } finally {
    loading.value = false
  }
}

const checkAndPerformPendingInterest = () => {
  const pendingPostCode = uni.getStorageSync('pendingResourceCollectPostCode') || uni.getStorageSync('pendingInterestPostCode')
  const currentPostCode = String(postCode.value || '').trim()

  if (isLoggedIn() && pendingPostCode && pendingPostCode === currentPostCode) {
    // 登录成功且需要收藏资源，并且数据已加载。
    performPendingInterest()
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

const loadCardProfile = async (targetUserId, options = {}) => {
  if (!targetUserId || cardProfileUserId.value === targetUserId) {
    return
  }
  const silent = Boolean(options?.silent)
  cardProfile.value = {}
  cardProfileUserId.value = ''
  if (!silent) {
    cardLoading.value = true
  }
  cardLoadError.value = ''
  try {
    const profile = await getUserProfileById(targetUserId)
    cardProfile.value = profile || {}
    cardProfileUserId.value = targetUserId
  } catch (err) {
    cardLoadError.value = err?.message || '名片加载失败'
  } finally {
    if (!silent) {
      cardLoading.value = false
    }
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

const onTapCollect = () => {
  if (!isLoggedIn()) {
    onCollectBeforeLogin()
    return
  }
  onToggleResourceCollect()
}

const onCollectBeforeLogin = () => {
  // 保存当前资源编码，登录后自动完成收藏。
  const postCode = String(post.value?.post_code || '').trim()
  if (!postCode) {
    showToast('资源信息缺失')
    return
  }

  // 保存标记
  uni.setStorageSync('pendingResourceCollectPostCode', postCode)

  // 跳转到登录页
  uni.navigateTo({
    url: '/pages/auth/login/index'
  })
}

const onToggleResourceCollect = async () => {
  const currentPostCode = String(post.value?.post_code || postCode.value || '').trim()
  if (!currentPostCode) {
    showToast('资源信息缺失')
    return
  }

  try {
    const result = await toggleResourceCollection(currentPostCode, !isPostInterested.value)
    const nextCollected = Boolean(result?.is_collected ?? result?.collected ?? result?.is_interested ?? result?.interested ?? result?.liked)
    const nextCount = Number(result?.collect_count ?? result?.favorite_count ?? result?.like_count ?? resourceCollectCount.value)
    isPostInterested.value = nextCollected
    post.value = {
      ...post.value,
      liked: nextCollected,
      interested: nextCollected,
      is_interested: nextCollected,
      collected: nextCollected,
      is_collected: nextCollected,
      like_count: nextCount,
      collect_count: nextCount,
      favorite_count: nextCount
    }
    reportDetailFeedback(nextCollected ? 'interest' : 'cancel_interest', { action: 'resource_collect' })
    showToast(nextCollected ? '已收藏' : '已取消收藏')
  } catch (error) {
    console.error('Toggle resource collect failed:', error)
    showToast('操作失败，请稍后重试')
  }
}

const goChatFromCard = () => {
  if (!isLoggedIn()) {
    showToast('\u8bf7\u5148\u767b\u5f55')
    return
  }
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

onShow(() => {
  // onShow 时不需要检查，因为会在 fetchDetail 完成后检查
})

const performPendingInterest = async () => {
  try {
    const currentPostCode = String(post.value?.post_code || postCode.value || '').trim()
    if (!currentPostCode) {
      showToast('资源信息缺失')
      uni.removeStorageSync('pendingResourceCollectPostCode')
      uni.removeStorageSync('pendingInterestPostCode')
      return
    }

    const result = await toggleResourceCollection(currentPostCode, true)
    const nextCount = Number(result?.collect_count ?? result?.favorite_count ?? result?.like_count ?? resourceCollectCount.value)
    isPostInterested.value = Boolean(result?.is_collected ?? result?.collected ?? result?.is_interested ?? result?.interested ?? result?.liked)
    post.value = {
      ...post.value,
      liked: isPostInterested.value,
      interested: isPostInterested.value,
      is_interested: isPostInterested.value,
      collected: isPostInterested.value,
      is_collected: isPostInterested.value,
      like_count: nextCount,
      collect_count: nextCount,
      favorite_count: nextCount
    }
    showToast('已收藏')
    // 清除标记
    uni.removeStorageSync('pendingResourceCollectPostCode')
    uni.removeStorageSync('pendingInterestPostCode')
  } catch (error) {
    console.error('Pending interest failed:', error)
    showToast('收藏失败，请稍后重试')
    // 即使失败也清除标记，避免重复尝试
    uni.removeStorageSync('pendingResourceCollectPostCode')
    uni.removeStorageSync('pendingInterestPostCode')
  }
}

onPullDownRefresh(async () => {
  await fetchDetail()
  uni.stopPullDownRefresh()
})
</script>

<style scoped>
.detail-page {
  height: 100vh;
  overflow: hidden;
  background: #f5f6f8;
  color: #111827;
  font-family: 'Public Sans', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.detail-scroll {
  height: 100vh;
}

.detail-scroll-with-bar {
  height: calc(100vh - 136rpx - env(safe-area-inset-bottom));
}

.detail-main {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
  padding-bottom: 24rpx;
}

.publisher-row {
  padding: 28rpx 32rpx;
  border-top: 1rpx solid #eef1f4;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
}

.publisher-row-hover {
  background: #f8fafc;
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
  width: 84rpx;
  height: 84rpx;
  border-radius: 42rpx;
  flex-shrink: 0;
}

.avatar {
  width: 100%;
  height: 100%;
  border-radius: 42rpx;
  background: #e8f1ff;
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
  min-width: 0;
}

.publisher-name {
  max-width: 420rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #1f2329;
  font-size: 32rpx;
  line-height: 44rpx;
  font-weight: 700;
}

.badge-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
  flex-shrink: 0;
  overflow: visible;
}

.identity-badge {
  display: block;
  width: 40rpx;
  height: 40rpx;
  flex-shrink: 0;
}

.publisher-role {
  color: #9aa1ab;
  font-size: 24rpx;
  line-height: 34rpx;
}

.publisher-chevron {
  width: 16rpx;
  height: 16rpx;
  margin-right: 8rpx;
  border-top: 3rpx solid #c5cad3;
  border-right: 3rpx solid #c5cad3;
  transform: rotate(45deg);
  flex-shrink: 0;
}

.content-card {
  background: #ffffff;
  overflow: hidden;
}

.content-head {
  padding: 36rpx 32rpx 24rpx;
  display: flex;
  flex-direction: column;
  gap: 28rpx;
}

.detail-title {
  color: #1f2329;
  font-size: 40rpx;
  line-height: 56rpx;
  font-weight: 700;
}

.detail-body {
  display: flex;
  flex-direction: column;
  gap: 28rpx;
}

.detail-line {
  color: #8b919c;
  font-size: 28rpx;
  line-height: 48rpx;
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

.publish-meta {
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 4rpx 32rpx 36rpx;
}

.publish-clock {
  width: 28rpx;
  height: 28rpx;
  display: block;
  flex-shrink: 0;
}

.publish-time {
  color: #a0a6b0;
  font-size: 24rpx;
  line-height: 34rpx;
  flex-shrink: 0;
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
  margin: 24rpx 32rpx;
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

.bottom-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 20;
  background: #ffffff;
  border-top: 1rpx solid #eef1f4;
  padding: 16rpx 24rpx calc(16rpx + env(safe-area-inset-bottom));
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.bottom-actions {
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.icon-action {
  width: 96rpx;
  min-width: 96rpx;
  height: 88rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
  line-height: 1;
  overflow: visible;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-action-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6rpx;
}

.icon-action::after {
  border: 0;
}

.icon-action-hover {
  opacity: 0.72;
}

.icon-action-image {
  width: 44rpx;
  height: 44rpx;
  display: block;
}

.icon-action-label {
  color: #6b7280;
  font-size: 20rpx;
  line-height: 28rpx;
}

.icon-action-label-active {
  color: #2f6bff;
}

.contact-btn {
  flex: 1;
  height: 88rpx;
  margin: 0;
  padding: 0;
  border: 0;
  border-radius: 999rpx;
  background: #2f6bff;
  color: #ffffff;
  font-size: 32rpx;
  line-height: 88rpx;
  font-weight: 600;
}

.contact-btn::after {
  border: 0;
}

.contact-btn-hover {
  opacity: 0.88;
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

  .content-card,
  .recommend-card,
  .status-wrap,
  .bottom-bar {
    background: #1a1a1a;
  }

  .publisher-row,
  .bottom-bar {
    border-top-color: #2a2a2a;
  }

  .publisher-row-hover {
    background: #222222;
  }

  .publisher-name,
  .detail-title,
  .recommend-title,
  .recommend-name {
    color: #ffffff;
  }

  .publisher-role,
  .detail-line,
  .publish-time,
  .status-text,
  .icon-action-label {
    color: #8a8a8a;
  }

  .publisher-chevron {
    border-top-color: #6b7280;
    border-right-color: #6b7280;
  }

  .avatar,
  .gallery-image {
    background: #2a2a2a;
  }

  .recommend-from {
    color: #666666;
  }

  .recommend-arrow {
    color: #4a4a4a;
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
