<template>
  <view class="page">
    <view v-if="loaded" class="list-head">
      <text>成员 {{ total }}</text>
      <text class="head-note">退费后将自动移除成员</text>
    </view>
    <view v-if="loading && !loaded" class="state">正在加载成员...</view>
    <view v-else-if="loadError && !loaded" class="state">
      <text class="error-text">{{ loadError }}</text>
      <button class="retry" @tap="loadMembers()">重试</button>
    </view>
    <AppEmptyState v-else-if="loaded && !members.length"><template #title>暂无成员</template></AppEmptyState>
    <view v-else class="member-list">
      <view v-for="member in members" :key="member.user_id" class="member-row">
        <image class="avatar" :src="member.avatar_url || '/static/logo.png'" mode="aspectFill" />
        <view class="member-content">
          <view class="member-title-row">
            <text class="member-name">{{ member.nickname }}</text>
            <text v-if="member.is_owner" class="owner-label">圈主</text>
          </view>
          <text class="member-meta">{{ paymentText(member) }} · {{ dateText(member.joined_at) }}</text>
          <view v-if="!member.is_owner" class="member-actions">
            <button v-if="member.can_refund" class="action refund" :disabled="acting" @tap="confirmAction(member, 'refund')">退费并移除</button>
            <text v-else-if="Number(member.join_amount) > 0 && member.payment_status === 'paid'" class="refund-note">该支付方式请联系平台退费</text>
            <button class="action remove" :disabled="acting" @tap="confirmAction(member, 'remove')">移除成员</button>
          </view>
        </view>
      </view>
    </view>
    <button v-if="members.length < total" class="more" :disabled="loading" @tap="loadMembers(true)">加载更多</button>
  </view>
</template>

<script setup>
import AppEmptyState from '../../../components/AppEmptyState/AppEmptyState.vue'

import { ref } from 'vue'
import { onLoad, onShow, onPullDownRefresh } from '@dcloudio/uni-app'
import { getManagedCircleMembers, removeCircleMember, refundCircleMember } from '../../../api/circle'

const circleCode = ref('')
const members = ref([])
const total = ref(0)
const loading = ref(false)
const acting = ref(false)
const loaded = ref(false)
const loadError = ref('')

const money = (value) => Number(value || 0).toFixed(2)
const dateText = (value) => String(value || '').slice(0, 10) || '--'
const paymentText = (member) => {
  if (member.payment_status === 'refunded') return `已退费 ¥${money(member.join_amount)}`
  if (member.payment_status === 'paid' && Number(member.join_amount) > 0) return `已付 ¥${money(member.join_amount)}`
  return '免费加入'
}

const loadMembers = async (append = false) => {
  if (loading.value) return
  if (!circleCode.value) {
    loadError.value = '缺少圈子编号，请返回圈子管理重新进入'
    return
  }
  loading.value = true
  loadError.value = ''
  try {
    const data = await getManagedCircleMembers(circleCode.value, { offset: append ? members.value.length : 0 })
    members.value = append ? [...members.value, ...(data?.items || [])] : (data?.items || [])
    total.value = Number(data?.total || 0)
    loaded.value = true
  } catch (error) {
    loadError.value = Number(error?.statusCode) === 404
      ? '成员管理接口尚未部署到当前服务器'
      : (error?.message || '成员加载失败')
    if (append || loaded.value) uni.showToast({ title: loadError.value, icon: 'none' })
  } finally {
    loading.value = false
  }
}

const confirmAction = (member, action) => {
  const refund = action === 'refund'
  uni.showModal({
    title: refund ? '确认退费' : '确认移除',
    content: refund
      ? `向${member.nickname}退还入圈费 ¥${money(member.join_amount)}，并移除其成员资格？`
      : `移除${member.nickname}？此操作不会自动退还已支付的入圈费。`,
    confirmText: refund ? '退费并移除' : '仅移除',
    confirmColor: '#dc2626',
    success: async (result) => {
      if (!result.confirm || acting.value) return
      acting.value = true
      try {
        if (refund) await refundCircleMember(circleCode.value, member.user_id)
        else await removeCircleMember(circleCode.value, member.user_id)
        uni.showToast({ title: refund ? '退费成功' : '已移除', icon: 'success' })
        await loadMembers()
      } catch (error) {
        uni.showToast({ title: error?.message || '操作失败', icon: 'none' })
      } finally {
        acting.value = false
      }
    }
  })
}

onLoad((options) => { circleCode.value = String(options?.code || '').trim() })
onShow(() => loadMembers())
onPullDownRefresh(() => loadMembers().finally(() => uni.stopPullDownRefresh()))
</script>

<style scoped>
.page { min-height: 100vh; padding: 24rpx; box-sizing: border-box; background: #f6f7fb; color: #172033; }
.action::after, .more::after { border: 0; }
.list-head { display: flex; justify-content: space-between; align-items: center; margin: 32rpx 4rpx 18rpx; font-size: 29rpx; font-weight: 600; }
.head-note { color: #8b95a7; font-size: 21rpx; font-weight: 400; }
.state { padding: 80rpx 0; color: #8b95a7; text-align: center; font-size: 25rpx; }
.error-text { display: block; padding: 0 28rpx; }
.retry { width: 160rpx; margin: 24rpx auto 0; background: #e9f0ff; color: #2563eb; font-size: 24rpx; }
.retry::after { border: 0; }
.member-list { background: #fff; border-radius: 8rpx; }
.member-row { display: flex; gap: 18rpx; padding: 24rpx; border-bottom: 1rpx solid #eef0f4; }
.member-row:last-child { border-bottom: 0; }
.avatar { width: 78rpx; height: 78rpx; flex-shrink: 0; border-radius: 50%; background: #eef2f7; }
.member-content { flex: 1; min-width: 0; }
.member-title-row { display: flex; align-items: center; gap: 12rpx; }
.member-name { font-size: 27rpx; font-weight: 600; }
.owner-label { color: #2563eb; font-size: 20rpx; }
.member-meta { display: block; margin-top: 8rpx; color: #8b95a7; font-size: 22rpx; }
.member-actions { display: flex; align-items: center; flex-wrap: wrap; gap: 12rpx; margin-top: 18rpx; }
.action { margin: 0; padding: 0 20rpx; height: 56rpx; line-height: 56rpx; border-radius: 6rpx; font-size: 22rpx; }
.refund { background: #e9f4ff; color: #1d4ed8; }
.remove { background: #fff0f0; color: #c83b3b; }
.refund-note { color: #9a6b1a; font-size: 21rpx; }
.more { margin: 24rpx auto; background: transparent; color: #2563eb; font-size: 24rpx; }
</style>
