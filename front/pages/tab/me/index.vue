<template>
  <view class="page">
    <view class="header" :style="{ paddingTop: statusBarHeight + 'px' }">
      <text class="title">我的</text>
    </view>

    <view class="main">
      <!-- 已登录 -->
      <view v-if="isLoggedIn" class="user-section">
        <view class="user-card">
          <view class="user-top">
            <image class="avatar" mode="aspectFill" :src="displayAvatar" />
            <view class="user-info">
              <view class="name-line">
                <text class="name">{{ displayName }}</text>
              </view>
              <text class="id">ID: {{ displayUserId }}</text>
              <view v-if="identityBadges.length" class="identity-badges">
                <image
                  v-for="badge in identityBadges"
                  :key="badge.key"
                  class="identity-badge"
                  mode="aspectFit"
                  :src="badge.icon"
                />
              </view>
            </view>
            <view class="edit" @tap="goEditInfo">
              <image class="edit-icon" mode="aspectFit" src="https://cos.cnptec.site/static/icon/edit.png" />
            </view>
          </view>

          <view class="intro" :class="{ 'intro-empty': isIntroEmpty }" @tap="onIntroTap">
            <text class="intro-text">{{ displayIntro }}</text>
          </view>

          <view class="stats">
            <view class="stat" @tap="goMyFollowing">
              <text class="stat-num">{{ displayCollectionCount }}</text>
              <text class="stat-name">收藏</text>
            </view>
            <view class="stat" @tap="goMyCircles">
              <text class="stat-num">{{ displayCircleCount }}</text>
              <text class="stat-name">圈子</text>
            </view>
            <view class="stat" @tap="goMyActivities">
              <text class="stat-num">{{ displayActivityCount }}</text>
              <text class="stat-name">活动</text>
            </view>
            <view class="stat" @tap="goMessages">
              <text class="stat-num">{{ unreadMessageCount }}</text>
              <text class="stat-name">消息</text>
            </view>
          </view>
        </view>

        <!-- 会员提示 -->
        <view class="member-cards">
          <view class="member-card" @tap="onOpenMember">
            <view class="member-card-content">
              <view class="member-card-top">
                <image class="member-icon" mode="aspectFit" src="https://cos.cnptec.site/static/icon/huiyuan.png" />
                <text class="member-title">{{ isMemberOpened ? '会员中心' : '开通会员' }}</text>
              </view>
              <text class="member-desc">{{ isMemberOpened ? '查看会员权益' : '解锁更多权益' }}</text>
            </view>
            <text class="member-arrow">›</text>
          </view>
          <view class="member-card" @tap="onCircleOwnerAction">
            <view class="member-card-content">
              <view class="member-card-top">
                <image class="member-icon" mode="aspectFit" src="https://cos.cnptec.site/static/icon/create.png" />
                <text class="member-title">{{ isCircleOwner ? '管理圈子' : '成为圈主' }}</text>
              </view>
              <text class="member-desc">{{ isCircleOwner ? '创建与管理我的圈子' : '解锁更多圈主权益' }}</text>
            </view>
            <text class="member-arrow">›</text>
          </view>
        </view>
      </view>

      <!-- 未登录 -->
      <view v-else class="guest-section">
        <image class="guest-logo" mode="aspectFit" src="https://cos.cnptec.site/static/logo.png" />
        <text class="guest-text">登录后查看完整功能</text>
        <view class="guest-btn" @tap="goLogin">
          <text class="guest-btn-text">立即登录</text>
        </view>
      </view>

      <view class="block">
        <view class="settings">
          <view
            v-for="item in visibleServiceList"
            :key="item.key"
            class="setting"
            @tap="onServiceTap(item)"
          >
            <image class="setting-icon" mode="aspectFit" :src="item.iconPath" />
            <text class="setting-name">{{ item.label }}</text>
            <view v-if="item.key === 'messages' && unreadMessageCount > 0" class="message-badge">
              <text class="message-badge-text">{{ unreadMessageCountText }}</text>
            </view>
            <text class="setting-arrow">›</text>
          </view>
          <view
            v-for="item in visibleSettingList"
            :key="item.key"
            class="setting"
            @tap="onSettingTap(item)"
          >
            <image class="setting-icon" mode="aspectFit" :src="item.iconPath" />
            <text class="setting-name">{{ item.label }}</text>
            <text class="setting-arrow">›</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getCurrentUserProfile } from '../../../api/user'
