<template>
  <view class="venue-detail-page">
    <!-- 第一板块：活动信息 -->
    <view class="event-header">
      <!-- 左侧海报 -->
      <view class="poster-wrap">
        <image
          v-if="coverImage"
          class="poster-image"
          :src="coverImage"
          mode="aspectFill"
        />
        <view v-else class="poster-placeholder">
          <text class="placeholder-text">暂无封面</text>
        </view>
        <!-- 左上角标签 -->
        <view class="poster-tag">电影</view>
      </view>

      <!-- 右侧信息 -->
      <view class="event-info">
        <!-- 第一行：标题和收藏 -->
        <view class="title-row">
          <text class="event-title">{{ post.title || '活动标题' }}</text>
          <view class="favorite-btn" @tap="onToggleFavorite">
            <text class="favorite-icon">{{ isFavorite ? '★' : '☆' }}</text>
          </view>
        </view>

        <!-- 第二行：价格 -->
        <view class="price-row">
          <text class="price-symbol">¥</text>
          <text class="price-value">{{ priceDisplay }}</text>
          <text class="price-unit">起</text>
        </view>
      </view>
    </view>

    <!-- 时间和地点信息（独立区域） -->
    <view class="event-details">
      <!-- 时间 -->
      <view class="detail-row">
        <text class="detail-text">{{ eventDateTime }}</text>
      </view>

      <!-- 地点 -->
      <view class="location-row" @tap="onViewLocation">
        <view class="location-icon">
          <text class="icon-text">📍</text>
        </view>
        <view class="location-content">
          <text class="location-name">{{ locationName }}</text>
          <text class="location-address">{{ locationAddress }}</text>
        </view>
        <text class="arrow-icon">›</text>
      </view>
    </view>

    <!-- 第二板块：参与人数 -->
    <view class="participants-wrapper">
      <view class="participants-section">
        <!-- 标题行 -->
        <view class="participants-header">
          <view class="participants-title" @tap="onViewParticipants">
            <text class="title-text">参与人数 {{ participantCount }}</text>
            <text class="arrow-icon">›</text>
          </view>
        </view>

        <!-- 参与者头像列表 -->
        <scroll-view class="participants-scroll" scroll-x>
          <view class="participants-list">
            <view class="participant-item" v-for="(participant, index) in participants" :key="index">
              <image class="participant-avatar" :src="participant.avatar" mode="aspectFill" />
              <text class="participant-name">{{ participant.name }}</text>
            </view>
          </view>
        </scroll-view>
      </view>
    </view>

    <!-- 第三板块：选项卡 -->
    <view class="tabs-wrapper">
      <view class="tabs-section">
        <!-- 选项卡头部 -->
        <view class="tabs-header">
          <view
            class="tab-item"
            :class="{ active: activeTab === 'detail' }"
            @tap="activeTab = 'detail'"
          >
            <text class="tab-text">活动详情</text>
            <view v-if="activeTab === 'detail'" class="tab-indicator"></view>
          </view>
          <view
            class="tab-item"
            :class="{ active: activeTab === 'notice' }"
            @tap="activeTab = 'notice'"
          >
            <text class="tab-text">报名须知</text>
            <view v-if="activeTab === 'notice'" class="tab-indicator"></view>
          </view>
        </view>

        <!-- 选项卡内容 -->
        <view class="tabs-content">
          <!-- 活动详情 -->
          <view v-if="activeTab === 'detail'" class="tab-panel">
            <rich-text v-if="detailContent" class="detail-content" :nodes="detailContent"></rich-text>
            <text v-else class="empty-text">暂无活动详情</text>
          </view>

          <!-- 报名须知 -->
          <view v-if="activeTab === 'notice'" class="tab-panel">
            <text class="notice-content">报名须知内容</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 底部固定操作栏 -->
    <view class="bottom-bar">
      <view class="action-buttons">
        <view class="action-btn" @tap="onShare">
          <text class="action-icon">📤</text>
          <text class="action-text">分享</text>
        </view>
        <view class="action-btn" @tap="onToggleFavorite">
          <text class="action-icon">{{ isFavorite ? '★' : '☆' }}</text>
          <text class="action-text">收藏</text>
        </view>
      </view>
      <view class="join-btn" @tap="onJoin">
        <text class="join-text">立即参与</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { getResourceDetail } from '../../../api/post'

