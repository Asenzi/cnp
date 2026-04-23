<template>
  <view class="me-page">
    <view class="page-shell">
      <view class="header" :style="headerStyle">
        <text class="header-title">我的</text>
      </view>

      <view class="main">
        <MeTopLogged
          v-if="isLoggedIn"
          :user-info="currentUser"
          :with-member-card="showMemberCenter"
          @edit="goEditInfo"
          @open-circles="goMyCircles"
          @open-wallet="goWallet"
        />
        <MeTopGuest v-else @login="goLogin" @open-circles="goMyCircles" />
        <MeMemberCenterCard v-if="showMemberCenter" @open="onOpenMember" />

        <view class="block-wrap">
          <text class="block-title">功能服务</text>
          <MeServiceGrid :items="serviceList" @tap-item="onServiceTap" />
        </view>

        <view class="block-wrap">
          <text class="block-title">系统设置</text>
          <MeSettingList :items="settingList" @tap-item="onSettingTap" />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import MeMemberCenterCard from './components/MeMemberCenterCard.vue'
import MeServiceGrid from './components/MeServiceGrid.vue'
import MeSettingList from './components/MeSettingList.vue'
import MeTopGuest from './components/MeTopGuest.vue'
import MeTopLogged from './components/MeTopLogged.vue'
import { getCurrentUserProfile } from '../../../api/user'
import { serviceList, settingList } from './modules/me-data'

const { statusBarHeight = 0 } = uni.getSystemInfoSync()
const headerStyle = `padding-top:${statusBarHeight}px;`

const isLoggedIn = ref(false)
const currentUser = ref({})

const isTruthyValue = (value) => {
  if (typeof value === 'boolean') {
    return value
  }
  if (typeof value === 'number') {
    return value === 1
  }
  if (typeof value === 'string') {
    const normalized = value.trim().toLowerCase()
    return normalized === '1' || normalized === 'true' || normalized === 'yes' || normalized === 'active'
  }
  return false
}

const isMemberOpened = computed(() => {
  const info = currentUser.value || {}
  const directFlags = [
    info.is_member,
    info.member_opened,
    info.is_vip,
    info.vip_opened,
    info.premium,
    info.pro_member
  ]
  if (directFlags.some((flag) => isTruthyValue(flag))) {
    return true
  }

  const statusText = String(info.member_status || info.vip_status || '').trim().toLowerCase()
  if (['active', 'opened', 'member', 'vip', 'paid'].includes(statusText)) {
    return true
  }

  const expireAtRaw = info.member_expire_at || info.vip_expire_at
  if (expireAtRaw) {
    const expireTs = new Date(String(expireAtRaw).replace(' ', 'T')).getTime()
    if (Number.isFinite(expireTs) && expireTs > Date.now()) {
      return true
    }
  }

  return false
})

const hasRealNameVerified = computed(() => Boolean(currentUser.value?.is_verified))

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
  const userInfo = uni.getStorageSync('userInfo')

  let parsedUserInfo = userInfo
  if (typeof parsedUserInfo === 'string') {
    try {
      parsedUserInfo = JSON.parse(parsedUserInfo)
    } catch (e) {
      parsedUserInfo = {}
    }
  }

  const hasLoginFlag = loginFlag === true || loginFlag === 'true' || loginFlag === 1 || loginFlag === '1'
  const hasToken = typeof token === 'string' ? token.trim().length > 0 : Boolean(token)
  const hasUser =
    typeof parsedUserInfo === 'object' && parsedUserInfo !== null
      ? Object.keys(parsedUserInfo).length > 0
      : Boolean(parsedUserInfo)

  isLoggedIn.value = hasLoginFlag || hasToken || hasUser
  currentUser.value = isLoggedIn.value && parsedUserInfo && typeof parsedUserInfo === 'object' ? parsedUserInfo : {}
}

const goEditInfo = () => {
  uni.navigateTo({
    url: '/pages/me/editInfo/index'
  })
}

const goLogin = () => {
  uni.navigateTo({
    url: '/pages/auth/login/index'
  })
}

const goMyCircles = () => {
  uni.navigateTo({
    url: '/pages/me/my-circles/index'
  })
}

// 积分功能暂时隐藏
// const goPoints = () => {
//   uni.navigateTo({
//     url: '/pages/me/points/index'
//   })
// }

const goWallet = () => {
  if (walletNavigating) {
    return
  }
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

const onNeedLogin = () => {
  uni.showToast({
    title: '请先登录',
    icon: 'none'
  })
}

const onOpenMember = () => {
  uni.navigateTo({
    url: '/pages/me/member-center/index'
  })
}

const onServiceTap = (item) => {
  if (!isLoggedIn.value) {
    onNeedLogin()
    return
  }

  if (item?.key === 'auth') {
    if (hasRealNameVerified.value) {
      uni.showModal({
        title: '实名认证',
        content: '您已经实名认证。',
        showCancel: false
      })
      return
    }

    uni.navigateTo({
      url: '/pages/me/auth/realname/index'
    })
    return
  }

  if (!item?.url) {
    return
  }

  uni.navigateTo({
    url: item.url
  })
}

const onSettingTap = (item) => {
  if (!isLoggedIn.value) {
    onNeedLogin()
    return
  }

  if (item?.key === 'general') {
    uni.navigateTo({
      url: '/pages/me/settings/index'
    })
    return
  }

  if (item?.key === 'bind-phone') {
    uni.navigateTo({
      url: '/pages/me/security/phone/index'
    })
    return
  }

  uni.showToast({
    title: item?.label || '设置',
    icon: 'none'
  })
}

const refreshUserProfileFromServer = async () => {
  const token = uni.getStorageSync('token')
  if (!token) {
    return
  }

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
.me-page {
  min-height: 100vh;
  background: #f6f6f8;
}

.page-shell {
  min-height: 100vh;
  background: #ffffff;
  color: #0f172a;
}

.header {
  position: sticky;
  top: 0;
  z-index: 10;
  padding-left: 32rpx;
  padding-right: 32rpx;
  border-bottom: 1rpx solid #f1f5f9;
  background: #ffffff;
}

.header-title {
  display: block;
  height: 88rpx;
  line-height: 88rpx;
  text-align: center;
  font-size: 36rpx;
  font-weight: 700;
  letter-spacing: 1rpx;
}

.main {
  padding: 24rpx 32rpx;
  padding-bottom: calc(32rpx + env(safe-area-inset-bottom));
}

.block-wrap {
  margin-bottom: 48rpx;
}

.block-title {
  display: block;
  margin-bottom: 24rpx;
  font-size: 32rpx;
  font-weight: 700;
  color: #0f172a;
}

@media (prefers-color-scheme: dark) {
  .me-page {
    background: #111621;
  }

  .page-shell {
    background: #111621;
    color: #f1f5f9;
  }

  .header {
    border-bottom-color: #1e293b;
    background: #111621;
  }

  .header-title,
  .block-title {
    color: #f1f5f9;
  }
}
</style>

