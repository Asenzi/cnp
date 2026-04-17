<template>
  <view class="action-row" hover-class="action-row-active" @tap="$emit('tap', item)">
    <view class="icon-box" :class="iconBoxClass">
      <MessageGlyph :name="item.icon" :size="22" :color="iconColor" />
      <view v-if="item.badge > 0" class="badge">{{ item.badge }}</view>
    </view>

    <view class="main">
      <text class="title">{{ item.title }}</text>
      <text class="preview">{{ item.preview }}</text>
    </view>

    <view class="chevron-wrap">
      <MessageGlyph name="chevron_right" :size="16" color="#cbd5e1" />
    </view>
  </view>
</template>

<script setup>
import { computed } from 'vue'
import MessageGlyph from './MessageGlyph.vue'

const props = defineProps({
  item: {
    type: Object,
    default: () => ({})
  }
})

defineEmits(['tap'])

const iconBoxClass = computed(() => {
  if (props.item?.iconTone === 'orange') return 'icon-box-orange'
  if (props.item?.iconTone === 'primary') return 'icon-box-primary'
  return 'icon-box-gray'
})

const iconColor = computed(() => {
  if (props.item?.iconTone === 'orange') return '#f97316'
  if (props.item?.iconTone === 'primary') return '#1a57db'
  return '#64748b'
})
</script>

<style scoped>
.action-row {
  min-height: 112rpx;
  padding: 22rpx 28rpx;
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.action-row-active {
  background: #f8fafc;
}

.icon-box {
  position: relative;
  width: 88rpx;
  height: 88rpx;
  border-radius: 18rpx;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.icon-box-orange {
  background: rgba(251, 146, 60, 0.18);
}

.icon-box-primary {
  background: rgba(26, 87, 219, 0.12);
}

.icon-box-gray {
  background: #e2e8f0;
}

.badge {
  position: absolute;
  top: -6rpx;
  right: -6rpx;
  min-width: 34rpx;
  height: 34rpx;
  padding: 0 8rpx;
  border-radius: 999rpx;
  background: #ef4444;
  color: #ffffff;
  font-size: 18rpx;
  line-height: 34rpx;
  font-weight: 700;
  text-align: center;
  border: 2rpx solid #ffffff;
}

.main {
  flex: 1;
  min-width: 0;
}

.title {
  display: block;
  color: #0f172a;
  font-size: 30rpx;
  line-height: 38rpx;
  font-weight: 600;
}

.preview {
  display: block;
  margin-top: 4rpx;
  color: #64748b;
  font-size: 22rpx;
  line-height: 30rpx;
  overflow: hidden;
  white-space: nowrap;
  text-overflow: ellipsis;
}

.chevron-wrap {
  width: 24rpx;
  height: 24rpx;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

@media (prefers-color-scheme: dark) {
  .action-row-active {
    background: #111827;
  }

  .badge {
    border-color: #0f172a;
  }

  .title {
    color: #f8fafc;
  }

  .preview {
    color: #94a3b8;
  }
}
</style>
