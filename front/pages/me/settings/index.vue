<template>
  <view class="settings-page">
    <view class="page-shell">
      <view class="group-wrap first-group">
        <text class="group-title">账户与安全</text>
        <view class="group-card">
          <view
            v-for="(item, index) in accountSecurityItems"
            :key="item.key"
            class="setting-row"
            :class="{ 'setting-row-border': index < accountSecurityItems.length - 1 }"
            hover-class="setting-row-active"
            @tap="onSettingTap(item)"
          >
            <view class="row-left">
              <view class="row-icon-box">
                <image class="row-icon" mode="aspectFit" :src="item.iconPath" />
              </view>
              <text class="row-label">{{ item.label }}</text>
            </view>
            <view class="row-right">
              <text v-if="item.extraText" class="row-extra">{{ item.extraText }}</text>
              <view v-if="item.showDot" class="row-dot"></view>
              <image class="row-chevron" mode="aspectFit" src="/static/me-icons/chevron-light.png" />
            </view>
          </view>
        </view>
      </view>

      <view class="group-wrap">
        <text class="group-title">系统设置</text>
        <view class="group-card">
          <view
            v-for="(item, index) in systemItems"
            :key="item.key"
            class="setting-row"
            :class="{ 'setting-row-border': index < systemItems.length - 1 }"
            hover-class="setting-row-active"
            @tap="onSettingTap(item)"
          >
            <view class="row-left">
              <view class="row-icon-box">
                <image class="row-icon" mode="aspectFit" :src="item.iconPath" />
              </view>
              <text class="row-label">{{ item.label }}</text>
            </view>
            <view class="row-right">
              <text v-if="item.extraText" class="row-extra">{{ item.extraText }}</text>
              <view v-if="item.showDot" class="row-dot"></view>
              <image class="row-chevron" mode="aspectFit" src="/static/me-icons/chevron-light.png" />
            </view>
          </view>
        </view>
      </view>

      <view class="group-wrap">
        <text class="group-title">其他</text>
        <view class="group-card">
          <view
            v-for="(item, index) in otherItems"
            :key="item.key"
            class="setting-row"
            :class="{ 'setting-row-border': index < otherItems.length - 1 }"
            hover-class="setting-row-active"
            @tap="onSettingTap(item)"
          >
            <view class="row-left">
              <view class="row-icon-box">
                <image class="row-icon" mode="aspectFit" :src="item.iconPath" />
              </view>
              <text class="row-label">{{ item.label }}</text>
            </view>
            <view class="row-right">
              <text v-if="item.extraText" class="row-extra">{{ item.extraText }}</text>
              <view v-if="item.showDot" class="row-dot"></view>
              <image class="row-chevron" mode="aspectFit" src="/static/me-icons/chevron-light.png" />
            </view>
          </view>
        </view>
      </view>

      <view class="logout-wrap">
        <view class="logout-btn" hover-class="logout-btn-active" @tap="onLogout">
          <text class="logout-text">退出登录</text>
        </view>
      </view>

      <view class="brand-wrap">
        <text class="brand-text">圈脉链 Quan Mai Lian v2.4.0</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'

const cacheSizeText = ref('24MB')

const accountSecurityItems = computed(() => [
  {
    key: 'account-security',
    label: '账号与安全',
    iconPath: '/static/me-icons/shield-person-primary.png'
  },
  {
    key: 'privacy',
    label: '隐私设置',
    iconPath: '/static/me-icons/tune-gray.png'
  }
])

const systemItems = computed(() => [
  {
    key: 'general',
    label: '通用设置',
    iconPath: '/static/me-icons/tune-gray.png'
  },
  {
    key: 'clear-cache',
    label: '清除缓存',
    iconPath: '/static/me-icons/cancel-slate.png',
    extraText: cacheSizeText.value
  },
  {
    key: 'about',
    label: '关于圈脉链',
    iconPath: '/static/me-icons/info-gray.png'
  },
  {
    key: 'check-update',
    label: '检查更新',
    iconPath: '/static/me-icons/event-orange.png',
    showDot: true
  }
])