import { getUnreadNotificationCount } from '../../../api/notification'
import {
  connectRealtimeSocket,
  disconnectRealtimeSocket,
  subscribeRealtime
} from '../../../utils/realtime'
import { serviceList, settingList } from './modules/me-data'

const { statusBarHeight = 0 } = uni.getSystemInfoSync()

const isLoggedIn = ref(false)
const currentUser = ref({})
const unreadMessageCount = ref(0)

const DEFAULT_AVATAR = 'https://cos.cnptec.site/static/logo.png'

const displayAvatar = computed(() => {
  const avatar = currentUser.value?.avatar_url?.trim() || ''
  return avatar || DEFAULT_AVATAR
})

const isVerified = computed(() => {
  return isTruthyValue(currentUser.value?.is_verified)
    || isTruthyValue(currentUser.value?.real_name_verified)
    || Boolean(String(currentUser.value?.verified_real_name || '').trim())
})

const visibleServiceList = computed(() => {
  return serviceList
    .filter((item) => {
      if (item.key === 'auth') return !isVerified.value
      if (item.key === 'member_center') return isMemberOpened.value
      if (item.key === 'income') return isCircleOwner.value
      return true
    })
    .map((item) => {
      if (item.key !== 'create_circle') {
        return item
      }
      if (Boolean(currentUser.value?.is_circle_owner)) {
        return {
          ...item,
          label: '创建圈子',
          url: '/pages/circles/create/index'
        }
      }
      return {
        ...item,
        label: '成为圈主',
        url: '/pages/me/circle-owner/apply/index'
      }
    })
})

const visibleSettingList = computed(() => {
  return settingList.filter((item) => item.key !== 'account-security')
})

const displayName = computed(() => {
  return currentUser.value?.nickname?.trim() || '圈脉用户'
})

const displayUserId = computed(() => {
  const id = currentUser.value?.userId || currentUser.value?.user_id
  return id ? String(id) : '--'
})

const displayIntro = computed(() => {
  return currentUser.value?.intro?.trim() || '一句话介绍你的行业、资源与合作方向，让更多合适的人脉主动找到你'
})

const isIntroEmpty = computed(() => {
  return !currentUser.value?.intro?.trim()
})

const displayCircleCount = computed(() => {
  const count = currentUser.value?.circle_count
  return typeof count === 'number' ? String(count) : '--'
})

const displayCollectionCount = computed(() => {
  const info = currentUser.value || {}
  const collectionParts = [
    info.network_interest_count,
    info.resource_interest_count,
    info.circle_interest_count
  ]
  const hasCompleteParts = collectionParts.every((value) => {
    const numericValue = Number(value)
    return value !== null && value !== undefined && value !== '' && Number.isFinite(numericValue)
  })

  if (hasCompleteParts) {
    return String(collectionParts.reduce((total, value) => total + Number(value), 0))
  }

  const fallbackCount = info.interest_count
    ?? info.interested_count
    ?? info.follow_favorite_count
    ?? info.favorite_count
    ?? info.collect_count
  const numericCount = Number(fallbackCount)
  return Number.isFinite(numericCount) && numericCount >= 0 ? String(numericCount) : '0'
})

const displayFansCount = computed(() => {
  const count = currentUser.value?.fans_count ?? currentUser.value?.follower_count
  return typeof count === 'number' ? String(count) : '0'
})

const displayActivityCount = computed(() => {
  const count = currentUser.value?.activity_count ?? currentUser.value?.event_count
  return typeof count === 'number' ? String(count) : '--'
})

