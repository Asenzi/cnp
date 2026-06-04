<template>
  <view class="profile-home-page">
    <view class="page-shell">
      <view v-if="loading && !hasProfileData" class="status-wrap">
          <text class="status-text">加载中...</text>
      </view>

      <view v-else-if="loadError && !hasProfileData" class="status-wrap">
        <text class="status-text">{{ loadError }}</text>
        <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetryAll">閲嶆柊鍔犺浇</button>
      </view>

      <view v-else>
        <ProfileHeroSection :profile="pageData.profile" :show-action="true" action-type="share" />
        <ProfileBioSection :bio="pageData.profile.bio" />
        <ProfileContactSection :contact="contactSectionData" />
        <!-- <ProfileStatsSection :stats="pageData.stats" /> -->

        <view class="tab-divider"></view>
        <view class="tabs-sticky">
          <ProfileTabsBar :tabs="pageData.tabs" :active-key="activeTab" @change="onSwitchTab" />
        </view>

        <view class="content-list-wrap">
          <template v-if="activeTab === 'feed'">
            <view v-if="feedLoading && !hasFeedAny" class="section-status-wrap">
            <text class="section-status-text">加载中...</text>
            </view>
            <view v-else-if="feedError && !hasFeedAny" class="section-status-wrap">
              <text class="section-status-text">{{ feedError }}</text>
              <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetryFeed">閲嶈瘯</button>
            </view>
            <template v-else>
              <ProfilePostCard v-for="item in feedPosts" :key="item.id" :item="item" @detail="onTapPostDetail" />
              <view v-if="feedLoaded && !hasFeedAny" class="section-status-wrap section-empty-wrap">
                <image class="section-empty-icon" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
                <text class="section-status-text section-empty-text">暂无动态资源</text>
              </view>
              <view v-if="feedLoadingMore" class="load-more-wrap">
            <text class="load-more-text">加载中...</text>
              </view>
              <view v-else-if="feedHasMore && hasFeedAny" class="load-more-wrap">
                <text class="load-more-text">上拉加载更多</text>
              </view>
            </template>
          </template>

          <template v-else>
            <view v-if="circlesLoading && !hasCircleAny" class="section-status-wrap">
            <text class="section-status-text">加载中...</text>
            </view>
            <view v-else-if="circlesError && !hasCircleAny" class="section-status-wrap">
              <text class="section-status-text">{{ circlesError }}</text>
              <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetryCircles">閲嶈瘯</button>
            </view>
            <template v-else>
              <ProfileCircleCard v-for="item in joinedCircles" :key="item.id" :item="item" @enter="onEnterCircle" />
              <view v-if="circlesLoaded && !hasCircleAny" class="section-status-wrap section-empty-wrap">
                <image class="section-empty-icon" src="https://cos.cnptec.site/static/icon/data-block.png" mode="aspectFit" />
                <text class="section-status-text section-empty-text">暂无加入的圈子</text>
              </view>
              <view v-if="circlesLoadingMore" class="load-more-wrap">
            <text class="load-more-text">加载中...</text>
              </view>
              <view v-else-if="circlesHasMore && hasCircleAny" class="load-more-wrap">
                <text class="load-more-text">上拉加载更多</text>
              </view>
            </template>
          </template>
        </view>

      </view>
    </view>

    <!-- 隐藏的Canvas用于生成分享图 -->
    <canvas canvas-id="shareCanvas" style="position: fixed; left: -9999px; top: -9999px; width: 750px; height: 900px; border: none;"></canvas>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom, onShareAppMessage, onShow } from '@dcloudio/uni-app'
