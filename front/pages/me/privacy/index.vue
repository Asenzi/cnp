<template>
  <view class="privacy-page">
    <view class="content-wrap">
      <view class="section-head">
        <text class="section-head-text">资料可见性</text>
      </view>

      <view class="cell cell-border">
        <view class="cell-main">
          <text class="cell-title">手机号可见性</text>
          <text class="cell-subtitle">仅好友可见</text>
        </view>
        <view
          class="switch-wrap"
          :class="{ 'switch-wrap-on': phoneVisibleToFriends }"
          @tap="onToggleBool('phone_visible_to_friends', phoneVisibleToFriends)"
        >
          <view class="switch-dot"></view>
        </view>
      </view>

      <view class="cell cell-border">
        <view class="cell-main">
          <text class="cell-title">真实姓名保护</text>
          <text class="cell-subtitle">对非认证用户隐藏</text>
        </view>
        <view
          class="switch-wrap"
          :class="{ 'switch-wrap-on': protectRealName }"
          @tap="onToggleBool('protect_real_name', protectRealName)"
        >
          <view class="switch-dot"></view>
        </view>
      </view>

      <view class="cell cell-border cell-compact">
        <text class="cell-title">允许通过邮箱找到我</text>
        <view
          class="switch-wrap"
          :class="{ 'switch-wrap-on': allowFindByEmail }"
          @tap="onToggleBool('allow_find_by_email', allowFindByEmail)"
        >
          <view class="switch-dot"></view>
        </view>
      </view>

      <view class="section-head section-gap">
        <text class="section-head-text">互动权限</text>
      </view>

      <view class="cell cell-border cell-click" hover-class="cell-active" @tap="selectFriendRequestScope">
        <view class="cell-main">
          <text class="cell-title">谁可以向我发送好友请求</text>
          <text class="cell-subtitle cell-subtitle-primary">{{ friendRequestScopeLabel }}</text>
        </view>
        <image class="chevron" mode="aspectFit" src="/static/me-icons/chevron-light.png" />
      </view>

      <view class="cell cell-border cell-click" hover-class="cell-active" @tap="selectMessageScope">
        <view class="cell-main">
          <text class="cell-title">私信接收范围</text>
          <text class="cell-subtitle cell-subtitle-primary">{{ messageScopeLabel }}</text>
        </view>
        <image class="chevron" mode="aspectFit" src="/static/me-icons/chevron-light.png" />
      </view>

      <view class="cell cell-border cell-compact">
        <text class="cell-title">允许自动添加好友</text>
        <view
          class="switch-wrap"
          :class="{ 'switch-wrap-on': allowAutoAddFriend }"
          @tap="onToggleBool('allow_auto_add_friend', allowAutoAddFriend)"
        >
          <view class="switch-dot"></view>
        </view>
      </view>

      <view class="section-head section-gap">
        <text class="section-head-text">黑名单</text>
      </view>

      <view class="cell cell-border cell-click" hover-class="cell-active" @tap="openBlockedUsers">
        <view class="cell-left-inline">
          <image class="block-icon" mode="aspectFit" src="/static/me-icons/cancel-slate.png" />
          <text class="cell-title">已屏蔽的用户</text>
        </view>
        <view class="cell-right-inline">
          <text class="cell-count">{{ blockedCount }} 人</text>
          <image class="chevron" mode="aspectFit" src="/static/me-icons/chevron-light.png" />
        </view>
      </view>

      <view class="policy-wrap">
        <text class="policy-text">
          Quan Mai Lian 全脉链 致力于保护您的隐私安全。
          <text>\n</text>
          更新您的设置将立即生效。
        </text>
        <view class="policy-links">
          <text class="policy-link" @tap="showPolicy('隐私政策')">隐私政策</text>
          <text class="policy-link" @tap="showPolicy('服务条款')">服务条款</text>
        </view>
      </view>

      <view class="bottom-space"></view>
    </view>

    <view class="bottom-action">
      <button class="restore-btn" hover-class="restore-btn-active" @tap="restoreDefaults">恢复默认设置</button>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getCurrentUserPrivacySettings, updateCurrentUserPrivacySettings } from '../../../api/user'

const FRIEND_SCOPE_OPTIONS = [
  { label: '所有人', value: 'all' },
  { label: '仅好友的好友', value: 'friends_of_friends' },
  { label: '不允许任何人', value: 'nobody' }
]

