<template>
  <view class="empty-wrap">
    <text class="empty-title">未找到匹配圈子</text>
    <text class="empty-subtitle">试试其他关键词</text>
  </view>
</template>

<style scoped>
.empty-wrap {
  margin-top: 28rpx;
  border-radius: 16rpx;
  border: 1rpx dashed #cbd5e1;
  background: #ffffff;
  min-height: 180rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.empty-title {
  color: #334155;
  font-size: 26rpx;
  line-height: 34rpx;
  font-weight: 600;
}

.empty-subtitle {
  margin-top: 6rpx;
  color: #94a3b8;
  font-size: 22rpx;
  line-height: 30rpx;
}

@media (prefers-color-scheme: dark) {
  .empty-wrap {
    background: #0f172a;
    border-color: #334155;
  }

  .empty-title {
    color: #cbd5e1;
  }

  .empty-subtitle {
    color: #64748b;
  }
}
</style>
