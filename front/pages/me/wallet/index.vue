<template>
  <view class="wallet-page">
    <scroll-view class="wallet-scroll" scroll-y :show-scrollbar="false">
      <view class="wallet-content">
        <WalletBalanceCard :balance-text="displayBalance" :wallet-id="walletId" />

        <view class="action-wrap">
          <button class="recharge-btn" hover-class="recharge-btn-active" @tap="onTapRecharge" @click="onTapRecharge">
            <image class="recharge-icon" mode="aspectFit" src="/static/icon/recharge.png" />
            <text>充值</text>
          </button>
        </view>

        <view class="section-head">
          <text class="section-title">收支明细</text>

          <view class="filter-row">
            <button
              class="filter-btn"
              :class="{ 'filter-btn-selected': selectedTimeFilter !== 'all' || showTimeFilterMenu }"
              hover-class="filter-btn-active"
              @tap.stop="onTapTimeFilter"
            >
              <text>{{ timeFilterButtonText }}</text>
              <image class="filter-icon" mode="aspectFit" src="/static/me-icons/tune-gray.png" />
            </button>

            <button
              class="filter-btn"
              :class="{ 'filter-btn-selected': selectedTypeFilter !== 'all' || showTypeFilterMenu }"
              hover-class="filter-btn-active"
              @tap.stop="onTapTypeFilter"
            >
              <text>{{ typeFilterButtonText }}</text>
              <image class="filter-icon" mode="aspectFit" src="/static/me-icons/tune-gray.png" />
            </button>

            <view v-if="showTimeFilterMenu" class="filter-dropdown time-filter-dropdown" @tap.stop>
              <view
                v-for="option in TIME_FILTER_OPTIONS"
                :key="option.value"
                class="filter-option"
                :class="{ 'filter-option-active': selectedTimeFilter === option.value }"
                @tap="onSelectTimeFilter(option.value)"
              >
                <text class="filter-option-text">{{ option.label }}</text>
              </view>
            </view>

            <view v-if="showTypeFilterMenu" class="filter-dropdown type-filter-dropdown" @tap.stop>
              <view
                v-for="option in TYPE_FILTER_OPTIONS"
                :key="option.value"
                class="filter-option"
                :class="{ 'filter-option-active': selectedTypeFilter === option.value }"
                @tap="onSelectTypeFilter(option.value)"
              >
                <text class="filter-option-text">{{ option.label }}</text>
              </view>
            </view>
          </view>
        </view>

        <view v-if="displayRecords.length > 0" class="tx-list">
          <WalletTransactionItem v-for="item in displayRecords" :key="item.id" :item="item" />
        </view>
        <view v-else class="empty-wrap">
          <image class="empty-icon" mode="aspectFit" src="/static/icon/block.png" />
          <text class="empty-text">{{ emptyTipText }}</text>
        </view>

        <view v-if="loadingMore" class="load-tip">加载中...</view>
        <view v-else-if="!hasMore && displayRecords.length > 0" class="load-tip">没有更多了</view>
      </view>
    </scroll-view>

    <view v-if="showTimeFilterMenu || showTypeFilterMenu" class="filter-mask" @tap="closeAllFilterMenus"></view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onPullDownRefresh, onReachBottom, onShow } from '@dcloudio/uni-app'
import { getMemberCenterOverview, getMemberOrders, getWalletRechargeOrders } from '../../../api/payment'
import { getCurrentUserProfile } from '../../../api/user'
import WalletBalanceCard from './components/WalletBalanceCard.vue'
import WalletTransactionItem from './components/WalletTransactionItem.vue'
import {
  formatWalletBalance,
  mapMemberOrderRecord,
  mapRechargeOrderRecord,
  mergeWalletRecords
} from './modules/wallet-view-model'

const TIME_FILTER_OPTIONS = [
  { label: '全部时间', value: 'all' },
  { label: '近一周', value: 'week' },
  { label: '近一月', value: 'month' },
  { label: '近一年', value: 'year' }
]

const TYPE_FILTER_OPTIONS = [
  { label: '全部', value: 'all' },
  { label: '支出', value: 'expense' },
  { label: '收入', value: 'income' }
]

const walletBalance = ref(0)
const walletId = ref('--')
const records = ref([])
const selectedTimeFilter = ref('all')
const selectedTypeFilter = ref('all')
const showTimeFilterMenu = ref(false)
const showTypeFilterMenu = ref(false)

const memberRecords = ref([])
const memberCursor = ref('')
const memberHasMore = ref(false)

const rechargeRecords = ref([])
const rechargeCursor = ref('')
const rechargeHasMore = ref(false)

const loadingMore = ref(false)
const hasMore = ref(false)

const displayBalance = computed(() => formatWalletBalance(walletBalance.value))

