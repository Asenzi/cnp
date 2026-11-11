<template><view class="page"><view class="main"><view v-if="isLoggedIn" class="profile-card"><view class="user-top"><image class="avatar" :src="displayAvatar" mode="aspectFill"/><view class="profile-details"><view class="user-info"><view class="name-line"><text class="name">{{displayName}}</text><view v-if="identityBadges.length" class="identity-badges"><view v-for="badge in identityBadges" :key="badge.key" class="identity-tag"><image :src="badge.icon" mode="aspectFit"/><text>{{ badge.label }}</text></view></view></view><view class="id-row"><text class="id" @tap="copyUserId">用户ID：{{displayUserId}}</text><image class="copy-icon" src="/static/me-reference/copy.png" @tap="copyUserId"/></view></view><view class="actions"><button @tap="goEditInfo"><image mode="aspectFit" src="/static/me-reference/edit.png"/>编辑名片</button><button open-type="share"><image mode="aspectFit" src="/static/me-reference/share.png"/>分享名片</button></view></view></view><view class="membership" @tap="onOpenMember"><image class="crown" mode="aspectFit" src="/static/me-reference/crown.png"/><view class="member-copy"><text class="member-title">{{isMemberOpened ? '钻石会员' : '开通会员'}}</text><text class="member-desc">解锁资源下载、发布、分销等全部权益</text></view><view v-if="isMemberOpened" class="expiry"><text>有效期至</text><text>{{memberExpiry}}</text></view></view><view class="stats"><view class="stat" @tap="goMyFollowing"><image mode="aspectFit" src="/static/me-reference/star.png"/><text>我的收藏</text></view><view class="stat" @tap="goMyCircles"><image mode="aspectFit" src="/static/me-reference/circles-stat.png"/><text>我的圈子</text></view><view class="stat" @tap="goMessages"><view class="stat-icon"><image mode="aspectFit" src="/static/me-reference/bell.png"/><text v-if="unreadMessageCount > 0" class="unread-badge">{{ unreadMessageCount > 99 ? '99+' : unreadMessageCount }}</text></view><text>我的消息</text></view><view class="stat" @tap="goWallet"><image mode="aspectFit" src="/static/me-reference/wallet.png"/><text>我的钱包</text></view></view></view><view v-else class="guest"><image class="avatar" :src="displayAvatar"/><text>登录后查看完整功能</text><button @tap="goLogin">立即登录</button></view><ManagementMenu class="management" :items="settingList" @select="onSettingTap"/><button class="publish" @tap="goPublish"><image class="publish-icon" src="/static/me-reference/plus.png"/>发布资源</button></view></view><canvas id="myProfileShareCanvas" type="2d" canvas-id="myProfileShareCanvas" style="position:fixed;left:-9999px;top:-9999px;width:750px;height:600px;" /></template>
<script setup>

import { computed, onUnmounted, ref } from 'vue'
import { generateProfileShareImage } from '../../../utils/profile-share-image'
import { onShow, onShareAppMessage } from '@dcloudio/uni-app'
import { getCurrentUserProfile } from '../../../api/user'
import { getUnreadNotificationCount } from '../../../api/notification'
import { getIncomeOverview } from '../../../api/settlement'
import {
  connectRealtimeSocket,
  disconnectRealtimeSocket,
  subscribeRealtime
} from '../../../utils/realtime'
import ManagementMenu from './components/ManagementMenu.vue'
import { buildIdentityBadges } from './modules/identity-badges'
import { settingList } from './modules/me-data'

const isLoggedIn = ref(false)
const currentUser = ref({})
const unreadMessageCount = ref(0)
const walletBalance = ref(null)

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



const displayName = computed(() => {
  return currentUser.value?.nickname?.trim() || '圈脉用户'
})