import { getMyCircles, getUserCircles } from '../../../api/circle'
import { getMyResourceFeed, getUserResourceFeed } from '../../../api/post'
import { getCurrentUserProfile, getUserProfileById } from '../../../api/user'
import { generateProfileShareImage } from '../../../utils/profile-share-image'
import ProfileBioSection from './components/ProfileBioSection.vue'
import ProfileCircleCard from './components/ProfileCircleCard.vue'
import ProfileContactSection from './components/ProfileContactSection.vue'
import ProfileHeroSection from './components/ProfileHeroSection.vue'
import ProfilePostCard from './components/ProfilePostCard.vue'
import ProfileStatsSection from './components/ProfileStatsSection.vue'
import ProfileTabsBar from './components/ProfileTabsBar.vue'
import {
  mapProfileCircleItem,
  mapProfilePostItem,
  resolveProfileHomeData
} from './modules/profile-home-view-model'

const PAGE_SIZE = 20

const loading = ref(false)
const loadError = ref('')
const pageData = ref(resolveProfileHomeData({}, { posts: [], circles: [] }))
const activeTab = ref('feed')
const targetUserId = ref('')
const rawProfile = ref({})
const shareImageUrl = ref('') // 缓存分享图片

const feedPosts = ref([])
const feedTotal = ref(0)
const feedCursor = ref('')
const feedHasMore = ref(true)
const feedLoading = ref(false)
const feedLoadingMore = ref(false)
const feedLoaded = ref(false)
const feedError = ref('')

const joinedCircles = ref([])
const circlesTotal = ref(0)
const circlesHasMore = ref(true)
const circlesLoading = ref(false)
const circlesLoadingMore = ref(false)
const circlesLoaded = ref(false)
const circlesError = ref('')

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const ensureLogin = () => {
  const token = String(uni.getStorageSync('token') || '').trim()
  if (token) {
    return true
  }

  showToast('请先登录')
  return false
}

const clearLoginState = () => {
  uni.removeStorageSync('token')
  uni.removeStorageSync('isLoggedIn')
  uni.removeStorageSync('userInfo')
}

const getLocalCurrentUserId = () => {
  const userInfo = uni.getStorageSync('userInfo') || {}
  return String(userInfo?.user_id || userInfo?.userId || '').trim()
}

const isSelfProfile = computed(() => {
  const target = String(targetUserId.value || '').trim()
  if (!target) {
    return true
  }
  const current = getLocalCurrentUserId()
  if (!current) {
    return false
  }
  return target === current
})

const hasProfileData = computed(() => Boolean(String(rawProfile.value?.user_id || '').trim()))
const hasFeedAny = computed(() => feedPosts.value.length > 0)
const hasCircleAny = computed(() => joinedCircles.value.length > 0)
const contactSectionData = computed(() => {
  const displayPhone = String(rawProfile.value?.display_phone || '').trim()
  const displayWechat = String(rawProfile.value?.display_wechat || '').trim()
  const displayEmail = String(rawProfile.value?.display_email || rawProfile.value?.email || '').trim()
  const isSelf = Boolean(isSelfProfile.value)
  const selfHasContact = Boolean(displayPhone || displayWechat)

  return {
    name: String(rawProfile.value?.nickname || '').trim(),
    industryLabel: String(rawProfile.value?.industry_label || '').trim(),
    avatarUrl: String(rawProfile.value?.avatar_url || '').trim(),
    miniappCodeUrl: String(rawProfile.value?.miniapp_code_url || '').trim(),
    displayPhone,
    displayWechat,
    displayEmail,
    contactVisible: isSelf ? selfHasContact : Boolean(rawProfile.value?.contact_visible),
    contactLockedReason: isSelf
      ? (selfHasContact ? '' : '你还未完善展示手机号或微信号')
      : String(rawProfile.value?.contact_locked_reason || '').trim(),
    targetHasContact: isSelf ? selfHasContact : Boolean(rawProfile.value?.target_has_contact),
    targetContactEnabled: isSelf ? rawProfile.value?.show_contact !== false : Boolean(rawProfile.value?.target_contact_enabled),
    viewerContactPackageRemainingViews: isSelf ? 0 : Number(rawProfile.value?.viewer_contact_package_remaining_views || 0),
    viewerContactPackageUsedForView: !isSelf && Boolean(rawProfile.value?.viewer_contact_package_used_for_view),
    isSelf
  }
})

