<template>
  <view class="tabs-wrap">
    <view
      v-for="(item, index) in tabs"
      :key="item.key"
      class="tab-item"
      :class="{ 'tab-item-active': activeIndex === index }"
      @tap="emit('change', index)"
    >
      <text class="tab-text" :class="{ 'tab-text-active': activeIndex === index }">{{ item.label }}</text>
    </view>
  </view>
</template>

<script setup>
defineProps({
  tabs: {
    type: Array,
    default: () => []
  },
  activeIndex: {
    type: Number,
    default: 0
  }
})

const emit = defineEmits(['change'])
</script>

<style scoped>
.tabs-wrap {
  margin-top: 24rpx;
  padding: 0 32rpx;
  border-bottom: 1rpx solid #e2e8f0;
  background: #f6f6f8;
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  gap: 40rpx;
}

.tab-item {
  height: 74rpx;
  display: inline-flex;
  align-items: center;
  border-bottom: 4rpx solid transparent;
}

.tab-item-active {
  border-bottom-color: #1a57db;
}

.tab-text {
  color: #64748b;
  font-size: 24rpx;
  line-height: 32rpx;
  font-weight: 500;
}

.tab-text-active {
  color: #1a57db;
  font-weight: 700;
}

@media (prefers-color-scheme: dark) {
  .tabs-wrap {
    background: #111621;
    border-bottom-color: #1e293b;
  }

  .tab-text {
    color: #94a3b8;
  }
}
</style>

