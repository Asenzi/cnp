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
        <ProfileHeroSection :profile="pageData.profile" :show-action="true" action-type="share" :is-self="isSelfProfile"
          @share="onOpenShareMenu" />
        <ProfileBioSection :bio="pageData.profile.bio" />
        <ProfileContactSection :contact="contactSectionData" @unlock-contact="onOpenMemberCenter" />
        <!-- <ProfileStatsSection :stats="pageData.stats" /> -->

        <view class="tab-divider"></view>
        <view class="tabs-sticky">
          <ProfileTabsBar :tabs="pageData.tabs" :active-key="activeTab" @change="onSwitchTab" />
        </view>

        <view class="content-list-wrap" :class="{ 'content-list-wrap-with-bottom': showBottomActionBar }">
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
                <image class="section-empty-icon" src="https://cos.cnptec.site/static/icon/data-block.png"
                  mode="aspectFit" />
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
                <image class="section-empty-icon" src="https://cos.cnptec.site/static/icon/data-block.png"
                  mode="aspectFit" />
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

    <view v-if="showBottomActionBar" class="bottom-action-bar">
      <button v-if="!isLoggedIn" class="action-btn action-btn-primary" hover-class="action-btn-active"
        @tap="onLoginToCreateCard">
        创建名片
      </button>
      <template v-else>
        <button class="action-btn action-btn-danger" hover-class="action-btn-active" @tap="onReportProfile">
          举报
        </button>
        <button class="action-btn action-btn-secondary" hover-class="action-btn-active" open-type="share">
          分享名片
        </button>
        <button class="action-btn action-btn-primary" :class="{ 'action-btn-followed': isNetworkCollected }"
          :disabled="collectingNetwork" hover-class="action-btn-active" @tap="onToggleNetworkCollect">
          {{ collectingNetwork ? '处理中...' : (isNetworkCollected ? '已收藏' : '收藏人脉') }}
        </button>
      </template>
    </view>

    <!-- 隐藏的Canvas用于生成分享图 -->
    <canvas canvas-id="shareCanvas"
      style="position: fixed; left: -9999px; top: -9999px; width: 750px; height: 900px; border: none;"></canvas>

    <!-- 分享菜单弹窗 -->
    <view v-if="shareMenuVisible" class="share-menu-mask" @tap="onCloseShareMenu">
      <view class="share-menu-panel" @tap.stop="">
        <view class="share-menu-list">
          <button class="share-menu-item" hover-class="share-menu-item-hover" open-type="share">
            <text class="share-menu-text">分享</text>
          </button>
          <button class="share-menu-item" hover-class="share-menu-item-hover" @tap="onCreateCard">
            <text class="share-menu-text">创建名片</text>
          </button>
          <button class="share-menu-item" hover-class="share-menu-item-hover" @tap="onTapFollowFromMenu">
            <text class="share-menu-text">{{ isFollowing ? '取消关注' : '关注' }}</text>
          </button>
          <button v-if="!isSelfProfile" class="share-menu-item share-menu-danger" hover-class="share-menu-item-hover" @tap="onReportProfile">
            <text class="share-menu-text share-menu-danger-text">举报资料</text>
          </button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom, onShareAppMessage, onShow } from '@dcloudio/uni-app'
import { getMyCircles, getUserCircles } from '../../../api/circle'
import { toggleUserFollow, toggleUserInterest } from '../../../api/network'
import { getMyResourceFeed, getUserResourceFeed } from '../../../api/post'
import { createContentReport, getCurrentUserProfile, getUserProfileById } from '../../../api/user'
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
const shareMenuVisible = ref(false) // 分享菜单显示状态
const collectingNetwork = ref(false)

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

const isLoggedIn = computed(() => {
  const token = String(uni.getStorageSync('token') || '').trim()
  return Boolean(token)
})

const toFiniteNumber = (value) => {
  const parsed = Number(value)
  return Number.isFinite(parsed) ? parsed : null
}

