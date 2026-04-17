<template>
  <view class="points-page">
    <view class="page-main">
      <view class="score-card">
        <view class="score-card-glow"></view>

        <view class="score-card-head">
          <view class="score-copy">
            <text class="score-label">当前积分余额</text>
            <view class="score-value-row">
              <text class="score-value">{{ pointsText }}</text>
              <text class="score-unit">Points</text>
            </view>
          </view>

          <button class="detail-chip" hover-class="detail-chip-active" @tap="onTapHistory">
            <text class="detail-chip-text">积分明细</text>
            <image class="detail-chip-icon" mode="aspectFit" src="/static/me-icons/chevron-light.png" />
          </button>
        </view>

        <view class="score-progress-row">
          <view class="score-progress-track">
            <view class="score-progress-fill" :style="{ width: progressWidth }"></view>
          </view>
          <text class="score-progress-text">{{ levelText }}</text>
        </view>
      </view>

      <view class="section">
        <view class="section-head">
          <text class="section-title">每日任务</text>
          <text class="section-badge">每日零点重置</text>
        </view>

        <view class="task-list">
          <view v-for="task in dailyTasks" :key="task.key" class="task-card">
            <view class="task-main">
              <view class="task-icon" :class="`task-icon-${task.tone}`">
                <image v-if="task.iconPath" class="task-icon-img" mode="aspectFit" :src="task.iconPath" />
                <text v-else class="task-icon-text">{{ task.iconText }}</text>
              </view>

              <view class="task-copy">
                <text class="task-title">{{ task.title }}</text>
                <view class="task-reward-row">
                  <view class="task-reward-dot"></view>
                  <text class="task-reward-text">+{{ task.amount }} 积分</text>
                </view>
              </view>
            </view>

            <button
              class="task-btn"
              :class="{ 'task-btn-disabled': isTaskDisabled(task) }"
              :disabled="isTaskDisabled(task)"
              hover-class="task-btn-active"
              @tap="onTapTask(task)"
            >
              {{ taskButtonText(task) }}
            </button>
          </view>
        </view>
      </view>

      <view class="section">
        <view class="section-head section-head-simple">
          <text class="section-title">成就任务</text>
        </view>

        <view class="achievement-grid">
          <view v-for="task in achievementTasks" :key="task.key" class="achievement-card">
            <view>
              <view class="achievement-icon" :class="`achievement-icon-${task.tone}`">
                <image v-if="task.iconPath" class="achievement-icon-img" mode="aspectFit" :src="task.iconPath" />
                <text v-else class="achievement-icon-text">{{ task.iconText }}</text>
              </view>

              <text class="achievement-title">{{ task.title }}</text>
              <text class="achievement-desc">{{ task.description }}</text>
            </view>

            <view class="achievement-foot">
              <text class="achievement-reward">+{{ task.amount }}</text>
              <button
                class="mini-arrow-btn"
                :class="{ 'mini-arrow-btn-disabled': isTaskDisabled(task) }"
                :disabled="isTaskDisabled(task)"
                hover-class="mini-arrow-btn-active"
                @tap="onTapTask(task)"
              >
                <image class="mini-arrow-img" mode="aspectFit" src="/static/me-icons/chevron-light.png" />
              </button>
            </view>
          </view>

          <view v-if="inviteTask" class="invite-card">
            <view class="invite-card-glow"></view>

            <view class="invite-card-content">
              <view class="invite-left">
                <view class="invite-icon">
                  <image v-if="inviteTask.iconPath" class="invite-icon-img" mode="aspectFit" :src="inviteTask.iconPath" />
                  <text v-else class="invite-icon-text">{{ inviteTask.iconText }}</text>
                </view>

                <view class="invite-copy">
                  <text class="invite-title">{{ inviteTask.title }}</text>
                  <text class="invite-desc">{{ inviteTask.description }}</text>
                </view>
              </view>

              <view class="invite-right">
                <text class="invite-reward">+{{ inviteTask.amount }}</text>
                <button
                  class="invite-btn"
                  open-type="share"
                  hover-class="invite-btn-active"
                  @tap="onTapTask(inviteTask)"
                >
                  去邀请
                </button>
              </view>
            </view>
          </view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow, onShareAppMessage } from '@dcloudio/uni-app'