const postCode = ref('')
const post = ref({})
const loading = ref(false)
const isFavorite = ref(false)
const activeTab = ref('detail')

const coverImage = computed(() => {
  const images = Array.isArray(post.value?.images) ? post.value.images : []
  return images.length > 0 ? String(images[0] || '').trim() : ''
})

const priceDisplay = computed(() => {
  const paymentType = String(post.value?.payment_type || 'free').trim()
  if (paymentType === 'free') {
    return '免费'
  }
  const price = String(post.value?.price || '0').trim()
  return price || '0'
})

const eventDateTime = computed(() => {
  const date = String(post.value?.event_date || '').trim()
  const time = String(post.value?.event_time || '').trim()
  if (!date) return '时间待定'

  try {
    const d = new Date(date)
    if (isNaN(d.getTime())) return date

    const year = d.getFullYear()
    const month = String(d.getMonth() + 1).padStart(2, '0')
    const day = String(d.getDate()).padStart(2, '0')
    const weekdays = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']
    const weekday = weekdays[d.getDay()]

    if (time) {
      return `${year}年${month}月${day}日 ${weekday} ${time}`
    }
    return `${year}年${month}月${day}日 ${weekday}`
  } catch {
    return date
  }
})

const locationName = computed(() => {
  const location = String(post.value?.location || '').trim()
  if (!location) return '地点待定'
  return location
})

const locationAddress = computed(() => {
  const address = String(post.value?.address || '').trim()
  return address || '闵厦'
})

const participantCount = computed(() => {
  return post.value?.participant_count || 0
})