const toRadians = (degree) => degree * Math.PI / 180

const calculateDistanceKm = (fromLat, fromLng, toLat, toLng) => {
  const lat1 = toFiniteNumber(fromLat)
  const lng1 = toFiniteNumber(fromLng)
  const lat2 = toFiniteNumber(toLat)
  const lng2 = toFiniteNumber(toLng)
  if ([lat1, lng1, lat2, lng2].some((item) => item === null)) {
    return null
  }

  const earthRadiusKm = 6371
  const dLat = toRadians(lat2 - lat1)
  const dLng = toRadians(lng2 - lng1)
  const a = Math.sin(dLat / 2) ** 2 +
    Math.cos(toRadians(lat1)) * Math.cos(toRadians(lat2)) * Math.sin(dLng / 2) ** 2
  return earthRadiusKm * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a))
}

const formatDistanceText = (distanceKm) => {
  const distance = toFiniteNumber(distanceKm)
  if (distance === null) {
    return ''
  }
  if (distance < 1) {
    return `距你${Math.max(1, Math.round(distance * 1000))}m`
  }
  if (distance < 10) {
    return `距你${distance.toFixed(1)}km`
  }
  return `距你${Math.round(distance)}km`
}

const getProfileLatitude = (profile = {}) => profile?.latitude ?? profile?.lat
const getProfileLongitude = (profile = {}) => profile?.longitude ?? profile?.lng

const buildProfileLocationLine = (profile = {}) => {
  const province = String(profile?.province_name || profile?.province || '').trim()
  const city = String(profile?.city_name || profile?.city || '').trim()
  const locationText = province && city && !city.includes(province)
    ? `${province}${city}`
    : (city || province)

  const currentUser = uni.getStorageSync('userInfo') || {}
  const distanceText = isSelfProfile.value
    ? ''
    : formatDistanceText(calculateDistanceKm(
      getProfileLatitude(currentUser),
      getProfileLongitude(currentUser),
      getProfileLatitude(profile),
      getProfileLongitude(profile)
    ))

  return [locationText, distanceText].filter(Boolean).join(' · ')
}

const updateNavigationTitle = () => {
  uni.setNavigationBarTitle({
    title: isSelfProfile.value ? '我的名片' : '人脉详情'
  })
}