import { claimPointsCheckIn, getPointsCenterOverview } from '../../../api/points'

const SCORE_LEVELS = [
  { level: 1, min: 0, max: 2000 },
  { level: 2, min: 2000, max: 3000 },
  { level: 3, min: 3000, max: 5000 },
  { level: 4, min: 5000, max: null }
]

const TASK_CONFIG = {
  daily_check_in: {
    key: 'daily_check_in',
    title: '签到',
    amount: 10,
    description: '每日签到一次，可获得积分奖励',
    tone: 'blue',
    iconPath: '/static/me-icons/badge-blue.png',
    iconText: '签'
  },
  publish_resource: {
    key: 'publish_resource',
    title: '发布资源',
    amount: 20,
    description: '每成功发布一条资源，可获得积分奖励',
    tone: 'orange',
    iconPath: '/static/me-icons/upload-primary.png',
    iconText: '发'
  },
  complete_profile: {
    key: 'complete_profile',
    title: '完善个人信息',
    amount: 100,
    description: '提升职场可信度',
    tone: 'blue-soft',
    iconPath: '/static/me-icons/description-primary.png',
    iconText: '资'
  },
  real_name_verified: {
    key: 'real_name_verified',
    title: '身份实名认证',
    amount: 200,
    description: '解锁更多高级权限',
    tone: 'green',
    iconPath: '/static/me-icons/verified-emerald.png',
    iconText: '认'
  },
  invite_friend: {
    key: 'invite_friend',
    title: '邀请好友加入',
    amount: 300,
    description: '每成功邀请一位可获得奖励',
    tone: 'primary',
    iconPath: '/static/me-icons/contact-page-primary.png',
    iconText: '邀'
  }
}

const pointsOverview = ref({
  balance: 0,
  available_balance: 0,
  frozen_balance: 0
})
const remoteTasks = ref([])
const inviteCode = ref('')
const isLoading = ref(false)

const pointsText = computed(() => {
  return Number(pointsOverview.value?.balance || 0).toLocaleString('zh-CN')
})

const levelMeta = computed(() => {
  const balance = Math.max(Number(pointsOverview.value?.balance || 0), 0)
  const current = SCORE_LEVELS.find((item) => {
    return item.max === null ? balance >= item.min : balance >= item.min && balance < item.max
  }) || SCORE_LEVELS[0]

  let ratio = 1
  if (current.max !== null) {
    const span = Math.max(current.max - current.min, 1)
    ratio = (balance - current.min) / span
  }

  return {
    level: current.level,
    progress: Math.min(Math.max(ratio, 0), 1)
  }
})

const progressWidth = computed(() => `${Math.round(levelMeta.value.progress * 100)}%`)
const levelText = computed(() => `LV${levelMeta.value.level} 会员`)

const normalizedTaskMap = computed(() => {
  const mapped = {}

  Object.keys(TASK_CONFIG).forEach((key) => {
    mapped[key] = {
      ...TASK_CONFIG[key],
      enabled: true,
      completed: false,
      eligible: true,
      completedCount: 0
    }
  })

  ;(remoteTasks.value || []).forEach((item) => {
    const key = String(item?.key || '').trim()
    if (!key || !mapped[key]) {
      return
    }
    mapped[key] = {
      ...mapped[key],
      title: String(item?.title || mapped[key].title).trim() || mapped[key].title,
      description: String(item?.description || mapped[key].description).trim() || mapped[key].description,
      amount: Number(item?.amount ?? mapped[key].amount),
      enabled: item?.enabled === undefined ? mapped[key].enabled : Boolean(item?.enabled),
      completed: Boolean(item?.completed),
      eligible: item?.eligible === undefined ? true : Boolean(item?.eligible),
      completedCount: Number(item?.completed_count || 0)
    }
  })

  return mapped
})

