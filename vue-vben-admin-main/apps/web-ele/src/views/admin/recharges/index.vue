<script setup lang="ts">
import type { AdminRechargeItem, PageResult } from '#/api/admin';

import { onMounted, reactive, ref } from 'vue';

import {
  ElButton,
  ElCard,
  ElForm,
  ElFormItem,
  ElInput,
  ElOption,
  ElPagination,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import { listAdminRechargesApi } from '#/api/admin';
import {
  formatAmount,
  formatDateTime,
  resolveStatusTagType,
} from '#/utils/admin';

defineOptions({ name: 'AdminRechargesPage' });

const loading = ref(false);
const filters = reactive({
  keyword: '',
  page: 1,
  page_size: 12,
  status: '',
});
const pageData = ref<PageResult<AdminRechargeItem>>({
  items: [],
  page: 1,
  page_size: 12,
  total: 0,
});

async function loadRecharges(page = filters.page) {
  filters.page = page;
  loading.value = true;
  try {
    pageData.value = await listAdminRechargesApi({
      keyword: filters.keyword.trim() || undefined,
      page: filters.page,
      page_size: filters.page_size,
      status: filters.status || undefined,
    });
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  void loadRecharges();
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">充值订单</h1>
      <p class="text-sm text-slate-500">
        查看钱包充值订单、支付状态和金额流水。
      </p>
    </div>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElForm inline class="flex flex-wrap gap-x-4">
        <ElFormItem label="关键词">
          <ElInput
            v-model="filters.keyword"
            clearable
            placeholder="搜索订单号 / 流水号 / 用户 / 手机"
            style="width: 320px"
            @keyup.enter="loadRecharges(1)"
          />
        </ElFormItem>
        <ElFormItem label="状态">
          <ElSelect v-model="filters.status" clearable style="width: 160px">
            <ElOption label="全部" value="" />
            <ElOption label="pending" value="pending" />
            <ElOption label="paid" value="paid" />
            <ElOption label="failed" value="failed" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem>
          <ElButton type="primary" @click="loadRecharges(1)">查询</ElButton>
        </ElFormItem>
      </ElForm>
    </ElCard>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElTable
        v-loading="loading"
        :data="pageData.items"
        empty-text="暂无充值订单"
        row-key="id"
        stripe
      >
        <ElTableColumn label="订单号" min-width="190" prop="order_no" />
        <ElTableColumn label="用户" min-width="200">
          <template #default="{ row }">
            {{ row.nickname || '--' }} ({{ row.user_id || '--' }})
          </template>
        </ElTableColumn>
        <ElTableColumn label="金额" width="100">
          <template #default="{ row }">
            {{ formatAmount(row.amount) }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="渠道" min-width="120" prop="pay_channel" />
        <ElTableColumn label="状态" width="100">
          <template #default="{ row }">
            <ElTag :type="resolveStatusTagType(row.status)">
              {{ row.status }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="创建时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="支付时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.paid_at) }}
          </template>
        </ElTableColumn>
      </ElTable>

      <div class="mt-4 flex justify-end">
        <ElPagination
          :current-page="pageData.page"
          :page-size="pageData.page_size"
          :total="pageData.total"
          background
          layout="total, prev, pager, next"
          @current-change="loadRecharges"
        />
      </div>
    </ElCard>
  </div>
</template>
