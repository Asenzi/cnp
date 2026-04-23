<script setup lang="ts">
import type { AdminUserItem, PageResult } from '#/api/admin';

import dayjs from 'dayjs';
import { onMounted, reactive, ref } from 'vue';

import {
  ElButton,
  ElCard,
  ElDatePicker,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElMessageBox,
  ElOption,
  ElPagination,
  ElSelect,
  ElTable,
  ElTableColumn,
  ElTag,
} from 'element-plus';

import { listAdminUsersApi, updateAdminUserStatusApi } from '#/api/admin';
import { formatDateTime } from '#/utils/admin';

defineOptions({ name: 'AdminUsersPage' });

const loading = ref(false);
const actionLoadingId = ref<number | null>(null);
const filters = reactive({
  is_active: '' as '' | boolean,
  is_verified: '' as '' | boolean,
  keyword: '',
  page: 1,
  page_size: 12,
  registered_at_range: [] as string[],
});
const pageData = ref<PageResult<AdminUserItem>>({
  items: [],
  page: 1,
  page_size: 12,
  total: 0,
});

function resolveCreatedAtFilters() {
  if (filters.registered_at_range.length !== 2) {
    return {
      created_from: undefined,
      created_to: undefined,
    };
  }

  const [startDate, endDate] = filters.registered_at_range;
  return {
    created_from: dayjs(startDate).startOf('day').format('YYYY-MM-DDTHH:mm:ss'),
    created_to: dayjs(endDate).endOf('day').format('YYYY-MM-DDTHH:mm:ss'),
  };
}

async function loadUsers(page = filters.page) {
  filters.page = page;
  loading.value = true;
  try {
    const { created_from, created_to } = resolveCreatedAtFilters();
    pageData.value = await listAdminUsersApi({
      created_from,
      created_to,
      is_active: filters.is_active === '' ? undefined : filters.is_active,
      is_verified: filters.is_verified === '' ? undefined : filters.is_verified,
      keyword: filters.keyword.trim() || undefined,
      page: filters.page,
      page_size: filters.page_size,
    });
  } finally {
    loading.value = false;
  }
}

async function toggleUserStatus(row: AdminUserItem) {
  const nextStatus = !row.is_active;
  const actionText = nextStatus ? '启用' : '禁用';
  try {
    await ElMessageBox.confirm(
      `确认${actionText}用户 ${row.nickname || row.user_id} 吗？`,
      '更新用户状态',
      {
        type: 'warning',
      },
    );
    actionLoadingId.value = row.id;
    await updateAdminUserStatusApi(row.id, nextStatus);
    ElMessage.success(`用户已${actionText}`);
    await loadUsers(filters.page);
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      throw error;
    }
  } finally {
    actionLoadingId.value = null;
  }
}

onMounted(() => {
  void loadUsers();
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">用户管理</h1>
      <p class="text-sm text-slate-500">
        统一管理用户状态、认证标记和账号基础信息。
      </p>
    </div>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElForm inline class="flex flex-wrap gap-x-4">
        <ElFormItem label="关键词">
          <ElInput
            v-model="filters.keyword"
            clearable
            placeholder="搜索用户ID / 昵称 / 手机 / 城市 / 行业 / 公司"
            style="width: 360px"
            @keyup.enter="loadUsers(1)"
          />
        </ElFormItem>
        <ElFormItem label="状态">
          <ElSelect v-model="filters.is_active" clearable style="width: 160px">
            <ElOption label="全部" value="" />
            <ElOption :value="true" label="正常" />
            <ElOption :value="false" label="禁用" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="认证">
          <ElSelect v-model="filters.is_verified" clearable style="width: 160px">
            <ElOption label="全部" value="" />
            <ElOption :value="true" label="已认证" />
            <ElOption :value="false" label="未认证" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="注册时间">
          <ElDatePicker
            v-model="filters.registered_at_range"
            clearable
            end-placeholder="结束日期"
            range-separator="至"
            start-placeholder="开始日期"
            style="width: 280px"
            type="daterange"
            value-format="YYYY-MM-DD"
          />
        </ElFormItem>
        <ElFormItem>
          <ElButton type="primary" @click="loadUsers(1)">查询</ElButton>
        </ElFormItem>
      </ElForm>
    </ElCard>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElTable
        v-loading="loading"
        :data="pageData.items"
        empty-text="暂无用户数据"
        row-key="id"
        stripe
      >
        <ElTableColumn label="用户ID" min-width="160" prop="user_id" />
        <ElTableColumn label="昵称" min-width="140" prop="nickname" />
        <ElTableColumn label="手机" min-width="140" prop="phone" />
        <ElTableColumn label="城市 / 行业" min-width="200">
          <template #default="{ row }">
            {{ row.city_name || '--' }} / {{ row.industry_label || '--' }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="公司" min-width="180">
          <template #default="{ row }">
            {{ row.company_name || '--' }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="认证" width="100">
          <template #default="{ row }">
            <ElTag :type="row.is_verified ? 'success' : 'info'">
              {{ row.is_verified ? '已认证' : '未认证' }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="状态" width="100">
          <template #default="{ row }">
            <ElTag :type="row.is_active ? 'success' : 'danger'">
              {{ row.is_active ? '正常' : '禁用' }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="圈子 / 人脉" min-width="110">
          <template #default="{ row }">
            {{ row.circle_count }} / {{ row.network_count }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="注册时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </ElTableColumn>
        <ElTableColumn fixed="right" label="操作" width="110">
          <template #default="{ row }">
            <ElButton
              :loading="actionLoadingId === row.id"
              link
              type="primary"
              @click="toggleUserStatus(row)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </ElButton>
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
          @current-change="loadUsers"
        />
      </div>
    </ElCard>
  </div>
</template>
