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
  padding: 0 32rpx;
  border-bottom: 1rpx solid #f3f4f6;
  background: #ffffff;
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  gap: 40rpx;
}

.tab-item {
  height: 88rpx;
  display: inline-flex;
  align-items: center;
  border-bottom: 2rpx solid transparent;
}

.tab-item-active {
  border-bottom-color: #2563eb;
}

.tab-text {
  color: #6b7280;
  font-size: 28rpx;
  line-height: 36rpx;
}

.tab-text-active {
  color: #111827;
  font-weight: 500;
}

@media (prefers-color-scheme: dark) {
  .tabs-wrap {
    background: #111827;
    border-bottom-color: #1f2937;
  }

  .tab-text {
    color: #9ca3af;
  }

  .tab-text-active {
    color: #f9fafb;
  }

  .tab-item-active {
    border-bottom-color: #3b82f6;
  }
}
</style>
