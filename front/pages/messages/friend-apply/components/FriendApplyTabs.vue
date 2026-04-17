<template>
  <view class="tabs-wrap">
    <view
      v-for="item in tabs"
      :key="item.key"
      class="tab-item"
      @tap="$emit('change', item.key)"
    >
      <text class="tab-text" :class="activeKey === item.key ? 'tab-text-active' : ''">{{ item.label }}</text>
      <view v-if="activeKey === item.key" class="tab-line"></view>
    </view>
  </view>
</template>

<script setup>
defineProps({
  tabs: {
    type: Array,
    default: () => []
  },
  activeKey: {
    type: String,
    default: ''
  }
})

defineEmits(['change'])
</script>

<style scoped>
.tabs-wrap {
  background: #f8f6f6;
  border-bottom: 1rpx solid rgba(26, 87, 219, 0.1);
  display: flex;
  align-items: center;
  gap: 48rpx;
  padding: 0 24rpx;
}

.tab-item {
  position: relative;
  height: 76rpx;
  display: inline-flex;
  align-items: center;
}

.tab-text {
  color: #64748b;
  font-size: 28rpx;
  line-height: 36rpx;
  font-weight: 500;
}

.tab-text-active {
  color: #1a57db;
  font-weight: 700;
}

.tab-line {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  height: 4rpx;
  background: #1a57db;
  border-radius: 999rpx;
}

@media (prefers-color-scheme: dark) {
  .tabs-wrap {
    background: #221610;
    border-bottom-color: rgba(59, 130, 246, 0.22);
  }

  .tab-text {
    color: #9ca3af;
  }

  .tab-text-active {
    color: #60a5fa;
  }

  .tab-line {
    background: #60a5fa;
  }
}
</style>