const MESSAGE_SCOPE_OPTIONS = [
  { label: '仅好友或联系人', value: 'friends_or_contacts' },
  { label: '所有人', value: 'all' },
  { label: '仅互相关注', value: 'mutual_follow' }
]

const phoneVisibleToFriends = ref(false) // 默认不可见
const protectRealName = ref(true)
const allowFindByEmail = ref(false)
const allowAutoAddFriend = ref(false)
const friendRequestScope = ref('all')
const messageScope = ref('friends_or_contacts')
const blockedCount = ref(0)
const saving = ref(false)

const friendRequestScopeLabel = computed(() => {
  const found = FRIEND_SCOPE_OPTIONS.find((item) => item.value === friendRequestScope.value)
  return found?.label || '所有人'
})

const messageScopeLabel = computed(() => {
  const found = MESSAGE_SCOPE_OPTIONS.find((item) => item.value === messageScope.value)
  return found?.label || '仅好友或联系人'
})

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const applySettings = (payload) => {
  phoneVisibleToFriends.value = Boolean(payload?.phone_visible_to_friends)
  protectRealName.value = Boolean(payload?.protect_real_name ?? true)
  allowFindByEmail.value = Boolean(payload?.allow_find_by_email)
  allowAutoAddFriend.value = Boolean(payload?.allow_auto_add_friend)
  friendRequestScope.value = String(payload?.friend_request_scope || 'all')
  messageScope.value = String(payload?.message_scope || 'friends_or_contacts')
  blockedCount.value = Number(payload?.blocked_count || 0)
}

const loadSettings = async () => {
  try {
    const data = await getCurrentUserPrivacySettings()
    applySettings(data)
  } catch (err) {
    if (err?.statusCode === 401) {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
      return
    }
    showToast(err?.message || '加载隐私设置失败')
  }
}

const saveSettings = async (partialPayload, rollback) => {
  if (saving.value) {
    return
  }
  saving.value = true
  try {
    const data = await updateCurrentUserPrivacySettings(partialPayload)
    applySettings(data)
  } catch (err) {
    if (typeof rollback === 'function') {
      rollback()
    }
    if (err?.statusCode === 401) {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
      return
    }
    showToast(err?.message || '保存失败，请稍后重试')
  } finally {
    saving.value = false
  }
}

const onToggleBool = (field, stateRef) => {
  if (saving.value) {
    return
  }
  const prev = Boolean(stateRef.value)
  const next = !prev
  stateRef.value = next
  saveSettings(
    {
      [field]: next
    },
    () => {
      stateRef.value = prev
    }
  )
}

const selectFriendRequestScope = () => {
  if (saving.value) {
    return
  }
  uni.showActionSheet({
    itemList: FRIEND_SCOPE_OPTIONS.map((item) => item.label),
    success: (res) => {
      const index = Number(res?.tapIndex ?? -1)
      if (index < 0 || index >= FRIEND_SCOPE_OPTIONS.length) {
        return
      }
      const next = FRIEND_SCOPE_OPTIONS[index].value
      const prev = friendRequestScope.value
      if (next === prev) {
        return
      }
      friendRequestScope.value = next
      saveSettings(
        { friend_request_scope: next },
        () => {
          friendRequestScope.value = prev
        }
      )
    }
  })
}

const selectMessageScope = () => {
  if (saving.value) {
    return
  }
  uni.showActionSheet({
    itemList: MESSAGE_SCOPE_OPTIONS.map((item) => item.label),
    success: (res) => {
      const index = Number(res?.tapIndex ?? -1)
      if (index < 0 || index >= MESSAGE_SCOPE_OPTIONS.length) {
        return
      }
      const next = MESSAGE_SCOPE_OPTIONS[index].value
      const prev = messageScope.value
      if (next === prev) {
        return
      }
      messageScope.value = next
      saveSettings(
        { message_scope: next },
        () => {
          messageScope.value = prev
        }
      )
    }
  })
}

const openBlockedUsers = () => {
  uni.navigateTo({
    url: '/pages/me/privacy/blocked/index'
  })
}

const showPolicy = (name) => {
  showToast(name)
}