const syncPageData = () => {
  pageData.value = resolveProfileHomeData(rawProfile.value || {}, {
    posts: feedPosts.value,
    circles: joinedCircles.value,
    resourceCount: Number(feedTotal.value || feedPosts.value.length || 0),
    circleCount: Number(circlesTotal.value || rawProfile.value?.circle_count || joinedCircles.value.length || 0)
  })
}

const loadProfile = async () => {
  const target = String(targetUserId.value || '').trim()
  if (!target && !ensureLogin()) {
    loadError.value = '请先登录查看自己的名片'
    return
  }

  loading.value = true
  loadError.value = ''

  try {
    const profile = target
      ? await getUserProfileById(target)
      : await getCurrentUserProfile()

    rawProfile.value = profile || {}
    syncPageData()

    const isSelf = !target || isSelfProfile.value
    if (isSelf) {
      uni.setStorageSync('userInfo', profile || {})
    }
  } catch (err) {
    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      clearLoginState()
      loadError.value = target ? '名片加载失败，请稍后重试' : '请先登录查看自己的名片'
      return
    }
    loadError.value = err?.message || '个人名片加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const fetchProfileFeed = async (reset = false) => {
  const target = String(targetUserId.value || '').trim()
  if (!target && !ensureLogin()) {
    return
  }
  if (feedLoading.value || feedLoadingMore.value) {
    return
  }
  if (!reset && (!feedHasMore.value || !feedCursor.value)) {
    return
  }

  if (reset) {
    feedLoading.value = true
    feedError.value = ''
  } else {
    feedLoadingMore.value = true
  }

  try {
    const payload = target
      ? await getUserResourceFeed(target, {
        cursor: reset ? '' : feedCursor.value,
        limit: PAGE_SIZE
      })
      : await getMyResourceFeed({
        status: 'active',
        cursor: reset ? '' : feedCursor.value,
        limit: PAGE_SIZE
      })

    const incoming = Array.isArray(payload?.items)
      ? payload.items
          .map((item) => mapProfilePostItem(item))
          .filter((item) => item.type !== 'venue') // 过滤掉活动类型 - 第二版上线
      : []
    if (reset) {
      feedPosts.value = incoming
    } else {
      const existed = new Set(feedPosts.value.map((item) => item.id))
      const appended = incoming.filter((item) => !existed.has(item.id))
      feedPosts.value = [...feedPosts.value, ...appended]
    }

    feedCursor.value = String(payload?.next_cursor || '').trim()
    feedHasMore.value = Boolean(payload?.has_more) && Boolean(feedCursor.value)
    const serverTotal = Number(payload?.total)
    feedTotal.value = Number.isFinite(serverTotal) ? Math.max(serverTotal, feedPosts.value.length) : feedPosts.value.length
    feedLoaded.value = true
    feedError.value = ''
    syncPageData()
  } catch (err) {
    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      clearLoginState()
      if (!target) {
        feedError.value = '请先登录查看自己的动态'
      }
      return
    }
    const message = err?.message || '动态资源加载失败，请稍后重试'
    if (reset && !hasFeedAny.value) {
      feedError.value = message
    }
    showToast(message)
  } finally {
    feedLoading.value = false
    feedLoadingMore.value = false
  }
}