const detailContent = computed(() => {
  const content = String(post.value?.detail_content || '').trim()
  if (!content) return ''

  // 为 HTML 内容添加内联样式，确保段落间距和换行显示
  let styledContent = content
    // 为所有 p 标签添加底部间距
    .replace(/<p>/g, '<p style="margin-bottom: 16rpx; line-height: 1.6;">')
    .replace(/<p style="/g, '<p style="margin-bottom: 16rpx; line-height: 1.6; ')
    // 为空的 p 标签添加最小高度，确保换行可见
    .replace(/<p([^>]*)><\/p>/g, '<p$1 style="min-height: 1em; margin-bottom: 16rpx;"></p>')
    .replace(/<p([^>]*)><br><\/p>/g, '<p$1 style="min-height: 1em; margin-bottom: 16rpx;"><br></p>')
    // 为 br 标签添加样式
    .replace(/<br>/g, '<br style="display: block; margin: 8rpx 0;">')
    .replace(/<br\/>/g, '<br style="display: block; margin: 8rpx 0;"/>')
    // 为图片添加样式
    .replace(/<img /g, '<img style="display: block; max-width: 100%; height: auto; margin: 16rpx 0;" ')

  return styledContent
})

// 模拟参与者数据（后续从API获取）
const participants = ref([
  { avatar: 'https://via.placeholder.com/100', name: '星座' },
  { avatar: 'https://via.placeholder.com/100', name: '小初' },
  { avatar: 'https://via.placeholder.com/100', name: 'Han' },
  { avatar: 'https://via.placeholder.com/100', name: 'sulli' },
  { avatar: 'https://via.placeholder.com/100', name: 'Yetta' },
  { avatar: 'https://via.placeholder.com/100', name: '菲猫🐱' }
])

const fetchDetail = async () => {
  if (!postCode.value) return

  loading.value = true
  try {
    const data = await getResourceDetail(postCode.value)
    post.value = data || {}

    // 打印活动详情全部信息
    console.log('========== 活动详情信息 ==========')
    console.log('完整数据:', JSON.stringify(data, null, 2))
    console.log('post_code:', data?.post_code)
    console.log('mode:', data?.mode)
    console.log('title:', data?.title)
    console.log('description:', data?.description)
    console.log('images:', data?.images)
    console.log('industry_label:', data?.industry_label)
    console.log('event_date:', data?.event_date)
    console.log('event_time:', data?.event_time)
    console.log('duration:', data?.duration)
    console.log('capacity:', data?.capacity)
    console.log('location:', data?.location)
    console.log('address:', data?.address)
    console.log('payment_type:', data?.payment_type)
    console.log('price:', data?.price)
    console.log('contact:', data?.contact)
    console.log('detail_content:', data?.detail_content)
    console.log('participant_count:', data?.participant_count)
    console.log('view_count:', data?.view_count)
    console.log('like_count:', data?.like_count)
    console.log('comment_count:', data?.comment_count)
    console.log('created_at:', data?.created_at)
    console.log('author:', data?.author)
    console.log('==================================')
  } catch (err) {
    console.error('加载活动详情失败:', err)
    uni.showToast({
      title: err?.message || '加载失败',
      icon: 'none'
    })
  } finally {
    loading.value = false
  }
}

const onToggleFavorite = () => {
  isFavorite.value = !isFavorite.value
  uni.showToast({
    title: isFavorite.value ? '已收藏' : '已取消收藏',
    icon: 'none'
  })
}

const onViewLocation = () => {
  const location = String(post.value?.location || '').trim()
  if (!location) {
    uni.showToast({
      title: '暂无地点信息',
      icon: 'none'
    })
    return
  }
  // TODO: 打开地图查看位置
  uni.showToast({
    title: '地图功能开发中',
    icon: 'none'
  })
}

const onViewParticipants = () => {
  uni.showToast({
    title: '查看参与者列表',
    icon: 'none'
  })
}

const onShare = () => {
  uni.showShareMenu({
    withShareTicket: true,
    success: () => {
      uni.showToast({
        title: '分享成功',
        icon: 'success'
      })
    },
    fail: () => {
      uni.showToast({
        title: '分享功能开发中',
        icon: 'none'
      })
    }
  })
}

const onJoin = () => {
  uni.showToast({
    title: '立即参与功能开发中',
    icon: 'none'
  })
}

onLoad((query = {}) => {
  postCode.value = String(query?.postCode || '').trim()
  if (postCode.value) {
    fetchDetail()
  }
})
</script>

<style scoped>
.venue-detail-page {
  min-height: 100vh;
  background: #f6f6f8;
}

.event-header {
  display: flex;
  padding: 24rpx 24rpx 0;
  gap: 20rpx;
  background: #ffffff;
}

/* 左侧海报 */
.poster-wrap {
  position: relative;
  width: 240rpx;
  height: 340rpx;
  flex-shrink: 0;
  border-radius: 12rpx;
  overflow: hidden;
}

.poster-image {
  width: 100%;
  height: 100%;
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  background: #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.placeholder-text {
  color: #999999;
  font-size: 24rpx;
}

.poster-tag {
  position: absolute;
  top: 12rpx;
  left: 12rpx;
  padding: 4rpx 12rpx;
  background: #ff6b35;
  border-radius: 6rpx;
  color: #ffffff;
  font-size: 20rpx;
  line-height: 28rpx;
  font-weight: 600;
}

/* 右侧信息 */
.event-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: 20rpx;
  min-width: 0;
}

.title-row {
  display: flex;
  align-items: flex-start;
  gap: 12rpx;
}

.event-title {
  flex: 1;
  color: #333333;
  font-size: 32rpx;
  line-height: 44rpx;
  font-weight: 600;
  min-width: 0;
  word-break: break-all;
}

