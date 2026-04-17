<template>
  <view class="benefit-grid">
    <view v-for="item in items" :key="item.key" class="benefit-item" :class="{ 'benefit-item-wide': item.wide }">
      <view class="benefit-icon-wrap">
        <image v-if="item.iconPath" class="benefit-icon-img" mode="aspectFit" :src="item.iconPath" />
        <text v-else class="benefit-icon-text">{{ item.iconText || '会' }}</text>
      </view>
      <view class="benefit-main">
        <text class="benefit-title">{{ item.title }}</text>
        <text class="benefit-desc">{{ item.desc }}</text>
      </view>
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
</script>

<style scoped>
.benefit-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.benefit-item {
  border-radius: 12px;
  border: 1px solid #e2e8f0;
  background: #ffffff;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 12px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.benefit-item-wide {
  grid-column: span 2 / span 2;
  flex-direction: row;
  align-items: center;
  gap: 14px;
}

.benefit-icon-wrap {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  background: rgba(26, 87, 219, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.benefit-icon-img {
  width: 23px;
  height: 23px;
}

.benefit-icon-text {
  color: #1a57db;
  font-size: 15px;
  line-height: 1;
  font-weight: 700;
}

.benefit-main {
  flex: 1;
  min-width: 0;
}

.benefit-title {
  display: block;
  color: #0f172a;
  font-size: 13px;
  line-height: 20px;
  font-weight: 700;
}

.benefit-desc {
  display: block;
  margin-top: 3px;
  color: #64748b;
  font-size: 11px;
  line-height: 18px;
}

@media (prefers-color-scheme: dark) {
  .benefit-item {
    background: #0f172a;
    border-color: #1e293b;
  }

  .benefit-title {
    color: #e2e8f0;
  }

  .benefit-desc {
    color: #94a3b8;
  }

  .benefit-icon-wrap {
    background: rgba(26, 87, 219, 0.25);
  }

  .benefit-icon-text {
    color: #93c5fd;
  }
}
</style>