const fetchJoinedCircles = async (reset = false) => {
  const target = String(targetUserId.value || '').trim()
  if (!target && !ensureLogin()) {
    return
  }
  if (circlesLoading.value || circlesLoadingMore.value) {
    return
  }
  if (!reset && !circlesHasMore.value) {
    return
  }

  const nextOffset = reset ? 0 : joinedCircles.value.length
  if (reset) {
    circlesLoading.value = true
    circlesError.value = ''
  } else {
    circlesLoadingMore.value = true
  }

  try {
    const payload = target
      ? await getUserCircles(target, {
        offset: nextOffset,
        limit: PAGE_SIZE
      })
      : await getMyCircles({
        offset: nextOffset,
        limit: PAGE_SIZE
      })

    const incoming = Array.isArray(payload?.items) ? payload.items.map((item) => mapProfileCircleItem(item)) : []
    if (reset) {
      joinedCircles.value = incoming
    } else {
      const existed = new Set(joinedCircles.value.map((item) => item.id))
      const appended = incoming.filter((item) => !existed.has(item.id))
      joinedCircles.value = [...joinedCircles.value, ...appended]
    }

    const serverTotal = Number(payload?.total)
    circlesTotal.value = Number.isFinite(serverTotal)
      ? Math.max(serverTotal, joinedCircles.value.length)
      : joinedCircles.value.length
    circlesHasMore.value = Boolean(payload?.has_more) && joinedCircles.value.length < circlesTotal.value
    circlesLoaded.value = true
    circlesError.value = ''
    syncPageData()
  } catch (err) {
    const statusCode = Number(err?.statusCode || 0)
    if (statusCode === 401) {
      clearLoginState()
      if (!target) {
        circlesError.value = '请先登录查看自己的圈子'
      }
      return
    }
    const message = err?.message || '加入圈子加载失败，请稍后重试'
    if (reset && !hasCircleAny.value) {
      circlesError.value = message
    }
    showToast(message)
  } finally {
    circlesLoading.value = false
    circlesLoadingMore.value = false
  }
}

const loadAllData = async () => {
  await loadProfile()
  if (loadError.value) {
    return
  }
  await Promise.all([fetchProfileFeed(true), fetchJoinedCircles(true)])
}

const onSwitchTab = async (tabKey) => {
  activeTab.value = tabKey || 'feed'
  if (activeTab.value === 'feed' && !feedLoaded.value) {
    await fetchProfileFeed(true)
  }
  if (activeTab.value === 'circles' && !circlesLoaded.value) {
    await fetchJoinedCircles(true)
  }
}

const onTapPostDetail = (item) => {
  const postCode = String(item?.postCode || '').trim()
  if (!postCode) {
    showToast('资源编号缺失')
    return
  }
  uni.navigateTo({
    url: `/pages/resources/detail/index?postCode=${encodeURIComponent(postCode)}`
  })
}

const onEnterCircle = (item) => {
  const circleCode = String(item?.circleCode || '').trim()
  if (!circleCode) {
    showToast('圈子编号缺失')
    return
  }
  uni.navigateTo({
    url: `/pages/circles/detail/index?code=${encodeURIComponent(circleCode)}`
  })
}

const onRetryAll = () => {
  loadAllData()
}

const onRetryFeed = () => {
  fetchProfileFeed(true)
}

const onRetryCircles = () => {
  fetchJoinedCircles(true)
}

onShareAppMessage(() => {
  const target = String(rawProfile.value?.user_id || rawProfile.value?.userId || targetUserId.value || '').trim()
  const nickname = String(rawProfile.value?.nickname || pageData.value?.profile?.name || '好友名片').trim() || '好友名片'
  const avatarUrl = String(rawProfile.value?.avatar_url || pageData.value?.profile?.avatarUrl || '').trim()

  return {
    title: `${nickname}的个人名片`,
    path: `/pages/me/card/index?userId=${encodeURIComponent(target)}`,
    imageUrl: avatarUrl || undefined
  }
})


onLoad((query = {}) => {
  targetUserId.value = String(query?.userId || '').trim()
})

onShow(() => {
  // 清除分享图缓存，确保使用最新的分享图生成逻辑
  shareImageUrl.value = ''
  loadAllData()
})