const dailyTasks = computed(() => {
  return ['daily_check_in', 'publish_resource']
    .map((key) => normalizedTaskMap.value[key])
    .filter((item) => item && item.enabled)
})

const achievementTasks = computed(() => {
  return ['complete_profile', 'real_name_verified']
    .map((key) => normalizedTaskMap.value[key])
    .filter((item) => item && item.enabled)
})

const inviteTask = computed(() => {
  const task = normalizedTaskMap.value.invite_friend
  return task && task.enabled ? task : null
})

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const hasLogin = () => Boolean(String(uni.getStorageSync('token') || '').trim())

const goLogin = () => {
  uni.navigateTo({
    url: '/pages/auth/login/index'
  })
}

const syncStoredPoints = (balance) => {
  const userInfo = uni.getStorageSync('userInfo') || {}
  uni.setStorageSync('userInfo', {
    ...userInfo,
    points: Number(balance || 0)
  })
}

const loadOverview = async () => {
  if (!hasLogin()) {
    pointsOverview.value = {
      balance: 0,
      available_balance: 0,
      frozen_balance: 0
    }
    remoteTasks.value = []
    inviteCode.value = ''
    return
  }

  isLoading.value = true
  try {
    const overview = await getPointsCenterOverview()
    pointsOverview.value = {
      balance: Number(overview?.points?.balance || 0),
      available_balance: Number(overview?.points?.available_balance || 0),
      frozen_balance: Number(overview?.points?.frozen_balance || 0)
    }
    remoteTasks.value = Array.isArray(overview?.tasks) ? overview.tasks : []
    inviteCode.value = String(overview?.invite?.invite_code || '').trim()
    syncStoredPoints(pointsOverview.value.balance)
  } catch (err) {
    showToast(err?.message || '积分信息加载失败')
  } finally {
    isLoading.value = false
  }
}

const onTapHistory = () => {
  if (!hasLogin()) {
    goLogin()
    return
  }
  uni.navigateTo({
    url: '/pages/me/points/records/index'
  })
}

const taskButtonText = (task) => {
  if (task.key === 'daily_check_in') {
    return task.completed ? '已签到' : '去完成'
  }
  if (task.key === 'publish_resource') {
    return '去完成'
  }
  if (task.key === 'complete_profile') {
    return task.completed ? '已完成' : '去完成'
  }
  if (task.key === 'real_name_verified') {
    return task.completed ? '已完成' : '去认证'
  }
  if (task.key === 'invite_friend') {
    return '去邀请'
  }
  return task.completed ? '已完成' : '去完成'
}

const isTaskDisabled = (task) => {
  if (task.key === 'publish_resource' || task.key === 'invite_friend') {
    return false
  }
  if (task.key === 'real_name_verified') {
    return Boolean(task.completed)
  }
  return Boolean(task.completed || isLoading.value)
}

const onTapTask = async (task) => {
  const key = String(task?.key || '').trim()

  if (!hasLogin()) {
    goLogin()
    return
  }

  if (key === 'daily_check_in') {
    if (isTaskDisabled(task)) {
      return
    }
    try {
      const result = await claimPointsCheckIn()
      pointsOverview.value = {
        balance: Number(result?.balance || pointsOverview.value.balance),
        available_balance: Number(result?.available_balance || pointsOverview.value.available_balance),
        frozen_balance: Number(pointsOverview.value.frozen_balance || 0)
      }
      syncStoredPoints(pointsOverview.value.balance)
      await loadOverview()
      showToast('签到成功')
    } catch (err) {
      showToast(err?.message || '签到失败')
    }
    return
  }

  if (key === 'publish_resource') {
    uni.navigateTo({
      url: '/pages/resources/publish/index'
    })
    return
  }

  if (key === 'complete_profile') {
    uni.navigateTo({
      url: '/pages/me/editInfo/index'
    })
    return
  }

  if (key === 'real_name_verified') {
    uni.navigateTo({
      url: '/pages/me/auth/index'
    })
    return
  }

  if (key === 'invite_friend') {
    if (typeof uni.showShareMenu === 'function') {
      uni.showShareMenu({
        withShareTicket: false
      })
    }
    showToast('请通过右上角或按钮分享给好友')
  }
}

