<template>
  <view class="tabs-wrap">
    <view
      v-for="tab in tabs"
      :key="tab.key"
      class="tab-item"
      :class="activeKey === tab.key ? 'tab-item-active' : ''"
      @tap="$emit('change', tab.key)"
    >
      <text class="tab-text" :class="activeKey === tab.key ? 'tab-text-active' : ''">{{ tab.label }}</text>
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
  display: flex;
  align-items: center;
  gap: 40rpx;
  padding: 0 32rpx;
  border-bottom: 1rpx solid #e2e8f0;
  background: #ffffff;
}

.tab-item {
  padding: 24rpx 0 18rpx;
  border-bottom: 4rpx solid transparent;
}

.tab-item-active {
  border-bottom-color: #1a57db;
}

.tab-text {
  color: #64748b;
  font-size: 26rpx;
  line-height: 34rpx;
  font-weight: 700;
  letter-spacing: 0.6rpx;
}

.tab-text-active {
  color: #1a57db;
}

@media (prefers-color-scheme: dark) {
  .tabs-wrap {
    background: rgba(15, 23, 42, 0.92);
    border-bottom-color: #1e293b;
  }

  .tab-text {
    color: #94a3b8;
  }

  .tab-text-active {
    color: #7aa2ff;
  }
}
</style>