const otherItems = computed(() => [
  {
    key: 'help',
    label: '反馈与帮助',
    iconPath: '/static/me-icons/help-gray.png'
  }
])

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const clearLoginState = () => {
  uni.removeStorageSync('token')
  uni.removeStorageSync('isLoggedIn')
  uni.removeStorageSync('userInfo')
}

const onSettingTap = (item) => {
  if (!item?.key) {
    return
  }

  if (item.key === 'clear-cache') {
    cacheSizeText.value = '0MB'
    showToast('缓存已清理')
    return
  }

  if (item.key === 'account-security') {
    uni.navigateTo({
      url: '/pages/me/security/index'
    })
    return
  }

  if (item.key === 'privacy') {
    uni.navigateTo({
      url: '/pages/me/privacy/index'
    })
    return
  }

  if (item.key === 'check-update') {
    showToast('当前已是最新版本')
    return
  }

  showToast(item.label)
}

const onLogout = () => {
  uni.showModal({
    title: '退出登录',
    content: '确定退出当前账号吗？',
    success: (res) => {
      if (!res?.confirm) {
        return
      }
      clearLoginState()
      showToast('已退出登录')
      setTimeout(() => {
        uni.switchTab({
          url: '/pages/tab/me/index'
        })
      }, 220)
    }
  })
}
</script>

<style scoped>
.settings-page {
  height: 100vh;
  overflow: hidden;
  background: #f6f6f8;
  color: #0f172a;
}

.page-shell {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: #f6f6f8;
  padding-bottom: calc(8px + env(safe-area-inset-bottom));
  box-sizing: border-box;
}

.group-wrap {
  margin-top: 16px;
}

.first-group {
  margin-top: 0;
}

.group-title {
  display: block;
  padding: 8px 16px 8px;
  color: #64748b;
  font-size: 13px;
  font-weight: 500;
  letter-spacing: 0.08em;
}

.group-card {
  background: #ffffff;
  overflow: hidden;
}

.setting-row {
  min-height: 56px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  transition: background-color 0.2s ease;
  box-sizing: border-box;
}

.setting-row-border {
  border-bottom: 1px solid #f8fafc;
}

.setting-row-active {
  background: #f8fafc;
}

.row-left {
  display: flex;
  align-items: center;
  gap: 16px;
  flex: 1;
  min-width: 0;
}

.row-icon-box {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(26, 87, 219, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.row-icon {
  width: 22px;
  height: 22px;
}

.row-label {
  color: #0f172a;
  font-size: 16px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.row-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.row-extra {
  color: #94a3b8;
  font-size: 14px;
}

.row-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #ef4444;
}

.row-chevron {
  width: 20px;
  height: 20px;
}

.logout-wrap {
  margin-top: 28px;
  padding: 0 16px;
}

.logout-btn {
  width: 100%;
  height: 56px;
  border-radius: 12px;
  border: 2px solid #e2e8f0;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 6px rgba(15, 23, 42, 0.06);
}

.logout-btn-active {
  transform: scale(0.99);
}

.logout-text {
  color: #ef4444;
  font-size: 18px;
  font-weight: 700;
}

.brand-wrap {
  margin-top: auto;
  padding-top: 20px;
  text-align: center;
}

.brand-text {
  color: #94a3b8;
  font-size: 12px;
  font-weight: 500;
}

@media (prefers-color-scheme: dark) {
  .settings-page {
    background: #111621;
    color: #f1f5f9;
  }

  .page-shell {
    background: #111621;
  }

  .group-title,
  .row-extra,
  .brand-text {
    color: #94a3b8;
  }

  .group-card,
  .logout-btn {
    background: #0f172a;
  }

  .setting-row-border {
    border-bottom-color: #1e293b;
  }

  .setting-row-active {
    background: #1e293b;
  }

  .row-label {
    color: #f1f5f9;
  }

  .row-icon-box {
    background: rgba(26, 87, 219, 0.2);
  }

  .logout-btn {
    border-color: #1e293b;
    box-shadow: none;
  }
}
</style>