const buildSharePath = () => {
  const code = String(inviteCode.value || '').trim()
  if (!code) {
    return '/pages/auth/login/index'
  }
  return `/pages/auth/login/index?inviteCode=${encodeURIComponent(code)}`
}

onShareAppMessage(() => {
  return {
    title: '加入圈脉链，完成任务赚积分，积分可用于会员折扣',
    path: buildSharePath()
  }
})

onShow(() => {
  if (typeof uni.showShareMenu === 'function') {
    uni.showShareMenu({
      withShareTicket: false
    })
  }
  loadOverview()
})
</script>

<style scoped>
.points-page {
  min-height: 100vh;
  background: #f6f6f8;
  color: #0f172a;
  font-family: 'Manrope', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.page-main {
  padding: 24px 16px calc(32px + env(safe-area-inset-bottom));
}

.score-card {
  position: relative;
  overflow: hidden;
  padding: 24px;
  border-radius: 18px;
  background: #1a57db;
  box-shadow: 0 18px 36px rgba(26, 87, 219, 0.22);
}

.score-card-glow {
  position: absolute;
  top: -32px;
  right: -32px;
  width: 128px;
  height: 128px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.12);
  filter: blur(10px);
}

.score-card-head {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.score-copy {
  flex: 1;
  min-width: 0;
}

.score-label {
  display: block;
  color: rgba(219, 234, 254, 0.82);
  font-size: 12px;
  line-height: 18px;
  font-weight: 700;
  letter-spacing: 1.6px;
}

.score-value-row {
  display: flex;
  align-items: baseline;
  gap: 6px;
  margin-top: 8px;
}

.score-value {
  color: #ffffff;
  font-size: 40px;
  line-height: 48px;
  font-weight: 800;
}

.score-unit {
  color: rgba(255, 255, 255, 0.88);
  font-size: 13px;
  line-height: 20px;
  font-weight: 600;
}

.detail-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 32px;
  line-height: 32px;
  padding: 0 12px;
  border: 0;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.16);
  color: #ffffff;
  font-size: 10px;
  font-weight: 700;
}

.detail-chip::after {
  border: 0;
}

.detail-chip-active {
  opacity: 0.9;
}

.detail-chip-text {
  color: #ffffff;
}

.detail-chip-icon {
  width: 12px;
  height: 12px;
  margin-left: 4px;
  vertical-align: middle;
}

.score-progress-row {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 18px;
}

.score-progress-track {
  flex: 1;
  height: 6px;
  overflow: hidden;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.22);
}

.score-progress-fill {
  height: 100%;
  border-radius: 999px;
  background: #ffffff;
}

.score-progress-text {
  flex-shrink: 0;
  color: #ffffff;
  font-size: 10px;
  line-height: 16px;
  font-weight: 700;
}

.section {
  margin-top: 32px;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 16px;
}

.section-head-simple {
  justify-content: flex-start;
}

.section-title {
  color: #0f172a;
  font-size: 18px;
  line-height: 26px;
  font-weight: 700;
}

.section-badge {
  padding: 2px 8px;
  border-radius: 6px;
  background: rgba(26, 87, 219, 0.1);
  color: #1a57db;
  font-size: 10px;
  line-height: 16px;
  font-weight: 700;
}

.task-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.task-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 16px;
  border-radius: 16px;
  background: #ffffff;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
}

.task-main {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.task-icon,
.achievement-icon,
.invite-icon {
  display: flex;
  align-items: center;
  justify-content: center;
}

.task-icon {
  width: 48px;
  height: 48px;
  border-radius: 999px;
}

.task-icon-blue {
  background: #eff6ff;
  color: #1a57db;
}

.task-icon-orange {
  background: #fff7ed;
  color: #ea580c;
}

.task-icon-text,
.achievement-icon-text,
.invite-icon-text {
  font-size: 16px;
  line-height: 1;
  font-weight: 700;
}

.task-icon-img {
  width: 22px;
  height: 22px;
}

.achievement-icon-img {
  width: 20px;
  height: 20px;
}

.task-copy {
  flex: 1;
  min-width: 0;
}

.task-title {
  display: block;
  color: #0f172a;
  font-size: 15px;
  line-height: 22px;
  font-weight: 700;
}

.task-reward-row {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 6px;
}

.task-reward-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: #1a57db;
}