const timeFilterButtonText = computed(() => {
  const option = TIME_FILTER_OPTIONS.find((opt) => opt.value === selectedTimeFilter.value)
  return option?.label || '时间'
})

const typeFilterButtonText = computed(() => {
  const option = TYPE_FILTER_OPTIONS.find((opt) => opt.value === selectedTypeFilter.value)
  return option?.label || '类型'
})

const getTimeFilterTimestamp = () => {
  const now = Date.now()
  if (selectedTimeFilter.value === 'week') {
    return now - 7 * 24 * 60 * 60 * 1000
  }
  if (selectedTimeFilter.value === 'month') {
    return now - 30 * 24 * 60 * 60 * 1000
  }
  if (selectedTimeFilter.value === 'year') {
    return now - 365 * 24 * 60 * 60 * 1000
  }
  return 0
}

const displayRecords = computed(() => {
  let list = Array.isArray(records.value) ? records.value : []

  // 时间筛选
  const timeThreshold = getTimeFilterTimestamp()
  if (timeThreshold > 0) {
    list = list.filter((item) => {
      const itemTs = Number(item?.sortTs || 0)
      return itemTs >= timeThreshold
    })
  }

  // 类型筛选
  if (selectedTypeFilter.value === 'expense') {
    list = list.filter((item) => Number(item?.amount || 0) < 0)
  } else if (selectedTypeFilter.value === 'income') {
    list = list.filter((item) => Number(item?.amount || 0) > 0)
  }

  return list
})

const emptyTipText = computed(() => {
  if (selectedTypeFilter.value === 'expense') {
    return '暂无支出记录'
  }
  if (selectedTypeFilter.value === 'income') {
    return '暂无收入记录'
  }
  return '暂无收支记录'
})

const resolveWalletId = (profile = {}) => {
  const userIdRaw = String(profile?.userId || profile?.user_id || '').trim()
  if (!userIdRaw) {
    return '--'
  }
  return userIdRaw
}

const mergeRecords = (reset = false) => {
  const merged = mergeWalletRecords(memberRecords.value, rechargeRecords.value)
  records.value = merged
  hasMore.value = Boolean(memberHasMore.value || rechargeHasMore.value)
}

const closeAllFilterMenus = () => {
  showTimeFilterMenu.value = false
  showTypeFilterMenu.value = false
}

const loadWalletOverview = async () => {
  try {
    const overview = await getMemberCenterOverview()
    walletBalance.value = Number(overview?.wallet?.balance || 0)
  } catch {
    walletBalance.value = Number(walletBalance.value || 0)
  }
}

const loadProfile = async () => {
  try {
    const profile = await getCurrentUserProfile()
    walletId.value = resolveWalletId(profile || {})
    if (!Number.isFinite(Number(walletBalance.value)) || Number(walletBalance.value) <= 0) {
      walletBalance.value = Number(profile?.balance || 0)
    }
  } catch {
    walletId.value = '--'
  }
}

const loadMemberOrderRecords = async (reset = false) => {
  if (!reset && !memberHasMore.value) {
    return
  }

  try {
    const payload = await getMemberOrders({
      cursor: reset ? '' : memberCursor.value,
      limit: 20
    })
    const incoming = Array.isArray(payload?.items) ? payload.items.map((item) => mapMemberOrderRecord(item)) : []
    memberRecords.value = reset ? incoming : [...memberRecords.value, ...incoming]
    memberCursor.value = String(payload?.next_cursor || '').trim()
    memberHasMore.value = Boolean(payload?.has_more) && Boolean(memberCursor.value)
  } catch {
    if (reset) {
      memberRecords.value = []
    }
    memberHasMore.value = false
    memberCursor.value = ''
  }
}

const loadRechargeOrderRecords = async (reset = false) => {
  if (!reset && !rechargeHasMore.value) {
    return
  }

  try {
    const payload = await getWalletRechargeOrders({
      cursor: reset ? '' : rechargeCursor.value,
      limit: 20
    })
    const incoming = Array.isArray(payload?.items) ? payload.items.map((item) => mapRechargeOrderRecord(item)) : []
    rechargeRecords.value = reset ? incoming : [...rechargeRecords.value, ...incoming]
    rechargeCursor.value = String(payload?.next_cursor || '').trim()
    rechargeHasMore.value = Boolean(payload?.has_more) && Boolean(rechargeCursor.value)
  } catch {
    if (reset) {
      rechargeRecords.value = []
    }
    rechargeHasMore.value = false
    rechargeCursor.value = ''
  }
}

const loadWalletRecords = async (reset = false) => {
  if (loadingMore.value) {
    return
  }
  if (!reset && !hasMore.value) {
    return
  }

  loadingMore.value = true
  try {
    await Promise.all([loadMemberOrderRecords(reset), loadRechargeOrderRecords(reset)])
    mergeRecords(reset)
  } finally {
    loadingMore.value = false
  }
}

