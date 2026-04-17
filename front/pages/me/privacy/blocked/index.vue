<template>
  <view class="blocked-page">
    <view class="content-wrap">
      <view class="add-card">
        <text class="card-title">添加黑名单</text>
        <text class="card-subtitle">输入用户 ID（8 位）后加入黑名单</text>

        <view class="add-row">
          <input
            v-model="targetUserId"
            class="target-input"
            type="text"
            maxlength="8"
            placeholder="请输入用户 ID"
            placeholder-class="input-placeholder"
          />
          <button
            class="add-btn"
            :class="{ 'add-btn-disabled': adding }"
            :disabled="adding"
            hover-class="add-btn-active"
            @tap="onAddBlockedUser"
          >
            {{ adding ? '添加中...' : '添加' }}
          </button>
        </view>
      </view>

      <view class="list-header">
        <text class="list-title">已屏蔽用户</text>
        <text class="list-count">{{ total }} 人</text>
      </view>

      <view v-if="loading" class="loading-wrap">
        <text class="loading-text">加载中...</text>
      </view>

      <view v-else-if="items.length === 0" class="empty-wrap">
        <text class="empty-title">暂无黑名单用户</text>
        <text class="empty-subtitle">你屏蔽的用户会出现在这里</text>
      </view>

      <view v-else class="list-wrap">
        <view
          v-for="item in items"
          :key="item.user_id"
          class="user-row"
        >
          <image class="avatar" mode="aspectFill" :src="item.avatar_url" />
          <view class="user-main">
            <view class="name-line">
              <text class="nickname">{{ item.nickname }}</text>
              <text v-if="item.is_verified" class="verified-tag">已认证</text>
            </view>
            <text class="user-id">ID: {{ item.user_id }}</text>
            <text class="blocked-time">加入时间：{{ formatTime(item.blocked_at) }}</text>
          </view>
          <button class="remove-btn" hover-class="remove-btn-active" @tap="onRemoveBlockedUser(item)">
            移除
          </button>
        </view>
      </view>

      <view class="bottom-space"></view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { addBlockedUser, getBlockedUsers, removeBlockedUser } from '../../../../api/user'

const targetUserId = ref('')
const loading = ref(false)
const adding = ref(false)
const items = ref([])
const total = ref(0)

const normalizeUserId = (value) => String(value || '').replace(/[^0-9a-zA-Z]/g, '').slice(0, 8)

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const formatTime = (value) => {
  if (!value) {
    return '--'
  }
  const normalized = String(value).replace('T', ' ')
  return normalized.slice(0, 16)
}

const loadBlockedUsers = async () => {
  loading.value = true
  try {
    const data = await getBlockedUsers({ offset: 0, limit: 100 })
    items.value = Array.isArray(data?.items) ? data.items : []
    total.value = Number(data?.total || 0)
  } catch (err) {
    if (err?.statusCode === 401) {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
      return
    }
    showToast(err?.message || '加载黑名单失败')
  } finally {
    loading.value = false
  }
}

const onAddBlockedUser = async () => {
  if (adding.value) {
    return
  }

  const normalizedId = normalizeUserId(targetUserId.value)
  targetUserId.value = normalizedId
  if (normalizedId.length !== 8) {
    showToast('请输入 8 位用户 ID')
    return
  }

  adding.value = true
  try {
    const data = await addBlockedUser(normalizedId)
    showToast(data?.created ? '已加入黑名单' : '该用户已在黑名单中')
    targetUserId.value = ''
    await loadBlockedUsers()
  } catch (err) {
    if (err?.statusCode === 401) {
      uni.navigateTo({
        url: '/pages/auth/login/index'
      })
      return
    }
    showToast(err?.message || '加入黑名单失败')
  } finally {
    adding.value = false
  }
}