.task-reward-text {
  color: #1a57db;
  font-size: 12px;
  line-height: 18px;
  font-weight: 700;
}

.task-btn,
.mini-arrow-btn,
.invite-btn {
  border: 0;
}

.task-btn::after,
.mini-arrow-btn::after,
.invite-btn::after {
  border: 0;
}

.task-btn {
  min-width: 84px;
  height: 34px;
  line-height: 34px;
  padding: 0 14px;
  border-radius: 999px;
  background: #1a57db;
  color: #ffffff;
  font-size: 12px;
  font-weight: 700;
}

.task-btn-active,
.mini-arrow-btn-active,
.invite-btn-active {
  opacity: 0.9;
}

.task-btn-disabled,
.mini-arrow-btn-disabled {
  opacity: 0.6;
}

.achievement-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.achievement-card {
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-height: 170px;
  padding: 20px 16px 16px;
  border-radius: 16px;
  background: #f8f9fc;
}

.achievement-icon {
  width: 40px;
  height: 40px;
  border-radius: 12px;
}

.achievement-icon-blue-soft {
  background: rgba(191, 219, 254, 0.45);
  color: #1a57db;
}

.achievement-icon-green {
  background: #f0fdf4;
  color: #059669;
}

.achievement-title {
  display: block;
  margin-top: 12px;
  color: #0f172a;
  font-size: 13px;
  line-height: 20px;
  font-weight: 700;
}

.achievement-desc {
  display: block;
  margin-top: 4px;
  color: #64748b;
  font-size: 10px;
  line-height: 16px;
}

.achievement-foot {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-top: 16px;
}

.achievement-reward {
  color: #1a57db;
  font-size: 12px;
  line-height: 18px;
  font-weight: 800;
}

.mini-arrow-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  line-height: 28px;
  border-radius: 999px;
  background: #1a57db;
  color: #ffffff;
  text-align: center;
}

.mini-arrow-img {
  width: 12px;
  height: 12px;
}

.invite-card {
  position: relative;
  grid-column: 1 / -1;
  overflow: hidden;
  padding: 20px 18px;
  border-radius: 16px;
  border: 1px solid rgba(26, 87, 219, 0.1);
  background: rgba(26, 87, 219, 0.05);
}

.invite-card-glow {
  position: absolute;
  top: -16px;
  right: -18px;
  width: 120px;
  height: 120px;
  border-radius: 999px;
  background: rgba(26, 87, 219, 0.05);
}

.invite-card-content {
  position: relative;
  z-index: 1;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.invite-left {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 0;
}

.invite-icon {
  width: 48px;
  height: 48px;
  border-radius: 999px;
  background: #ffffff;
  color: #1a57db;
  box-shadow: 0 6px 14px rgba(15, 23, 42, 0.06);
}

.invite-icon-img {
  width: 22px;
  height: 22px;
}

.invite-copy {
  flex: 1;
  min-width: 0;
}

.invite-title {
  display: block;
  color: #0f172a;
  font-size: 14px;
  line-height: 21px;
  font-weight: 700;
}

.invite-desc {
  display: block;
  margin-top: 4px;
  color: #64748b;
  font-size: 12px;
  line-height: 18px;
}

.invite-right {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.invite-reward {
  color: #1a57db;
  font-size: 18px;
  line-height: 24px;
  font-weight: 800;
}

.invite-btn {
  min-width: 76px;
  height: 32px;
  line-height: 32px;
  margin-top: 6px;
  padding: 0 14px;
  border-radius: 999px;
  background: #1a57db;
  color: #ffffff;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 0.6px;
}
</style>
