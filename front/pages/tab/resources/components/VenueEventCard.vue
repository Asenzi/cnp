<template>
  <view class="venue-card" hover-class="venue-card-active" @tap="$emit('detail', item)">
    <!-- 上半部分：海报 + 内容 -->
    <view class="card-top">
      <!-- 左侧海报 -->
      <view class="poster-wrap">
        <image
          v-if="item.coverImage"
          class="poster-image"
          :src="item.coverImage"
          mode="aspectFill"
        />
        <view v-else class="poster-placeholder">
          <text class="placeholder-icon">🎭</text>
        </view>
      </view>

      <!-- 右侧内容 -->
      <view class="content-wrap">
        <!-- 标题 -->
        <text class="event-title">{{ item.title }}</text>

        <!-- 标签 -->
        <view v-if="item.industryLabels?.length" class="tag-badge">
          <text class="tag-text">{{ item.industryLabels[0] }}</text>
        </view>

        <!-- 时间 -->
        <view class="info-row">
          <text class="info-icon">🕐</text>
          <text class="info-text">{{ item.eventTime || '待定' }}</text>
        </view>

        <!-- 地点 -->
        <view v-if="item.location" class="info-row">
          <text class="info-icon">📍</text>
          <text class="info-text">{{ item.location }}</text>
        </view>
      </view>
    </view>

    <!-- 下半部分：组织者 + 参与人数 -->
    <view class="card-bottom">
      <!-- 左侧组织者 -->
      <view class="organizer-info">
        <image
          v-if="item.avatar"
          class="organizer-avatar"
          :src="item.avatar"
          mode="aspectFill"
        />
        <view v-else class="organizer-avatar organizer-avatar-placeholder">
          <text class="avatar-text">{{ item.userName?.charAt(0) || '?' }}</text>
        </view>
        <text class="organizer-name">{{ item.userName || '匿名' }}</text>
      </view>

      <!-- 右侧参与人数 -->
      <view class="participants-info">
        <text class="participants-count">{{ participantText }}</text>
        <view v-if="participantAvatars.length" class="participants-avatars">
          <image
            v-for="(avatar, idx) in participantAvatars"
            :key="`avatar-${idx}`"
            class="participant-avatar"
            :src="avatar"
            mode="aspectFill"
          />
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  item: {
    type: Object,
    default: () => ({})
  },
  showInterest: {
    type: Boolean,
    default: false
  }
})

defineEmits(['detail', 'interest'])

const participantText = computed(() => {
  const current = Number(props.item?.participants || 0)
  return `${current}人参加`
})

const participantAvatars = computed(() => {
  // 从 item 中获取参与者头像列表，最多显示3个
  const avatars = props.item?.participantAvatars || []
  return Array.isArray(avatars) ? avatars.slice(0, 3) : []
})
</script>

<style scoped>
.venue-card {
  display: flex;
  flex-direction: column;
  background: #ffffff;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 16rpx rgba(15, 23, 42, 0.06);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  padding: 24rpx;
  gap: 20rpx;
}

.venue-card-active {
  transform: translateY(-2rpx);
  box-shadow: 0 8rpx 24rpx rgba(15, 23, 42, 0.1);
}

/* 上半部分 */
.card-top {
  display: flex;
  gap: 20rpx;
}

/* 左侧海报 */
.poster-wrap {
  width: 180rpx;
  height: 240rpx;
  flex-shrink: 0;
  border-radius: 16rpx;
  overflow: hidden;
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
}

.poster-image {
  width: 100%;
  height: 100%;
}

.poster-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e2e8f0 0%, #cbd5e1 100%);
}

.placeholder-icon {
  font-size: 64rpx;
  opacity: 0.5;
}

/* 右侧内容 */
.content-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
  min-width: 0;
}

.event-title {
  display: block;
  color: #0f172a;
  font-size: 30rpx;
  line-height: 42rpx;
  font-weight: 600;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.tag-badge {
  display: inline-flex;
  align-self: flex-start;
  padding: 4rpx 12rpx;
  border-radius: 6rpx;
  background: #e0f2fe;
  margin-top: 10rpx;
}

.tag-text {
  color: #0284c7;
  font-size: 20rpx;
  line-height: 28rpx;
  font-weight: 500;
}

/* 信息行 */
.info-row {
  display: flex;
  align-items: center;
  gap: 6rpx;
  margin-top: 10rpx;
}

.info-icon {
  font-size: 24rpx;
  line-height: 1;
  flex-shrink: 0;
}

.info-text {
  flex: 1;
  color: #64748b;
  font-size: 24rpx;
  line-height: 32rpx;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 下半部分 */
.card-bottom {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16rpx;
  padding: 16rpx;
  background: linear-gradient(135deg, #ffffff 0%, #e0f2fe 100%);
  border-radius: 0 0 22rpx 12rpx;
}

/* 组织者信息 */
.organizer-info {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex: 1;
  min-width: 0;
}

.organizer-avatar {
  width: 48rpx;
  height: 48rpx;
  border-radius: 24rpx;
  flex-shrink: 0;
}

.organizer-avatar-placeholder {
  background: linear-gradient(135deg, #94a3b8 0%, #64748b 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-text {
  color: #ffffff;
  font-size: 20rpx;
  font-weight: 600;
}

.organizer-name {
  flex: 1;
  color: #0f172a;
  font-size: 22rpx;
  line-height: 30rpx;
  font-weight: 500;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 参与者信息 */
.participants-info {
  display: flex;
  align-items: center;
  gap: 8rpx;
  flex-shrink: 0;
}

.participants-count {
  color: #1a57db;
  font-size: 26rpx;
  line-height: 34rpx;
  font-weight: 600;
}

.participants-avatars {
  display: flex;
  align-items: center;
}

.participant-avatar {
  width: 40rpx;
  height: 40rpx;
  border-radius: 20rpx;
  border: 2rpx solid #ffffff;
  margin-left: -12rpx;
}

.participant-avatar:first-child {
  margin-left: 0;
}

@media (prefers-color-scheme: dark) {
  .venue-card {
    background: #1e293b;
    box-shadow: 0 2rpx 16rpx rgba(0, 0, 0, 0.3);
  }

  .venue-card-active {
    box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.4);
  }

  .poster-wrap {
    background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
  }

  .poster-placeholder {
    background: linear-gradient(135deg, #334155 0%, #475569 100%);
  }

  .event-title {
    color: #f1f5f9;
  }

  .info-text {
    color: #94a3b8;
  }

  .card-bottom {
    border-top-color: #334155;
  }

  .organizer-name {
    color: #f1f5f9;
  }

  .participant-avatar {
    border-color: #1e293b;
  }
}
</style>
