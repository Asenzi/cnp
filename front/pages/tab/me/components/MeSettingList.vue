<template>
  <view class="setting-list">
    <view
      v-for="item in items"
      :key="item.key"
      class="setting-item"
      hover-class="setting-item-active"
      @tap="onTap(item)"
    >
      <view class="setting-left">
        <image class="setting-icon-img" mode="aspectFit" :src="item.iconPath" />
        <text class="setting-text">{{ item.label }}</text>
      </view>
      <image class="chevron-img" mode="aspectFit" src="/static/me-icons/chevron-light.png" />
    </view>
  </view>
</template>

<script setup>
defineProps({
  items: {
    type: Array,
    default: () => []
  }
})

const emit = defineEmits(['tap-item'])

const onTap = (item) => {
  emit('tap-item', item)
}
</script>

<style scoped>
.setting-list {
  display: flex;
  flex-direction: column;
  gap: 2rpx;
}

.setting-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20rpx 24rpx;
  border-radius: 12rpx;
}

.setting-item-active {
  background: #f8fafc;
}

.setting-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.setting-icon-img {
  width: 36rpx;
  height: 36rpx;
}

.setting-text {
  font-size: 28rpx;
  color: #334155;
}

.chevron-img {
  width: 32rpx;
  height: 32rpx;
}

@media (prefers-color-scheme: dark) {
  .setting-item {
    background: transparent;
  }

  .setting-item-active {
    background: rgba(30, 41, 59, 0.6);
  }

  .setting-text {
    color: #cbd5e1;
  }
}
</style>