const displayUserId = computed(() => {
  const id = currentUser.value?.userId || currentUser.value?.user_id
  return id ? String(id) : '--'
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


const displayWalletBalance = computed(() => walletBalance.value === null ? '--' : `¥${Number(walletBalance.value).toFixed(2)}`)


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



const isCircleOwner = computed(() => {
  return isTruthyValue(currentUser.value?.is_circle_owner)
})

const identityBadges = computed(() => buildIdentityBadges(currentUser.value, isVerified.value, isCircleOwner.value))

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

const goLogin = () => {
  uni.navigateTo({ url: '/pages/auth/login/index' })
}

const goMyCircles = () => {
  uni.navigateTo({ url: '/pages/me/my-circles/index' })
}

const goMyFollowing = () => {
  uni.navigateTo({ url: '/pages/me/following/index' })
}

const goWallet = () => {
  uni.navigateTo({ url: '/pages/me/income/index' })
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
    uni.navigateTo({ url: '/pages/me/circle-owner/apply/index' })
  }
}

const onLogout = () => {
  uni.showModal({
    title: '退出登录',
    content: '确定退出当前账号吗？',
    confirmText: '退出登录',
    cancelText: '取消',
    confirmColor: '#ef4444',
    success: (res) => {
      if (!res?.confirm) {
        return
      }
      clearLoginState()
      unreadMessageCount.value = 0
      uni.showToast({ title: '已退出登录', icon: 'none' })
    }
  })
}

const onSettingTap = (item) => {
  if (!isLoggedIn.value) {
    onNeedLogin()
    return
  }

  if (item?.key === 'logout') {
    onLogout()
    return
  }

  const urlMap = {
    'resources': '/pages/resources/manage/index',
    'circles': '/pages/circles/manage/index',
    'distribution': '/pages/me/income/index',
    'account-security': '/pages/me/security/index',
    'profile-card': '/pages/me/card/index',
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

    void prepareMyShareImage()
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

const loadWalletBalance = async () => {
  try {
    const data = await getIncomeOverview({ limit: 1 })
    const balance = Number(data?.account?.available_balance)
    walletBalance.value = Number.isFinite(balance) ? balance : null
  } catch (err) {
    walletBalance.value = null
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
    void prepareMyShareImage()
    connectRealtimeSocket()
    refreshUserProfileFromServer()
    loadWalletBalance()
  } else {
    walletBalance.value = null
  }
})

onUnmounted(() => {
  unsubscribeRealtime()
})

const memberExpiry = computed(() => String(currentUser.value?.member_expire_at || currentUser.value?.vip_expire_at || '').slice(0, 10) || '未开通')
const myShareImage = ref('')
let myShareKey = ''
let myShareTask = Promise.resolve('')
const prepareMyShareImage = () => {
  if (!isLoggedIn.value || displayUserId.value === '--') return Promise.resolve('')
  const profile = currentUser.value || {}
  const data = {
    nickname: displayName.value,
    avatarUrl: displayAvatar.value,
    company: String(profile.company_name || profile.company || '').trim(),
    jobTitle: String(profile.job_title || profile.position || '').trim(),
    bio: String(profile.intro || '').trim(),
    isVerified: isVerified.value,
    isMember: isMemberOpened.value,
    isCircleOwner: isCircleOwner.value
  }
  const key = JSON.stringify([displayUserId.value, data])
  if (myShareKey === key) return myShareTask
  myShareKey = key
  myShareImage.value = ''
  myShareTask = myShareTask.catch(() => '').then(async () => {
    try {
      const image = await generateProfileShareImage(data, {canvasId:'myProfileShareCanvas'})
      if (myShareKey === key) myShareImage.value = image
      return image
    } catch (error) {
      if (myShareKey === key) myShareKey = ''
      console.error('生成个人名片分享图失败', error)
      uni.showToast({title:'分享图生成失败，请稍后重试',icon:'none'})
      return data.avatarUrl || ''
    }
  })
  return myShareTask
}
onShareAppMessage(() => {
  const share = {
    title: `${displayName.value}的个人名片`,
    path: `/pages/me/card/index?userId=${encodeURIComponent(displayUserId.value)}`,
    imageUrl: myShareImage.value || displayAvatar.value
  }
  return {...share, promise:prepareMyShareImage().then(imageUrl => ({...share, imageUrl}))}
})
const copyUserId = () => uni.setClipboardData({ data: displayUserId.value })
const goPublish = () => { if (!isLoggedIn.value) return onNeedLogin(); uni.navigateTo({ url: '/pages/resources/publish/index' }) }

</script>
<style scoped>
.page{min-height:100vh;background:#f7f8fc;color:#090b20}.main{padding:16rpx 18rpx 90rpx}.profile-card{background:#fff;border-radius:10rpx;padding:26rpx 17rpx 30rpx}.user-top{display:flex;align-items:center;gap:20rpx;min-height:120rpx}.profile-details{flex:1;min-width:0;display:flex;flex-direction:column;gap:16rpx}.user-info{display:flex;flex-direction:column;gap:16rpx}.avatar{width:120rpx;height:120rpx;border-radius:50%;flex-shrink:0}.user-info{flex:1;min-width:0}.name-line{display:flex;align-items:center;gap:8rpx}.name{font-size:32rpx;font-weight:600;line-height:40rpx}.badge{width:28rpx;height:28rpx}.id{display:block;font-size:24rpx;color:#77798d;margin-top:0;line-height:34rpx}.actions{display:flex;justify-content:flex-start;gap:10rpx;width:100%}.actions button{display:flex;align-items:center;gap:6rpx;height:50rpx;line-height:38rpx;border:2rpx solid #d3dcff;border-radius:8rpx;background:#fff;padding:0 14rpx;font-size:24rpx;margin:0}.actions image{width:28rpx;height:28rpx}button::after{border:0}.membership{display:flex;align-items:center;background:#f0f4ff;border-radius:22rpx;margin-top:24rpx;padding:22rpx 20rpx;gap:20rpx;min-height:66rpx}.crown{width:62rpx;height:55rpx;flex-shrink:0}.member-copy{flex:1;min-width:0}.member-title{display:block;font-size:28rpx;font-weight:600;line-height:40rpx}.member-desc{display:block;font-size:24rpx;color:#6e748a;margin-top:6rpx;white-space:nowrap;line-height:34rpx}.expiry{display:flex;flex-direction:column;align-items:center;border-left:1rpx solid #cbd6f4;padding-left:24rpx;font-size:24rpx;color:#4262a7;gap:6rpx;line-height:34rpx}.expiry text:last-child{font-size:26rpx;line-height:36rpx}.stats{display:flex;margin-top:36rpx}.stat{flex:1;display:flex;align-items:center;flex-direction:column;gap:8rpx;font-size:24rpx;color:#76798b;line-height:34rpx}.stat+.stat{border-left:1rpx solid #e6e8f0;font-size:24rpx;line-height:34rpx}.stat image,.stat-icon{width:44rpx;height:40rpx}.stat-icon{position:relative}.unread-badge{position:absolute;right:-16rpx;top:-12rpx;min-width:28rpx;height:28rpx;padding:0 6rpx;box-sizing:border-box;border:3rpx solid #fff;border-radius:18rpx;background:#f04444;color:#fff;font-size:20rpx;font-weight:600;line-height:22rpx;text-align:center;white-space:nowrap;z-index:1}.management{display:block;margin-top:20rpx}.publish{margin-top:36rpx;height:78rpx;line-height:78rpx;border-radius:22rpx;background:#1c5cf3;color:#fff;font-size:28rpx;font-weight:600}.guest{display:flex;align-items:center;flex-direction:column;gap:24rpx;padding:36rpx;background:#fff;border-radius:24rpx}.guest{font-size:26rpx;line-height:38rpx}.guest button{background:#1c5cf3;color:#fff}
.id-row{display:flex;align-items:center;gap:12rpx;margin-top:0}.id-row .id{margin-top:0;font-size:24rpx;line-height:34rpx}.copy-icon{width:28rpx;height:28rpx}.publish{display:flex;align-items:center;justify-content:center;gap:16rpx;font-size:28rpx}.publish-icon{width:43rpx;height:43rpx}.stat image{object-fit:contain}
.name-line{flex-wrap:wrap;row-gap:8rpx}.identity-badges{display:flex;flex-wrap:wrap;align-items:center;gap:8rpx}.identity-tag{display:flex;align-items:center;gap:4rpx;padding:2rpx 8rpx;border-radius:16rpx;background:#edf3ff;color:#3d6fdf;font-size:24rpx;line-height:32rpx}.identity-tag image{width:26rpx;height:26rpx;flex-shrink:0}
</style>