const hasProfileData = computed(() => Boolean(String(rawProfile.value?.user_id || '').trim()))
const hasFeedAny = computed(() => feedPosts.value.length > 0)
const hasCircleAny = computed(() => joinedCircles.value.length > 0)
const isFollowing = computed(() => Boolean(rawProfile.value?.is_following || rawProfile.value?.followed))
const isNetworkCollected = computed(() => Boolean(rawProfile.value?.is_interested || rawProfile.value?.interested))
const showBottomActionBar = computed(() => Boolean(!isSelfProfile.value && String(targetUserId.value || '').trim()))
const isActiveMemberValue = (value) => {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value > 0
  const normalized = String(value ?? '').trim().toLowerCase()
  return ['1', 'true', 'yes', 'active', 'opened', 'member', 'vip', 'paid', 'enabled', 'on', '已开通', '会员'].includes(normalized)
}
const getCurrentUserIsMember = () => {
  const userInfo = uni.getStorageSync('userInfo') || {}
  if ([
    userInfo.is_member,
    userInfo.member_opened,
    userInfo.pro_member,
    userInfo.vip_opened,
    userInfo.vip_member
  ].some((item) => isActiveMemberValue(item))) {
    return true
  }
  const statusText = String(userInfo.member_status || userInfo.vip_status || '').trim()
  if (isActiveMemberValue(statusText)) {
    return true
  }
  const expireAtRaw = userInfo.member_expire_at || userInfo.vip_expire_at
  if (expireAtRaw) {
    const expireTs = new Date(String(expireAtRaw).replace(' ', 'T')).getTime()
    if (Number.isFinite(expireTs) && expireTs > Date.now()) return true
  }
  return false
}
const shouldMaskProfileSensitiveInfo = () => Boolean(!isSelfProfile.value && !getCurrentUserIsMember())
const MASK_TEXT = '********'
const contactSectionData = computed(() => {
  const displayPhone = String(rawProfile.value?.display_phone || '').trim()
  const displayWechat = String(rawProfile.value?.display_wechat || '').trim()
  const displayEmail = String(rawProfile.value?.display_email || rawProfile.value?.email || '').trim()
  const verifiedRealName = String(rawProfile.value?.verified_real_name || '').trim()
  const isSelf = Boolean(isSelfProfile.value)
  const selfHasContact = Boolean(displayPhone || displayWechat || displayEmail)
  const maskSensitive = shouldMaskProfileSensitiveInfo()

  return {
    name: maskSensitive ? MASK_TEXT : (verifiedRealName || String(rawProfile.value?.nickname || '').trim()),
    companyName: maskSensitive ? MASK_TEXT : String(rawProfile.value?.company_name || rawProfile.value?.company || '').trim(),
    jobTitle: maskSensitive ? MASK_TEXT : String(rawProfile.value?.job_title || rawProfile.value?.card_title || rawProfile.value?.position || '').trim(),
    cityName: buildProfileLocationLine(rawProfile.value || {}),
    avatarUrl: String(rawProfile.value?.avatar_url || '').trim(),
    miniappCodeUrl: String(rawProfile.value?.miniapp_code_url || '').trim(),
    displayPhone,
    displayWechat,
    displayEmail,
    contactVisible: isSelf ? selfHasContact : (maskSensitive ? false : Boolean(rawProfile.value?.contact_visible)),
    contactLockedReason: isSelf
      ? (selfHasContact ? '' : '你还未完善展示手机号、微信号或邮箱')
      : (maskSensitive ? '开通会员即可查看联系方式' : String(rawProfile.value?.contact_locked_reason || '').trim()),
    isSelf
  }
})

