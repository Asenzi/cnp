<template>
  <view class="profile-home-page">
    <view class="page-shell">
      <view v-if="loading && !hasProfileData" class="status-wrap">
        <text class="status-text">鍔犺浇涓?..</text>
      </view>

      <view v-else-if="loadError && !hasProfileData" class="status-wrap">
        <text class="status-text">{{ loadError }}</text>
        <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetryAll">閲嶆柊鍔犺浇</button>
      </view>

      <view v-else>
        <ProfileHeroSection :profile="pageData.profile" :show-action="true" action-type="share" />
        <ProfileBioSection :bio="pageData.profile.bio" />
        <ProfileContactSection :contact="contactSectionData" />
        <ProfileStatsSection :stats="pageData.stats" />

        <view class="tab-divider"></view>
        <view class="tabs-sticky">
          <ProfileTabsBar :tabs="pageData.tabs" :active-key="activeTab" @change="onSwitchTab" />
        </view>

        <view class="content-list-wrap">
          <template v-if="activeTab === 'feed'">
            <view v-if="feedLoading && !hasFeedAny" class="section-status-wrap">
              <text class="section-status-text">鍔犺浇涓?..</text>
            </view>
            <view v-else-if="feedError && !hasFeedAny" class="section-status-wrap">
              <text class="section-status-text">{{ feedError }}</text>
              <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetryFeed">閲嶈瘯</button>
            </view>
            <template v-else>
              <ProfilePostCard v-for="item in feedPosts" :key="item.id" :item="item" @detail="onTapPostDetail" />
              <view v-if="feedLoaded && !hasFeedAny" class="section-status-wrap section-empty-wrap">
                <image class="section-empty-icon" src="/static/icon/block.png" mode="aspectFit" />
                <text class="section-status-text section-empty-text">暂无动态资源</text>
              </view>
              <view v-if="feedLoadingMore" class="load-more-wrap">
                <text class="load-more-text">鍔犺浇涓?..</text>
              </view>
              <view v-else-if="feedHasMore && hasFeedAny" class="load-more-wrap">
                <text class="load-more-text">涓婃媺鍔犺浇鏇村</text>
              </view>
            </template>
          </template>

          <template v-else>
            <view v-if="circlesLoading && !hasCircleAny" class="section-status-wrap">
              <text class="section-status-text">鍔犺浇涓?..</text>
            </view>
            <view v-else-if="circlesError && !hasCircleAny" class="section-status-wrap">
              <text class="section-status-text">{{ circlesError }}</text>
              <button class="retry-btn" hover-class="retry-btn-active" @tap="onRetryCircles">閲嶈瘯</button>
            </view>
            <template v-else>
              <ProfileCircleCard v-for="item in joinedCircles" :key="item.id" :item="item" @enter="onEnterCircle" />
              <view v-if="circlesLoaded && !hasCircleAny" class="section-status-wrap">
                <text class="section-status-text">暂无加入的圈子</text>
              </view>
              <view v-if="circlesLoadingMore" class="load-more-wrap">
                <text class="load-more-text">鍔犺浇涓?..</text>
              </view>
              <view v-else-if="circlesHasMore && hasCircleAny" class="load-more-wrap">
                <text class="load-more-text">涓婃媺鍔犺浇鏇村</text>
              </view>
            </template>
          </template>
        </view>

      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom, onShareAppMessage, onShow } from '@dcloudio/uni-app'
import { getMyCircles, getUserCircles } from '../../../api/circle'
import { getMyResourceFeed, getUserResourceFeed } from '../../../api/post'
import { getCurrentUserProfile, getUserProfileById } from '../../../api/user'
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
  setTimeout(() => {
    uni.navigateTo({
      url: '/pages/auth/login/index'
    })
  }, 220)
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
  const isSelf = Boolean(isSelfProfile.value)
  const selfHasContact = Boolean(displayPhone || displayWechat)

  return {
    displayPhone,
    displayWechat,
    contactVisible: isSelf ? selfHasContact : Boolean(rawProfile.value?.contact_visible),
    contactLockedReason: isSelf
      ? (selfHasContact ? '' : '你还未完善展示手机号或微信号')
      : String(rawProfile.value?.contact_locked_reason || '').trim(),
    targetHasContact: isSelf ? selfHasContact : Boolean(rawProfile.value?.target_has_contact),
    targetContactEnabled: isSelf ? rawProfile.value?.show_contact !== false : Boolean(rawProfile.value?.target_contact_enabled),
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
  if (!ensureLogin()) {
    return
  }

  loading.value = true
  loadError.value = ''

  try {
    const target = String(targetUserId.value || '').trim()
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
      ensureLogin()
      return
    }
    loadError.value = err?.message || '个人名片加载失败，请稍后重试'
  } finally {
    loading.value = false
  }
}

const fetchProfileFeed = async (reset = false) => {
  if (!ensureLogin()) {
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
    const target = String(targetUserId.value || '').trim()
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

    const incoming = Array.isArray(payload?.items) ? payload.items.map((item) => mapProfilePostItem(item)) : []
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
      ensureLogin()
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
  if (!ensureLogin()) {
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
    const target = String(targetUserId.value || '').trim()
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
      ensureLogin()
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
  loadAllData()
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
  padding: 28rpx 20rpx;
  border: none;
  background: #ffffff;
}

.section-empty-icon {
  width: 88rpx;
  height: 88rpx;
  display: block;
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
}
</style>
