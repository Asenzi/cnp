<template>
  <view class="records-page">
    <scroll-view class="page-scroll" scroll-y :show-scrollbar="false" @scrolltolower="loadMore">
      <view class="page-main">
        <view v-if="records.length" class="record-list">
          <view v-for="record in records" :key="record.id" class="record-item">
            <view class="record-copy">
              <text class="record-title">{{ record.title }}</text>
              <text class="record-meta">{{ record.remark || formatDateTime(record.created_at) }}</text>
            </view>
            <view class="record-action">
              <text class="record-amount" :class="record.change_amount >= 0 ? 'record-amount-plus' : 'record-amount-minus'">
                {{ record.change_amount >= 0 ? '+' : '' }}{{ record.change_amount }}
              </text>
              <text class="record-balance">余额 {{ record.balance_after }}</text>
            </view>
          </view>
        </view>
        <view v-else class="empty-card">
          <text class="empty-text">暂无积分记录</text>
        </view>

        <view v-if="records.length" class="load-state">
          <text class="load-state-text">{{ loadStateText }}</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getPointsRecords } from '../../../../api/points'

const records = ref([])
const nextCursor = ref('')
const hasMore = ref(true)
const isLoading = ref(false)

const loadStateText = computed(() => {
  if (isLoading.value) {
    return '加载中...'
  }
  return hasMore.value ? '上拉加载更多' : '没有更多了'
})

const formatDateTime = (value) => {
  const text = String(value || '').trim()
  if (!text) {
    return ''
  }
  return text.replace('T', ' ').slice(0, 16)
}

const showToast = (title) => {
  uni.showToast({
    title,
    icon: 'none'
  })
}

const loadRecords = async (reset = false) => {
  if (isLoading.value) {
    return
  }
  if (!reset && !hasMore.value) {
    return
  }

  isLoading.value = true
  try {
    const response = await getPointsRecords({
      cursor: reset ? '' : nextCursor.value,
      limit: 20
    })
    const items = Array.isArray(response?.items) ? response.items : []
    records.value = reset ? items : [...records.value, ...items]
    nextCursor.value = String(response?.next_cursor || '').trim()
    hasMore.value = Boolean(response?.has_more)
  } catch (err) {
    showToast(err?.message || '积分记录加载失败')
  } finally {
    isLoading.value = false
  }
}

const loadMore = () => {
  loadRecords(false)
}

onShow(() => {
  records.value = []
  nextCursor.value = ''
  hasMore.value = true
  loadRecords(true)
})
</script>

<style scoped>
.records-page {
  min-height: 100vh;
  background: #f6f6f8;
  color: #0f172a;
  font-family: 'Manrope', 'PingFang SC', 'Microsoft YaHei', sans-serif;
}

.page-scroll {
  height: 100vh;
}

.page-main {
  padding: 16px;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-item,
.empty-card {
  padding: 16px;
  border-radius: 14px;
  background: #ffffff;
  box-shadow: 0 8px 22px rgba(15, 23, 42, 0.05);
  display: flex;
  justify-content: space-between;
  gap: 16px;
}

.record-copy {
  flex: 1;
}

.record-title {
  display: block;
  color: #0f172a;
  font-size: 15px;
  line-height: 22px;
  font-weight: 700;
}

.record-meta,
.record-balance {
  display: block;
  margin-top: 6px;
  color: #64748b;
  font-size: 12px;
  line-height: 18px;
}

.record-action {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.record-amount {
  font-size: 16px;
  line-height: 22px;
  font-weight: 700;
}

.record-amount-plus {
  color: #1d4ed8;
}

.record-amount-minus {
  color: #dc2626;
}

.empty-text,
.load-state-text {
  color: #64748b;
  font-size: 13px;
  line-height: 20px;
  text-align: center;
}

.load-state {
  padding: 18px 0 8px;
}
</style>