const syncPageData = () => {
  pageData.value = resolveProfileHomeData(rawProfile.value || {}, {
    posts: feedPosts.value,
    circles: joinedCircles.value,
    locationLine: buildProfileLocationLine(rawProfile.value || {}),
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
    updateNavigationTitle()
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
    updateNavigationTitle()
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

const onFollowBeforeLogin = () => {
  // 保存当前用户ID和标记，表示登录后需要关注
  const target = String(targetUserId.value || '').trim()
  if (!target) {
    showToast('用户信息缺失')
    return
  }

  // 设置标记
  uni.setStorageSync('pendingFollowUserId', target)

  // 跳转到登录页
  uni.navigateTo({
    url: '/pages/auth/login/index'
  })
}

const onCreateCard = () => {
  if (!isLoggedIn.value) {
    onLoginToCreateCard()
    return
  }

  uni.navigateTo({
    url: '/pages/me/editInfo/index'
  })
}

const onLoginToCreateCard = () => {
  uni.navigateTo({
    url: '/pages/auth/login/index'
  })
}

const onOpenMemberCenter = () => {
  if (!isLoggedIn.value) {
    uni.navigateTo({
      url: '/pages/auth/login/index'
    })
    return
  }

  uni.navigateTo({
    url: '/pages/me/member-center/index'
  })
}

const onOpenShareMenu = () => {
  shareMenuVisible.value = true
}

const onCloseShareMenu = () => {
  shareMenuVisible.value = false
}

const onTapFollowFromMenu = async () => {
  onCloseShareMenu()
  await onToggleFollow()
}

const onReportProfile = () => {
  onCloseShareMenu()
  const target = String(targetUserId.value || rawProfile.value?.user_id || rawProfile.value?.userId || '').trim()
  if (!target) {
    showToast('用户信息缺失')
    return
  }
  if (!isLoggedIn.value) {
    onLoginToCreateCard()
    return
  }
  uni.showActionSheet({
    itemList: ['色情低俗头像/资料', '广告引流或诈骗', '冒充他人', '其他违规'],
    success: async (res) => {
      const reasons = ['色情低俗头像/资料', '广告引流或诈骗', '冒充他人', '其他违规']
      try {
        await createContentReport({
          target_type: 'profile',
          target_id: target,
          reason: reasons[Number(res.tapIndex || 0)] || '其他违规'
        })
        showToast('举报已提交')
      } catch (err) {
        showToast(err?.message || '举报失败，请稍后重试')
      }
    }
  })
}

const onToggleFollow = async () => {
  const target = String(targetUserId.value || '').trim()
  if (!target) {
    showToast('用户信息缺失')
    return
  }

  const willFollow = !isFollowing.value

  try {
    await toggleUserFollow(target, willFollow)

    // 更新本地状态
    if (rawProfile.value) {
      rawProfile.value.is_following = willFollow
      rawProfile.value.followed = willFollow
    }

    showToast(willFollow ? '关注成功' : '已取消关注')
  } catch (error) {
    console.error('关注操作失败:', error)
    showToast(error?.message || '操作失败，请稍后重试')
  }
}

const onToggleNetworkCollect = async () => {
  const target = String(targetUserId.value || rawProfile.value?.user_id || rawProfile.value?.userId || '').trim()
  if (!target) {
    showToast('用户信息缺失')
    return
  }
  if (!isLoggedIn.value) {
    onLoginToCreateCard()
    return
  }

  const nextCollected = !isNetworkCollected.value
  if (collectingNetwork.value) {
    return
  }
  collectingNetwork.value = true
  try {
    const payload = await toggleUserInterest(target, nextCollected)
    const resolvedCollected = Boolean(payload?.is_interested ?? payload?.interested ?? nextCollected)
    if (rawProfile.value) {
      rawProfile.value.is_interested = resolvedCollected
      rawProfile.value.interested = resolvedCollected
    }
    showToast(resolvedCollected ? '已收藏人脉' : '已取消收藏')
  } catch (error) {
    const statusCode = Number(error?.statusCode || 0)
    if (statusCode === 401) {
      clearLoginState()
      onLoginToCreateCard()
      return
    }
    showToast(error?.message || '操作失败，请稍后重试')
  } finally {
    collectingNetwork.value = false
  }
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
  const sceneUserId = decodeURIComponent(String(query?.scene || '').trim())
  targetUserId.value = String(query?.userId || sceneUserId || '').trim()
  updateNavigationTitle()
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
  overflow: visible;
  background: #ffffff;
  box-shadow: 0 12rpx 30rpx rgba(15, 23, 42, 0.08);
}

.tabs-sticky {
  position: -webkit-sticky;
  position: sticky;
  top: 0rpx;
  z-index: 50;
  width: 100%;
  box-sizing: border-box;
  background: #ffffff;
  box-shadow: 0 2rpx 8rpx rgba(15, 23, 42, 0.05);
}

.tab-divider {
  height: 12rpx;
  background: #eef2f7;
}

.content-list-wrap {
  background: #f8f8f8;
  padding: 16rpx 32rpx calc(5rpx + env(safe-area-inset-bottom));
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.content-list-wrap-with-bottom {
  padding-bottom: calc(150rpx + env(safe-area-inset-bottom));
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

.follow-action-fixed {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
  padding: 16rpx 32rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: linear-gradient(180deg, rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 0.95) 20%, #ffffff 100%);
  backdrop-filter: blur(10rpx);
}

.follow-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #1a57db 0%, #2563eb 100%);
  border-radius: 44rpx;
  border: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 600;
  box-shadow: 0 4rpx 12rpx rgba(26, 87, 219, 0.2);
}

.follow-btn::after {
  border: 0;
}

.follow-btn-active {
  opacity: 0.85;
  transform: scale(0.98);
}

.bottom-action-bar {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 100;
  box-sizing: border-box;
  padding: 18rpx 32rpx calc(-20rpx + env(safe-area-inset-bottom));
  background: linear-gradient(180deg, rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 0.95) 20%, #ffffff 100%);
  backdrop-filter: blur(10rpx);
  display: flex;
  gap: 16rpx;
}

.action-btn {
  flex: 1;
  height: 88rpx;
  border-radius: 44rpx;
  border: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 30rpx;
  font-weight: 600;
}

.action-btn::after {
  border: 0;
}

.action-btn[disabled] {
  opacity: 0.72;
}

.action-btn-primary {
  background: linear-gradient(135deg, #1a57db 0%, #2563eb 100%);
  color: #ffffff;
  box-shadow: 0 4rpx 12rpx rgba(26, 87, 219, 0.2);
}

.action-btn-secondary {
  background: #f1f5f9;
  color: #334155;
  box-shadow: 0 2rpx 8rpx rgba(15, 23, 42, 0.08);
}

.action-btn-danger {
  background: #fef2f2;
  color: #dc2626;
  box-shadow: 0 2rpx 8rpx rgba(220, 38, 38, 0.08);
}

.action-btn-followed {
  background: #e0e7ff;
  color: #4f46e5;
  box-shadow: 0 2rpx 8rpx rgba(79, 70, 229, 0.15);
}

.action-btn-active {
  opacity: 0.85;
  transform: scale(0.98);
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

  .tabs-sticky {
    background: #0f172a;
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.24);
  }

  .section-status-wrap {
    background: #0f172a;
    border-color: #334155;
  }

  .section-empty-wrap {
    background: transparent;
  }

  .follow-action-fixed {
    background: linear-gradient(180deg, rgba(17, 22, 33, 0) 0%, rgba(17, 22, 33, 0.95) 20%, #111621 100%);
  }

  .follow-btn {
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
    box-shadow: 0 4rpx 12rpx rgba(37, 99, 235, 0.3);
  }

  .bottom-action-bar {
    background: linear-gradient(180deg, rgba(17, 22, 33, 0) 0%, rgba(17, 22, 33, 0.95) 20%, #111621 100%);
  }

  .action-btn-primary {
    background: linear-gradient(135deg, #2563eb 0%, #3b82f6 100%);
    box-shadow: 0 4rpx 12rpx rgba(37, 99, 235, 0.3);
  }

  .action-btn-secondary {
    background: #1e293b;
    color: #e2e8f0;
    box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.24);
  }

  .action-btn-danger {
    background: #3f1d1d;
    color: #fca5a5;
  }

  .action-btn-followed {
    background: #312e81;
    color: #a5b4fc;
    box-shadow: 0 2rpx 8rpx rgba(165, 180, 252, 0.2);
  }
}

/* 分享菜单弹窗样式 */
.share-menu-mask {
  position: fixed;
  left: 0;
  right: 0;
  top: 0;
  bottom: 0;
  z-index: 9999;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  justify-content: center;
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }

  to {
    opacity: 1;
  }
}

.share-menu-panel {
  width: 100%;
  max-width: 750rpx;
  background: #ffffff;
  border-radius: 32rpx 32rpx 0 0;
  padding: 0 0 calc(32rpx + env(safe-area-inset-bottom));
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(100%);
  }

  to {
    transform: translateY(0);
  }
}

.share-menu-list {
  padding: 24rpx 32rpx;
  display: flex;
  flex-direction: column;
  gap: 0;
}

.share-menu-item {
  height: 96rpx;
  margin: 0;
  padding: 0 32rpx;
  border: 0;
  border-radius: 20rpx;
  background: transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease;
}

.share-menu-item::after {
  border: 0;
}

.share-menu-text {
  color: #111827;
  font-size: 32rpx;
  line-height: 40rpx;
  font-weight: 500;
}

.share-menu-danger-text {
  color: #dc2626;
}

.share-menu-item-hover {
  background: #f8fafc;
}
</style>