const unreadMessageCountText = computed(() => {
  const count = unreadMessageCount.value
  if (count === 0) return '--'
  if (count > 99) return '99+'
  return String(count)
})

const isTruthyValue = (value) => {
  if (typeof value === 'boolean') return value
  if (typeof value === 'number') return value === 1
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    return ['1', 'true', 'yes', 'active'].includes(normalized)
  }
  return false
}

const isMemberOpened = computed(() => {
  const info = currentUser.value || {}
  const directFlags = [
    info.is_member,
    info.member_opened,
    info.is_vip,
    info.vip_opened
  ]
  if (directFlags.some((flag) => isTruthyValue(flag))) return true

  const statusText = String(info.member_status || info.vip_status || '').trim().toLowerCase()
  if (['active', 'opened', 'member', 'vip', 'paid'].includes(statusText)) return true

  const expireAtRaw = info.member_expire_at || info.vip_expire_at
  if (expireAtRaw) {
    const expireTs = new Date(String(expireAtRaw).replace(' ', 'T')).getTime()
    if (Number.isFinite(expireTs) && expireTs > Date.now()) return true
  }

  return false
})

const isYearlyMemberOpened = computed(() => {
  if (!isMemberOpened.value) return false
  const info = currentUser.value || {}
  const planId = String(info.member_plan_id || info.plan_id || info.vip_plan_id || '').trim().toLowerCase()
  return planId === 'yearly'
})

const identityBadges = computed(() => {
  const badges = []
  if (isVerified.value) {
    badges.push({
      key: 'verified',
      icon: 'https://cos.cnptec.site/static/icon/certification.png'
    })
  }
  if (isMemberOpened.value) {
    badges.push({
      key: 'member',
      icon: 'https://cos.cnptec.site/static/icon/mennber1.png'
    })
  }
  if (isCircleOwner.value) {
    badges.push({
      key: 'circle-owner',
      icon: 'https://cos.cnptec.site/static/icon/leader.png?v=20260623'
    })
  }
  return badges
})

const showMemberCenter = computed(() => {
  return isLoggedIn.value && !isMemberOpened.value
})

const isCircleOwner = computed(() => {
  return isTruthyValue(currentUser.value?.is_circle_owner)
})

const clearLoginState = () => {
  disconnectRealtimeSocket()
  uni.removeStorageSync('token')
  uni.removeStorageSync('isLoggedIn')
  uni.removeStorageSync('userInfo')
  isLoggedIn.value = false
  currentUser.value = {}
}

const syncLoginState = () => {
  const loginFlag = uni.getStorageSync('isLoggedIn')
  const token = uni.getStorageSync('token')
  let userInfo = uni.getStorageSync('userInfo')

  if (typeof userInfo === 'string') {
    try {
      userInfo = JSON.parse(userInfo)
    } catch (e) {
      userInfo = {}
    }
  }

  const hasLoginFlag = [true, 'true', 1, '1'].includes(loginFlag)
  const hasToken = typeof token === 'string' ? token.trim().length > 0 : Boolean(token)
  const hasUser = userInfo && typeof userInfo === 'object' && Object.keys(userInfo).length > 0

  isLoggedIn.value = hasLoginFlag || hasToken || hasUser
  currentUser.value = isLoggedIn.value && userInfo && typeof userInfo === 'object' ? userInfo : {}
}

const goEditInfo = () => {
  uni.navigateTo({ url: '/pages/me/editInfo/index' })
}

const onIntroTap = () => {
  if (!isIntroEmpty.value) return
  goEditInfo()
}

const goLogin = () => {
  uni.navigateTo({ url: '/pages/auth/login/index' })
}

const goMyCircles = () => {
  uni.navigateTo({ url: '/pages/me/my-circles/index' })
}

const goMyFollowing = () => {
  uni.navigateTo({ url: '/pages/me/following/index' })
}

const goMyFans = () => {
  uni.navigateTo({ url: '/pages/me/followers/index' })
}

const goMyActivities = () => {
  uni.showToast({ title: '我的活动功能开发中', icon: 'none' })
}

