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
                <image v-if="isVerified" class="badge" mode="aspectFit" src="https://cos.cnptec.site/static/icon/certification.png" />
              </view>
              <text class="id">ID: {{ displayUserId }}</text>
              <text class="meta">{{ displayMeta }}</text>
            </view>
            <view class="edit" @tap="goEditInfo">
              <image class="edit-icon" mode="aspectFit" src="https://cos.cnptec.site/static/icon/edit.png" />
            </view>
          </view>

          <view v-if="displayIntro" class="intro">
            <text class="intro-text">{{ displayIntro }}</text>
          </view>

          <view class="stats">
            <view class="stat" @tap="goMyFollowing">
              <text class="stat-num">{{ displayFollowingCount }}</text>
              <text class="stat-name">关注</text>
            </view>
            <view class="stat" @tap="goMyFans">
              <text class="stat-num">{{ displayFansCount }}</text>
              <text class="stat-name">粉丝</text>
            </view>
            <view class="stat" @tap="goMyActivities">
              <text class="stat-num">{{ displayActivityCount }}</text>
              <text class="stat-name">活动</text>
            </view>
            <view class="stat" @tap="goMyCircles">
              <text class="stat-num">{{ displayCircleCount }}</text>
              <text class="stat-name">圈子</text>
            </view>
          </view>
        </view>

        <!-- 会员提示 -->
        <view v-if="showMemberCenter" class="member-tip" @tap="onOpenMember">
          <text class="member-text">开通会员，解锁更多权益</text>
          <text class="member-arrow">›</text>
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
            v-for="item in settingList"
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
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getCurrentUserProfile } from '../../../api/user'
import { getUnreadNotificationCount } from '../../../api/notification'
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
  return Boolean(currentUser.value?.is_verified || currentUser.value?.real_name_verified)
})

const visibleServiceList = computed(() => {
  return serviceList
    .filter((item) => item.key !== 'auth' || !isVerified.value)
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

const displayName = computed(() => {
  return currentUser.value?.nickname?.trim() || '圈脉用户'
})

const displayUserId = computed(() => {
  const id = currentUser.value?.userId || currentUser.value?.user_id
  return id ? String(id) : '--'
})

const displayMeta = computed(() => {
  const parts = []
  if (currentUser.value?.job_title) parts.push(currentUser.value.job_title)
  if (currentUser.value?.company_name) parts.push(currentUser.value.company_name)
  return parts.join(' · ') || '完善资料，展示专业形象'
})

const displayIntro = computed(() => {
  return currentUser.value?.intro?.trim() || ''
})

const displayCircleCount = computed(() => {
  const count = currentUser.value?.circle_count
  return typeof count === 'number' ? String(count) : '--'
})

const displayFollowingCount = computed(() => {
  const count = currentUser.value?.following_count ?? currentUser.value?.follow_count
  return typeof count === 'number' ? String(count) : '0'
})

const displayFansCount = computed(() => {
  const count = currentUser.value?.fans_count ?? currentUser.value?.follower_count
  return typeof count === 'number' ? String(count) : '0'
})

const displayActivityCount = computed(() => {
  const count = currentUser.value?.activity_count ?? currentUser.value?.event_count
  return typeof count === 'number' ? String(count) : '--'
})

const displayInterestCount = computed(() => {
  const info = currentUser.value || {}
  const count = info.follow_favorite_count
    ?? info.favorite_count
    ?? info.collect_count
    ?? info.interest_count
    ?? info.interested_count
  const numericCount = Number(count)
  return Number.isFinite(numericCount) && numericCount >= 0 ? String(numericCount) : '0'
})

const displayBalance = computed(() => {
  const balance = currentUser.value?.balance
  if (typeof balance === 'number') {
    return `¥${balance.toFixed(2)}`
  }
  return '¥0.00'
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

const showMemberCenter = computed(() => {
  return isLoggedIn.value && !isMemberOpened.value
})

let walletNavigating = false

const clearLoginState = () => {
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

const goWallet = () => {
  if (walletNavigating) return
  walletNavigating = true
  uni.navigateTo({
    url: '/pages/me/wallet/index',
    complete: () => {
      setTimeout(() => {
        walletNavigating = false
      }, 400)
    }
  })
}

const goInterests = () => {
  uni.navigateTo({ url: '/pages/me/interests/index' })
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

syncLoginState()

onShow(() => {
  syncLoginState()
  if (isLoggedIn.value) {
    refreshUserProfileFromServer()
  }
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

.badge {
  width: 32rpx;
  height: 32rpx;
}

.id {
  display: block;
  font-size: 24rpx;
  color: #66758a;
  margin-bottom: 4rpx;
}

.meta {
  display: block;
  font-size: 26rpx;
  color: #66758a;
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

.intro-text {
  font-size: 26rpx;
  line-height: 38rpx;
  color: #66758a;
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

.member-tip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #1296db;
  border-radius: 12rpx;
  padding: 43rpx 28rpx;
  margin-top: 16rpx;
}

.member-text {
  font-size: 26rpx;
  color: #fff;
}

.member-arrow {
  font-size: 32rpx;
  color: #fff;
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
