<script setup lang="ts">
import type { AdminSettlementAccountItem, PageResult } from '#/api/admin';

import { onMounted, reactive, ref } from 'vue';

import {
  ElButton,
  ElCard,
  ElForm,
  ElFormItem,
  ElInput,
  ElPagination,
  ElTable,
  ElTableColumn,
} from 'element-plus';

import { listAdminSettlementAccountsApi } from '#/api/admin';
import { formatAmount, formatDateTime } from '#/utils/admin';

defineOptions({ name: 'AdminSettlementAccountsPage' });

const loading = ref(false);
const filters = reactive({
  keyword: '',
  page: 1,
  page_size: 12,
});
const pageData = ref<PageResult<AdminSettlementAccountItem>>({
  items: [],
  page: 1,
  page_size: 12,
  total: 0,
});

async function loadAccounts(page = filters.page) {
  filters.page = page;
  loading.value = true;
  try {
    pageData.value = await listAdminSettlementAccountsApi({
      keyword: filters.keyword.trim() || undefined,
      page: filters.page,
      page_size: filters.page_size,
    });
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadAccounts();
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">结算账户</h1>
      <p class="text-sm text-slate-500">
        查看圈主收益账户，当前展示付费入圈自动结算后的可结算收益。
      </p>
    </div>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElForm inline class="flex flex-wrap gap-x-4">
        <ElFormItem label="关键词">
          <ElInput
            v-model="filters.keyword"
            clearable
            placeholder="搜索用户ID / 昵称 / 手机"
            style="width: 320px"
            @keyup.enter="loadAccounts(1)"
          />
        </ElFormItem>
        <ElFormItem>
          <ElButton type="primary" @click="loadAccounts(1)">查询</ElButton>
        </ElFormItem>
      </ElForm>
    </ElCard>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElTable
        v-loading="loading"
        :data="pageData.items"
        empty-text="暂无结算账户"
        row-key="id"
        stripe
      >
        <ElTableColumn label="用户" min-width="180">
          <template #default="{ row }">
            {{ row.nickname || '--' }} ({{ row.user_id || '--' }})
          </template>
        </ElTableColumn>
        <ElTableColumn label="手机号" min-width="130" prop="phone" />
        <ElTableColumn label="可结算收益" width="130">
          <template #default="{ row }">¥{{ formatAmount(row.available_balance) }}</template>
        </ElTableColumn>
        <ElTableColumn label="冻结金额" width="120">
          <template #default="{ row }">¥{{ formatAmount(row.frozen_balance) }}</template>
        </ElTableColumn>
        <ElTableColumn label="累计收益" width="120">
          <template #default="{ row }">¥{{ formatAmount(row.total_income) }}</template>
        </ElTableColumn>
        <ElTableColumn label="已提现" width="120">
          <template #default="{ row }">¥{{ formatAmount(row.total_withdrawn) }}</template>
        </ElTableColumn>
        <ElTableColumn label="更新时间" min-width="160">
          <template #default="{ row }">{{ formatDateTime(row.updated_at) }}</template>
        </ElTableColumn>
      </ElTable>

      <div class="mt-4 flex justify-end">
        <ElPagination
          :current-page="pageData.page"
          :page-size="pageData.page_size"
          :total="pageData.total"
          background
          layout="total, prev, pager, next"
          @current-change="loadAccounts"
        />
      </div>
    </ElCard>
  </div>
</template>