const goMessages = () => {
  uni.navigateTo({ url: '/pages/me/messages/index' })
}

const onNeedLogin = () => {
  uni.showToast({ title: '请先登录', icon: 'none' })
}

const onOpenMember = () => {
  uni.navigateTo({ url: '/pages/me/member-center/index' })
}

const onCircleOwnerAction = () => {
  if (!isLoggedIn.value) {
    onNeedLogin()
    return
  }

  if (isCircleOwner.value) {
    uni.navigateTo({ url: '/pages/circles/manage/index' })
  } else {
    if (!isYearlyMemberOpened.value) {
      uni.showModal({
        title: '需要年度会员',
        content: '购买圈主身份前需要先开通年度会员，是否现在前往会员中心？',
        confirmText: '去开通',
        cancelText: '取消',
        success: (res) => {
          if (res?.confirm) {
            uni.navigateTo({ url: '/pages/me/member-center/index?planId=yearly' })
          }
        }
      })
      return
    }
    uni.navigateTo({ url: '/pages/me/circle-owner/apply/index' })
  }
}

const onServiceTap = (item) => {
  if (!isLoggedIn.value) {
    onNeedLogin()
    return
  }

  if (item?.key === 'auth') {
    if (isVerified.value) {
      uni.showModal({
        title: '实名认证',
        content: '您已经实名认证。',
        showCancel: false
      })
      return
    }
    uni.navigateTo({ url: '/pages/me/auth/realname/index' })
    return
  }

  if (item?.url) {
    uni.navigateTo({ url: item.url })
  }
}

const onSettingTap = (item) => {
  if (!isLoggedIn.value) {
    onNeedLogin()
    return
  }

  const urlMap = {
    'account-security': '/pages/me/security/index',
    'help': '/pages/me/help-feedback/index',
    'about': '/pages/me/about/index'
  }

  const url = urlMap[item?.key]
  if (url) {
    uni.navigateTo({ url })
  } else {
    uni.showToast({ title: item?.label || '设置', icon: 'none' })
  }
}

const refreshUserProfileFromServer = async () => {
  const token = uni.getStorageSync('token')
  if (!token) return

  try {
    const profile = await getCurrentUserProfile()
    uni.setStorageSync('isLoggedIn', true)
    uni.setStorageSync('userInfo', profile || {})
    currentUser.value = profile || {}
    isLoggedIn.value = true

    // 加载未读消息数量
    loadUnreadMessageCount()
  } catch (err) {
    if (err?.statusCode === 401) {
      clearLoginState()
    }
  }
}

const loadUnreadMessageCount = async () => {
  try {
    const data = await getUnreadNotificationCount()
    const count = Number(data?.unread_count || data?.count || 0)
    unreadMessageCount.value = count
  } catch (err) {
    console.error('加载未读消息数量失败:', err)
    unreadMessageCount.value = 0
  }
}

const handleRealtimeEvent = (payload) => {
  if (payload?.event !== 'notification.changed') return
  const count = Number(payload?.data?.unread_count)
  if (Number.isFinite(count) && count >= 0) {
    unreadMessageCount.value = count
    return
  }
  loadUnreadMessageCount()
}

const unsubscribeRealtime = subscribeRealtime(handleRealtimeEvent)

syncLoginState()

onShow(() => {
  syncLoginState()
  if (isLoggedIn.value) {
    connectRealtimeSocket()
    refreshUserProfileFromServer()
  }
})

onUnmounted(() => {
  unsubscribeRealtime()
})
</script>

<style scoped>
.page {
  min-height: 100vh;
  background: #f6f6f8;
}

.header {
  position: sticky;
  top: 0;
  z-index: 10;
  background: #ffffff;
  border-bottom: 1rpx solid #e7ecf3;
}

.title {
  display: block;
  height: 88rpx;
  line-height: 88rpx;
  text-align: center;
  font-size: 34rpx;
  font-weight: 600;
  color: #172033;
}

