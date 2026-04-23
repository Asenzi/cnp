<script setup lang="ts">
import { computed } from 'vue';

import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElTag,
} from 'element-plus';

import { useUserStore } from '@vben/stores';

import { formatRoleLabel } from '#/api/admin';
import { formatDateTime } from '#/utils/admin';

defineOptions({ name: 'AdminProfilePage' });

const userStore = useUserStore();

const roleLabel = computed(() => {
  const role = String(userStore.userInfo?.roles?.[0] || 'super_admin');
  return formatRoleLabel(role);
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">管理员资料</h1>
      <p class="text-sm text-slate-500">
        当前登录管理员的账户和角色信息。
      </p>
    </div>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElDescriptions :column="2" border>
        <ElDescriptionsItem label="显示名称">
          {{ userStore.userInfo?.realName || '--' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="账号">
          {{ userStore.userInfo?.username || '--' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="管理员ID">
          {{ userStore.userInfo?.userId || '--' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="角色">
          <ElTag type="success">{{ roleLabel }}</ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="默认首页">
          {{ userStore.userInfo?.homePath || '--' }}
        </ElDescriptionsItem>
        <ElDescriptionsItem label="最近登录">
          {{ formatDateTime(userStore.userInfo?.lastLoginAt) }}
        </ElDescriptionsItem>
      </ElDescriptions>
    </ElCard>
  </div>
</template>