.favorite-btn {
  width: 48rpx;
  height: 48rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.favorite-icon {
  color: #ff6b35;
  font-size: 40rpx;
  line-height: 1;
}

.price-row {
  display: flex;
  align-items: baseline;
  gap: 4rpx;
}

.price-symbol {
  color: #ff6b35;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 600;
}

.price-value {
  color: #ff6b35;
  font-size: 48rpx;
  line-height: 56rpx;
  font-weight: 700;
}

.price-unit {
  color: #ff6b35;
  font-size: 24rpx;
  line-height: 40rpx;
  font-weight: 500;
}

/* 时间和地点区域 */
.event-details {
  padding: 24rpx;
  background: #ffffff;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.detail-row {
  display: flex;
  align-items: center;
}

.detail-text {
  color: #666666;
  font-size: 24rpx;
  line-height: 34rpx;
  font-weight: 400;
}

.location-row {
  display: flex;
  align-items: flex-start;
  gap: 8rpx;
}

.location-icon {
  width: 32rpx;
  height: 32rpx;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-text {
  font-size: 24rpx;
  line-height: 1;
}

.location-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4rpx;
  min-width: 0;
}

.location-name {
  color: #333333;
  font-size: 26rpx;
  line-height: 36rpx;
  font-weight: 500;
}

.location-address {
  color: #999999;
  font-size: 22rpx;
  line-height: 30rpx;
  font-weight: 400;
}

.arrow-icon {
  color: #999999;
  font-size: 32rpx;
  line-height: 32rpx;
  flex-shrink: 0;
  margin-top: 2rpx;
}

/* 参与人数板块 */
.participants-wrapper {
  padding: 24rpx;
  background: #f6f6f8;
}

.participants-section {
  padding: 24rpx;
  background: #ffffff;
  border-radius: 16rpx;
}

.participants-header {
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
}

.participants-title {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.title-text {
  color: #333333;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 600;
}

.participants-scroll {
  white-space: nowrap;
}

.participants-list {
  display: inline-flex;
  gap: 24rpx;
}

.participant-item {
  display: inline-flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
}

.participant-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  background: #f0f0f0;
}

.participant-name {
  color: #666666;
  font-size: 22rpx;
  line-height: 30rpx;
  font-weight: 400;
  max-width: 96rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 选项卡板块 */
.tabs-wrapper {
  padding: 0 24rpx;
  background: #f6f6f8;
}

.tabs-section {
  background: #ffffff;
  border-radius: 16rpx;
  overflow: hidden;
}

.tabs-header {
  display: flex;
  border-bottom: 1rpx solid #e5e5e5;
  padding: 0 24rpx;
}

.tab-item {
  position: relative;
  padding: 24rpx 32rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.tab-text {
  color: #999999;
  font-size: 28rpx;
  line-height: 40rpx;
  font-weight: 500;
  transition: color 0.3s;
}

.tab-item.active .tab-text {
  color: #333333;
  font-weight: 600;
}

.tab-indicator {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 4rpx;
  background: #ff6b35;
  border-radius: 2rpx;
}

.tabs-content {
  padding: 24rpx;
  padding-bottom: 120rpx;
}

.tab-panel {
  min-height: 200rpx;
}

.detail-content,
.notice-content {
  color: #666666;
  font-size: 26rpx;
  line-height: 40rpx;
  font-weight: 400;
  word-break: break-all;
}

.detail-content {
  width: 100%;
}

/* rich-text 内部样式 */
.detail-content :deep(p) {
  margin: 0 0 20rpx 0;
  line-height: 40rpx;
}

.detail-content :deep(p:last-child) {
  margin-bottom: 0;
}

.detail-content :deep(img) {
  display: block;
  max-width: 100%;
  height: auto;
  margin: 20rpx 0;
}

.detail-content :deep(br) {
  display: block;
  content: "";
  margin: 10rpx 0;
}

.empty-text {
  color: #999999;
  font-size: 26rpx;
  line-height: 40rpx;
  text-align: center;
  display: block;
  padding: 60rpx 0;
}

/* 底部固定操作栏 */
.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 24rpx;
  padding-bottom: calc(16rpx + env(safe-area-inset-bottom));
  background: #ffffff;
  border-top: 1rpx solid #e5e5e5;
  z-index: 100;
}

.action-buttons {
  flex: 0.5;
  display: flex;
  gap: 32rpx;
}

.action-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4rpx;
}

.action-icon {
  font-size: 40rpx;
  line-height: 1;
  color: #666666;
}

.action-text {
  color: #666666;
  font-size: 20rpx;
  line-height: 28rpx;
  font-weight: 400;
}

.join-btn {
  flex: 1;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #ff6b35 0%, #ff8c42 100%);
  border-radius: 40rpx;
}

.join-text {
  color: #ffffff;
  font-size: 32rpx;
  line-height: 44rpx;
  font-weight: 600;
}
</style>