const onRemoveBlockedUser = (item) => {
  if (!item?.user_id) {
    return
  }

  uni.showModal({
    title: '移出黑名单',
    content: `确认将 ${item.nickname || '该用户'} 移出黑名单吗？`,
    success: async (res) => {
      if (!res?.confirm) {
        return
      }

      try {
        const data = await removeBlockedUser(item.user_id)
        showToast(data?.removed ? '已移出黑名单' : '该用户不在黑名单中')
        await loadBlockedUsers()
      } catch (err) {
        if (err?.statusCode === 401) {
          uni.navigateTo({
            url: '/pages/auth/login/index'
          })
          return
        }
        showToast(err?.message || '移除失败，请稍后重试')
      }
    }
  })
}

onShow(() => {
  loadBlockedUsers()
})
</script>

<style scoped>
.blocked-page {
  min-height: 100vh;
  background: #f8f6f6;
  color: #0f172a;
}

.content-wrap {
  padding: 16px;
  box-sizing: border-box;
}

.add-card {
  background: #ffffff;
  border: 1px solid #f1f5f9;
  border-radius: 12px;
  padding: 14px;
  box-sizing: border-box;
}

.card-title {
  display: block;
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.card-subtitle {
  display: block;
  margin-top: 4px;
  color: #64748b;
  font-size: 12px;
}

.add-row {
  margin-top: 12px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.target-input {
  flex: 1;
  min-width: 0;
  height: 44px;
  border-radius: 10px;
  border: 1px solid #e2e8f0;
  padding: 0 12px;
  box-sizing: border-box;
  font-size: 15px;
  color: #0f172a;
  background: #ffffff;
}

.input-placeholder {
  color: #94a3b8;
}

.add-btn {
  width: 84px;
  height: 44px;
  border: 0;
  border-radius: 10px;
  background: #1a57db;
  color: #ffffff;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}

.add-btn-active {
  opacity: 0.9;
}

.add-btn-disabled {
  opacity: 0.75;
}

.list-header {
  margin-top: 20px;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.list-title {
  font-size: 16px;
  font-weight: 700;
  color: #0f172a;
}

.list-count {
  font-size: 13px;
  color: #64748b;
}

.loading-wrap,
.empty-wrap {
  background: #ffffff;
  border: 1px solid #f1f5f9;
  border-radius: 12px;
  min-height: 120px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.loading-text,
.empty-title {
  font-size: 14px;
  color: #334155;
}

.empty-subtitle {
  margin-top: 6px;
  font-size: 12px;
  color: #94a3b8;
}

.list-wrap {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.user-row {
  background: #ffffff;
  border: 1px solid #f1f5f9;
  border-radius: 12px;
  padding: 12px;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  gap: 10px;
}

.avatar {
  width: 46px;
  height: 46px;
  border-radius: 999px;
  background: #e2e8f0;
  flex-shrink: 0;
}

.user-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.name-line {
  display: flex;
  align-items: center;
  gap: 6px;
  min-width: 0;
}

.nickname {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-size: 15px;
  font-weight: 600;
  color: #0f172a;
}

.verified-tag {
  font-size: 10px;
  line-height: 16px;
  height: 16px;
  padding: 0 6px;
  border-radius: 999px;
  background: rgba(26, 87, 219, 0.12);
  color: #1a57db;
  flex-shrink: 0;
}

.user-id,
.blocked-time {
  font-size: 12px;
  color: #64748b;
}

.remove-btn {
  width: 64px;
  height: 34px;
  border: 0;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.12);
  color: #ef4444;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.remove-btn-active {
  opacity: 0.9;
}

.bottom-space {
  height: calc(16px + env(safe-area-inset-bottom));
}

@media (prefers-color-scheme: dark) {
  .blocked-page {
    background: #111621;
    color: #f1f5f9;
  }

  .add-card,
  .loading-wrap,
  .empty-wrap,
  .user-row {
    background: #0f172a;
    border-color: #1e293b;
  }

  .card-title,
  .list-title,
  .nickname,
  .loading-text,
  .empty-title {
    color: #f1f5f9;
  }

  .card-subtitle,
  .list-count,
  .empty-subtitle,
  .user-id,
  .blocked-time {
    color: #94a3b8;
  }

  .target-input {
    background: #1e293b;
    border-color: #334155;
    color: #f1f5f9;
  }

  .input-placeholder {
    color: #64748b;
  }
}
</style>