.main {
  padding: 24rpx 32rpx;
  padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
}

/* 用户区域 */
.user-section {
  margin-bottom: 20rpx;
}

.user-card {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 32rpx;
}

.user-top {
  display: flex;
  gap: 20rpx;
  margin-bottom: 24rpx;
}

.avatar {
  width: 112rpx;
  height: 112rpx;
  border-radius: 56rpx;
  background: #f3f6fa;
  flex-shrink: 0;
}

.user-info {
  flex: 1;
  min-width: 0;
  padding-top: 4rpx;
}

.name-line {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-bottom: 8rpx;
}

.name {
  font-size: 32rpx;
  font-weight: 600;
  color: #172033;
}

.id {
  display: block;
  font-size: 24rpx;
  color: #66758a;
  margin-bottom: 4rpx;
}

.identity-badges {
  min-height: 34rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.identity-badge {
  width: 32rpx;
  height: 32rpx;
  flex-shrink: 0;
}

.edit {
  width: 56rpx;
  height: 56rpx;
  border-radius: 28rpx;
  background: #f6f8fc;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.edit-icon {
  width: 40rpx;
  height: 40rpx;
}

.intro {
  padding: 20rpx;
  background: #f6f8fc;
  border-radius: 12rpx;
  margin-bottom: 24rpx;
}

.intro-empty {
  background: #f5f8ff;

}

.intro-text {
  font-size: 26rpx;
  line-height: 38rpx;
  color: #66758a;
}

.intro-empty .intro-text {
  color: #64748b;
}

.stats {
  display: flex;
  border-top: 1rpx solid #e7ecf3;
  padding-top: 24rpx;
}

.stat {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.stat-num {
  font-size: 32rpx;
  font-weight: 600;
  color: #172033;
}

.stat-num-message {
  color: #ef4444;
}

.stat-name {
  font-size: 24rpx;
  color: #66758a;
}

.member-cards {
  display: flex;
  gap: 16rpx;
  margin-top: 16rpx;
}

.member-card {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-radius: 12rpx;
  padding: 32rpx 24rpx;
}

.member-card-content {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
  flex: 1;
}

.member-card-top {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.member-icon {
  width: 40rpx;
  height: 40rpx;
  flex-shrink: 0;
}

.member-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #333;
}

.member-desc {
  font-size: 22rpx;
  color: #999;
  padding-left: 52rpx;
}

.member-arrow {
  font-size: 32rpx;
  color: #999;
  margin-left: 8rpx;
}

/* 未登录 */
.guest-section {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 64rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 32rpx;
}

.guest-logo {
  width: 96rpx;
  height: 96rpx;
  margin-bottom: 20rpx;
  opacity: 0.6;
}

.guest-text {
  font-size: 26rpx;
  color: #66758a;
  margin-bottom: 32rpx;
}

.guest-btn {
  width: 280rpx;
  height: 80rpx;
  background: #2563eb;
  border-radius: 40rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.guest-btn-text {
  font-size: 28rpx;
  font-weight: 500;
  color: #ffffff;
}

/* 功能区块 */
.block {
  margin-bottom: 32rpx;
}

.settings {
  background: #ffffff;
  border-radius: 16rpx;
  overflow: hidden;
}

.setting {
  display: flex;
  align-items: center;
  padding: 28rpx 32rpx;
  border-bottom: 1rpx solid #f3f6fa;
}

.setting:last-child {
  border-bottom: none;
}

.setting-icon {
  width: 36rpx;
  height: 36rpx;
  margin-right: 20rpx;
}

.setting-name {
  flex: 1;
  font-size: 28rpx;
  color: #172033;
}

.setting-arrow {
  font-size: 32rpx;
  color: #cbd5e1;
}

.message-badge {
  min-width: 36rpx;
  height: 36rpx;
  padding: 0 8rpx;
  background: #ef4444;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12rpx;
}

.message-badge-text {
  font-size: 20rpx;
  color: #ffffff;
  font-weight: 500;
  line-height: 1;
}
</style>