const restoreDefaults = () => {
  if (saving.value) {
    return
  }

  const prev = {
    phone_visible_to_friends: phoneVisibleToFriends.value,
    protect_real_name: protectRealName.value,
    allow_find_by_email: allowFindByEmail.value,
    friend_request_scope: friendRequestScope.value,
    message_scope: messageScope.value,
    allow_auto_add_friend: allowAutoAddFriend.value,
    blocked_count: blockedCount.value
  }

  const defaults = {
    phone_visible_to_friends: false, // 默认不可见
    protect_real_name: true,
    allow_find_by_email: false,
    friend_request_scope: 'all',
    message_scope: 'friends_or_contacts',
    allow_auto_add_friend: false,
    blocked_count: blockedCount.value
  }

  applySettings(defaults)
  saveSettings(defaults, () => {
    applySettings(prev)
  })
}

onShow(() => {
  loadSettings()
})
</script>

<style scoped>
.privacy-page {
  min-height: 100vh;
  background: #f8f6f6;
  color: #0f172a;
}

.content-wrap {
  padding-bottom: calc(98px + env(safe-area-inset-bottom));
}

.section-head {
  padding: 16px 16px;
}

.section-gap {
  margin-top: 12px;
}

.section-head-text {
  color: #64748b;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.cell {
  min-height: 72px;
  padding: 10px 16px;
  box-sizing: border-box;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
}

.cell-compact {
  min-height: 64px;
}

.cell-border {
  border-bottom: 1px solid #f1f5f9;
}

.cell-click {
  transition: background-color 0.2s ease;
}

.cell-active {
  background: #f8fafc;
}

.cell-main {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 0;
  flex: 1;
}

.cell-title {
  color: #0f172a;
  font-size: 16px;
  font-weight: 500;
}

.cell-subtitle {
  color: #64748b;
  font-size: 12px;
}

.cell-subtitle-primary {
  color: #1a57db;
  font-weight: 500;
}

.switch-wrap {
  width: 48px;
  height: 28px;
  border-radius: 999px;
  padding: 2px;
  box-sizing: border-box;
  background: #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: flex-start;
  transition: background-color 0.2s ease, justify-content 0.2s ease;
  flex-shrink: 0;
}

.switch-wrap-on {
  background: #1a57db;
  justify-content: flex-end;
}

.switch-dot {
  width: 24px;
  height: 24px;
  border-radius: 999px;
  background: #ffffff;
  box-shadow: 0 1px 4px rgba(15, 23, 42, 0.18);
}

.chevron {
  width: 20px;
  height: 20px;
  opacity: 0.6;
  flex-shrink: 0;
}

.cell-left-inline {
  display: flex;
  align-items: center;
  gap: 10px;
  min-width: 0;
  flex: 1;
}

.block-icon {
  width: 20px;
  height: 20px;
  opacity: 0.75;
}

.cell-right-inline {
  display: flex;
  align-items: center;
  gap: 4px;
}

.cell-count {
  color: #94a3b8;
  font-size: 14px;
}

.policy-wrap {
  padding: 32px 16px 24px;
  text-align: center;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.policy-text {
  color: #94a3b8;
  font-size: 12px;
  line-height: 1.6;
}

.policy-links {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16px;
}

.policy-link {
  color: #1a57db;
  font-size: 12px;
  font-weight: 600;
  text-decoration: underline;
}

.bottom-space {
  height: 40px;
}

.bottom-action {
  position: fixed;
  left: 0;
  right: 0;
  bottom: 0;
  padding: 12px 16px calc(12px + env(safe-area-inset-bottom));
  box-sizing: border-box;
  background: rgba(255, 255, 255, 0.8);
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: center;
}

.restore-btn {
  height: 42px;
  border-radius: 999px;
  padding: 0 26px;
  background: rgba(26, 87, 219, 0.1);
  color: #1a57db;
  font-size: 14px;
  font-weight: 700;
  border: 0;
}

.restore-btn-active {
  opacity: 0.85;
}

@media (prefers-color-scheme: dark) {
  .privacy-page {
    background: #221610;
    color: #f8fafc;
  }

  .cell {
    background: #2a1b14;
  }

  .cell-border {
    border-bottom-color: #3a261d;
  }

  .cell-active {
    background: rgba(26, 87, 219, 0.08);
  }

  .cell-title {
    color: #f8fafc;
  }

  .cell-subtitle,
  .cell-count,
  .section-head-text,
  .policy-text {
    color: #c4b5a9;
  }

  .switch-wrap {
    background: #5b463b;
  }

  .switch-wrap-on {
    background: #1a57db;
  }

  .bottom-action {
    background: rgba(34, 22, 16, 0.84);
    border-top-color: #3a261d;
  }
}
</style>