const refreshWalletPage = async () => {
  await Promise.all([loadWalletOverview(), loadProfile()])
  await loadWalletRecords(true)
}

const onTapRecharge = () => {
  closeAllFilterMenus()
  uni.navigateTo({
    url: '/pages/me/wallet/recharge/index'
  })
}

const onTapTimeFilter = () => {
  showTypeFilterMenu.value = false
  showTimeFilterMenu.value = !showTimeFilterMenu.value
}

const onTapTypeFilter = () => {
  showTimeFilterMenu.value = false
  showTypeFilterMenu.value = !showTypeFilterMenu.value
}

const onSelectTimeFilter = (value) => {
  selectedTimeFilter.value = String(value || 'all')
  closeAllFilterMenus()
}

const onSelectTypeFilter = (value) => {
  selectedTypeFilter.value = String(value || 'all')
  closeAllFilterMenus()
}

onLoad(async () => {
  await refreshWalletPage()
})

onShow(async () => {
  await refreshWalletPage()
})

onPullDownRefresh(async () => {
  closeAllFilterMenus()
  try {
    await refreshWalletPage()
  } finally {
    uni.stopPullDownRefresh()
  }
})

onReachBottom(async () => {
  closeAllFilterMenus()
  await loadWalletRecords(false)
})
</script>

<style scoped>
.wallet-page {
  min-height: 100vh;
  height: 100vh;
  position: relative;
  background: #f6f6f8;
}

.wallet-scroll {
  height: 100%;
}

.wallet-content {
  padding: 24rpx 24rpx calc(48rpx + env(safe-area-inset-bottom));
}

.action-wrap {
  margin-top: 32rpx;
}

.recharge-btn {
  height: 88rpx;
  border-radius: 20rpx;
  border: 0;
  background: #1a57db;
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10rpx;
  box-shadow: 0 8rpx 20rpx rgba(26, 87, 219, 0.18);
}

.recharge-btn::after {
  border: 0;
}

.recharge-icon {
  width: 32rpx;
  height: 32rpx;
}

.recharge-btn-active {
  opacity: 0.92;
}

.section-head {
  margin-top: 40rpx;
  margin-bottom: 16rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-title {
  color: #0f172a;
  font-size: 30rpx;
  font-weight: 700;
}

.filter-row {
  display: flex;
  align-items: center;
  gap: 10rpx;
  position: relative;
  z-index: 30;
}

.filter-btn {
  margin: 0;
  padding: 0 14rpx;
  height: 50rpx;
  border-radius: 16rpx;
  border: 0;
  background: rgba(26, 87, 219, 0.08);
  color: #1a57db;
  font-size: 24rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.filter-btn-selected {
  background: rgba(26, 87, 219, 0.14);
}

.filter-btn::after {
  border: 0;
}

.filter-icon {
  width: 22rpx;
  height: 22rpx;
}

.filter-btn-active {
  opacity: 0.82;
}

.filter-mask {
  position: fixed;
  inset: 0;
  z-index: 20;
  background: transparent;
}

.filter-dropdown {
  position: absolute;
  top: calc(100% + 10rpx);
  min-width: 160rpx;
  padding: 10rpx;
  border-radius: 20rpx;
  background: #ffffff;
  box-shadow: 0 12rpx 32rpx rgba(15, 23, 42, 0.12);
}

.time-filter-dropdown {
  right: 90rpx;
}

.type-filter-dropdown {
  right: 0;
}

.filter-option {
  min-height: 60rpx;
  padding: 0 16rpx;
  border-radius: 14rpx;
  display: flex;
  align-items: center;
}

.filter-option-active {
  background: rgba(26, 87, 219, 0.08);
}

.filter-option-text {
  color: #0f172a;
  font-size: 24rpx;
  font-weight: 600;
}

.tx-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.empty-wrap {
  padding: 80rpx 0 40rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20rpx;
}

.empty-icon {
  width: 120rpx;
  height: 120rpx;
  opacity: 0.4;
}

.empty-text {
  color: #94a3b8;
  font-size: 24rpx;
}

.load-tip {
  margin-top: 16rpx;
  margin-bottom: 20rpx;
  text-align: center;
  color: #94a3b8;
  font-size: 22rpx;
}

@media (prefers-color-scheme: dark) {
  .wallet-page {
    background: #111621;
  }

  .section-title {
    color: #f8fafc;
  }

  .filter-dropdown {
    background: #0f172a;
    box-shadow: 0 14rpx 36rpx rgba(15, 23, 42, 0.4);
  }

  .filter-option-active {
    background: rgba(59, 130, 246, 0.18);
  }

  .filter-option-text {
    color: #e2e8f0;
  }
}
</style>
