<template>
  <view class="status-card">
    <view class="status-glow"></view>

    <view class="status-top">
      <view>
        <text class="status-title">尊享会员 VIP</text>
        <text class="status-subtitle">全脉联 · 商务社交首选</text>
      </view>
      <view class="status-pill">
        <text class="status-pill-text">{{ status?.statusText || '未开通' }}</text>
      </view>
    </view>

    <view class="status-bottom">
      <view>
        <text class="status-expire">有效期至：{{ status?.expireDateText || '--' }}</text>
        <text class="status-slogan">升级会员，解锁无限商机</text>
      </view>
      <image class="status-vip-icon" mode="aspectFit" src="/static/me-icons/badge-primary.png" />
    </view>
  </view>
</template>

<script setup>
defineProps({
  status: {
    type: Object,
    default: () => ({})
  }
})
</script>

<style scoped>
.status-card {
  position: relative;
  overflow: hidden;
  border-radius: 12px;
  padding: 24px;
  background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
  border: 1px solid rgba(51, 65, 85, 0.6);
  box-shadow: 0 10px 22px rgba(15, 23, 42, 0.22);
}

.status-glow {
  position: absolute;
  width: 180px;
  height: 180px;
  right: -70px;
  top: -70px;
  border-radius: 999px;
  background: rgba(212, 175, 55, 0.1);
}

.status-top {
  position: relative;
  z-index: 1;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 14px;
}

.status-title {
  display: block;
  font-size: 19px;
  line-height: 32px;
  font-weight: 800;
  letter-spacing: 0.4px;
  background: linear-gradient(to right, #fde68a, #d4af37);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}

.status-subtitle {
  display: block;
  margin-top: 4px;
  color: #94a3b8;
  font-size: 7px;
  line-height: 18px;
}

.status-pill {
  flex-shrink: 0;
  border-radius: 999px;
  border: 1px solid rgba(212, 175, 55, 0.4);
  background: rgba(212, 175, 55, 0.18);
  padding: 4px 12px;
}

.status-pill-text {
  color: #d4af37;
  font-size: 7px;
  line-height: 18px;
  font-weight: 700;
}

.status-bottom {
  position: relative;
  z-index: 1;
  margin-top: 28px;
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: 12px;
}

.status-expire {
  display: block;
  color: #cbd5e1;
  font-size: 9px;
  line-height: 22px;
}

.status-slogan {
  display: block;
  margin-top: 6px;
  color: #e2e8f0;
  font-size: 11px;
  line-height: 24px;
  font-style: italic;
  font-weight: 500;
}

.status-vip-icon {
  width: 54px;
  height: 54px;
  opacity: 0.48;
  flex-shrink: 0;
}
</style>