onShareAppMessage(async () => {
  const target = String(rawProfile.value?.user_id || rawProfile.value?.userId || targetUserId.value || '').trim()
  const nickname = String(rawProfile.value?.nickname || pageData.value?.profile?.name || '好友名片').trim() || '好友名片'
  const avatarUrl = String(rawProfile.value?.avatar_url || pageData.value?.profile?.avatarUrl || '').trim()

  // 如果已有缓存的分享图，直接使用
  if (shareImageUrl.value) {
    return {
      title: `${nickname}的个人名片`,
      path: `/pages/me/card/index?userId=${encodeURIComponent(target)}`,
      imageUrl: shareImageUrl.value
    }
  }

  // 生成自定义分享图
  try {
    const userData = {
      nickname: nickname,
      avatarUrl: avatarUrl,
      bio: String(rawProfile.value?.intro || pageData.value?.profile?.bio || '').trim(),
      company: String(rawProfile.value?.company_name || '').trim(),
      jobTitle: String(rawProfile.value?.job_title || '').trim(),
      industry: String(rawProfile.value?.industry_label || '').trim(),
      isVerified: Boolean(rawProfile.value?.is_verified)
    }

    console.log('生成分享图数据:', userData)

    const imagePath = await generateProfileShareImage(userData)
    shareImageUrl.value = imagePath

    return {
      title: `${nickname}的个人名片`,
      path: `/pages/me/card/index?userId=${encodeURIComponent(target)}`,
      imageUrl: imagePath
    }
  } catch (err) {
    console.error('生成分享图失败:', err)
    // 降级方案：使用头像
    return {
      title: `${nickname}的个人名片`,
      path: `/pages/me/card/index?userId=${encodeURIComponent(target)}`,
      imageUrl: avatarUrl || undefined
    }
  }
})

onPullDownRefresh(async () => {
  await loadAllData()
  uni.stopPullDownRefresh()
})

onReachBottom(() => {
  if (activeTab.value === 'feed') {
    fetchProfileFeed(false)
    return
  }
  fetchJoinedCircles(false)
})
</script>

<style scoped>
.profile-home-page {
  min-height: 100vh;
  background: #f6f6f8;
  font-family: 'Manrope', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.page-shell {
  position: relative;
  width: 100%;
  max-width: 750rpx;
  margin: 0 auto;
  min-height: 100vh;
  background: #ffffff;
  box-shadow: 0 12rpx 30rpx rgba(15, 23, 42, 0.08);
}

.tabs-sticky {
  position: sticky;
  top: 0;
  z-index: 10;
}

.tab-divider {
  height: 12rpx;
  background: #eef2f7;
}

.content-list-wrap {
  background: #ffffff;
  padding: 16rpx 32rpx calc(5rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.status-wrap {
  min-height: 100vh;
  padding: 48rpx 32rpx;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 18rpx;
}

.section-status-wrap {
  border-radius: 16rpx;
  border: none;
  background: #ffffff;
  min-height: 220rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 14rpx;
}

.section-empty-wrap {
  padding: 80rpx 20rpx 60rpx;
  border: none;
  background: transparent;
}

.section-empty-icon {
  width: 200rpx;
  height: 200rpx;
  display: block;
  margin: 0 auto 12rpx;
}

.section-empty-text {
  margin-top: 4rpx;
  text-align: center;
}

.status-text,
.section-status-text {
  color: #64748b;
  font-size: 26rpx;
  line-height: 34rpx;
}

.retry-btn {
  height: 64rpx;
  border-radius: 999rpx;
  border: 0;
  padding: 0 28rpx;
  color: #ffffff;
  background: #1a57db;
  font-size: 24rpx;
  line-height: 64rpx;
}

.retry-btn-active {
  opacity: 0.9;
}

.load-more-wrap {
  padding: 12rpx 0 8rpx;
  text-align: center;
}

.load-more-text {
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

@media (prefers-color-scheme: dark) {
  .profile-home-page {
    background: #111621;
  }

  .page-shell {
    background: #111621;
    box-shadow: none;
  }

  .status-text,
  .section-status-text {
    color: #94a3b8;
  }

  .tab-divider,
  .content-list-wrap {
    background: rgba(17, 22, 33, 0.7);
  }

  .section-status-wrap {
    background: #0f172a;
    border-color: #334155;
  }

  .section-empty-wrap {
    background: transparent;
  }
}
</style>
