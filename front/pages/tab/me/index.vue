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
                <image v-if="isVerified" class="badge" mode="aspectFit" src="/static/icon/certification.png" />
              </view>
              <text class="id">ID: {{ displayUserId }}</text>
              <text class="meta">{{ displayMeta }}</text>
            </view>
            <view class="edit" @tap="goEditInfo">
              <image class="edit-icon" mode="aspectFit" src="/static/icon/edit.png" />
            </view>
          </view>

          <view v-if="displayIntro" class="intro">
            <text class="intro-text">{{ displayIntro }}</text>
          </view>

          <view class="stats">
            <view class="stat" @tap="goMyCircles">
              <text class="stat-num">{{ displayCircleCount }}</text>
              <text class="stat-name">圈子</text>
            </view>
            <view class="stat" @tap="goInterests">
              <text class="stat-num">{{ displayInterestCount }}</text>
              <text class="stat-name">感兴趣</text>
            </view>
            <view class="stat" @tap="goWallet">
              <text class="stat-num">{{ displayBalance }}</text>
              <text class="stat-name">余额</text>
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
        <image class="guest-logo" mode="aspectFit" src="/static/logo.png" />
        <text class="guest-text">登录后查看完整功能</text>
        <view class="guest-btn" @tap="goLogin">
          <text class="guest-btn-text">立即登录</text>
        </view>
      </view>

      <!-- 功能 -->
      <view class="block">
        <text class="block-title">功能服务</text>
        <view class="services">
          <view
            v-for="item in serviceList"
            :key="item.key"
            class="service"
            @tap="onServiceTap(item)"
          >
            <image class="service-icon" mode="aspectFit" :src="item.iconPath" />
            <text class="service-name">{{ item.label }}</text>
          </view>
        </view>
      </view>

      <!-- 设置 -->
      <view class="block">
        <text class="block-title">系统设置</text>
        <view class="settings">
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
import { serviceList, settingList } from './modules/me-data'

const { statusBarHeight = 0 } = uni.getSystemInfoSync()

const isLoggedIn = ref(false)
const currentUser = ref({})

const DEFAULT_AVATAR = '/static/logo.png'

const displayAvatar = computed(() => {
  const avatar = currentUser.value?.avatar_url?.trim() || ''
  return avatar || DEFAULT_AVATAR
})

const isVerified = computed(() => {
  return Boolean(currentUser.value?.is_verified || currentUser.value?.real_name_verified)
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

const displayInterestCount = computed(() => {
  return '--'
})

const displayBalance = computed(() => {
  const balance = currentUser.value?.balance
  if (typeof balance === 'number') {
    return `¥${balance.toFixed(2)}`
  }
  return '¥0.00'
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
  } catch (err) {
    if (err?.statusCode === 401) {
      clearLoginState()
    }
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
  margin-bottom: 32rpx;
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
  width: 28rpx;
  height: 28rpx;
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

.stat-name {
  font-size: 24rpx;
  color: #66758a;
}

.member-tip {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff9f5;
  border-radius: 12rpx;
  padding: 24rpx 28rpx;
  margin-top: 16rpx;
}

.member-text {
  font-size: 26rpx;
  color: #d4a574;
}

.member-arrow {
  font-size: 32rpx;
  color: #d4a574;
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

.block-title {
  display: block;
  font-size: 28rpx;
  font-weight: 600;
  color: #172033;
  margin-bottom: 16rpx;
}

.services {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20rpx;
  background: #ffffff;
  border-radius: 16rpx;
  padding: 28rpx 20rpx;
}

.service {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}

.service-icon {
  width: 80rpx;
  height: 80rpx;
}

.service-name {
  font-size: 24rpx;
  color: #172033;
  text-align: center;
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
</style>
