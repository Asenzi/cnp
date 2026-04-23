<template>
  <view class="service-grid">
    <view v-for="item in items" :key="item.key" class="service-item" hover-class="service-item-active" @tap="onTap(item)">
      <view class="service-icon-box" :class="item.colorClass">
        <image class="service-icon-img" mode="aspectFit" :src="item.iconPath" />
      </view>
      <text class="service-label">{{ item.label }}</text>
    </view>
  </view>
</template>

<script setup>
const props = defineProps({
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
.service-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 20rpx;
}

.service-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10rpx;
}

.service-item-active {
  opacity: 0.82;
}

.service-icon-box {
  width: 88rpx;
  height: 88rpx;
  border-radius: 999rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.service-icon-img {
  width: 40rpx;
  height: 40rpx;
}

.service-blue {
  color: #2563eb;
  background: #eff6ff;
}

.service-orange {
  color: #ea580c;
  background: #fff7ed;
}

.service-green {
  color: #16a34a;
  background: #f0fdf4;
}

.service-purple {
  color: #9333ea;
  background: #faf5ff;
}

.service-label {
  font-size: 22rpx;
  color: #475569;
}

@media (prefers-color-scheme: dark) {
  .service-label {
    color: #94a3b8;
  }

  .service-blue {
    background: rgba(37, 99, 235, 0.2);
    color: #60a5fa;
  }

  .service-orange {
    background: rgba(234, 88, 12, 0.2);
    color: #fb923c;
  }

  .service-green {
    background: rgba(22, 163, 74, 0.2);
    color: #4ade80;
  }

  .service-purple {
    background: rgba(147, 51, 234, 0.2);
    color: #c084fc;
  }
}
</style>
