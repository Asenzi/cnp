<script setup lang="ts">
import type { AdminCircleItem, PageResult } from '#/api/admin';

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

import {
  listAdminCirclesApi,
  updateAdminCircleStatusApi,
} from '#/api/admin';
import { formatDateTime, resolveStatusTagType } from '#/utils/admin';

defineOptions({ name: 'AdminCirclesPage' });

const loading = ref(false);
const actionLoadingCode = ref<string | null>(null);
const filters = reactive({
  keyword: '',
  page: 1,
  page_size: 12,
  registered_at_range: [] as string[],
  status: '',
});
const pageData = ref<PageResult<AdminCircleItem>>({
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

async function loadCircles(page = filters.page) {
  filters.page = page;
  loading.value = true;
  try {
    const { created_from, created_to } = resolveCreatedAtFilters();
    pageData.value = await listAdminCirclesApi({
      created_from,
      created_to,
      keyword: filters.keyword.trim() || undefined,
      page: filters.page,
      page_size: filters.page_size,
      status: filters.status || undefined,
    });
  } finally {
    loading.value = false;
  }
}

async function toggleCircleStatus(row: AdminCircleItem) {
  const nextStatus = row.status === 'active' ? 'inactive' : 'active';
  const actionText = nextStatus === 'active' ? '上线' : '下线';
  try {
    await ElMessageBox.confirm(
      `确认${actionText}圈子 ${row.name || row.circle_code} 吗？`,
      '更新圈子状态',
      {
        type: 'warning',
      },
    );
    actionLoadingCode.value = row.circle_code;
    await updateAdminCircleStatusApi(row.circle_code, nextStatus);
    ElMessage.success(`圈子已${actionText}`);
    await loadCircles(filters.page);
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      throw error;
    }
  } finally {
    actionLoadingCode.value = null;
  }
}

onMounted(() => {
  void loadCircles();
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">圈子管理</h1>
      <p class="text-sm text-slate-500">
        审核圈子在线状态，快速定位异常圈子和注册时间分布。
      </p>
    </div>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElForm inline class="flex flex-wrap gap-x-4">
        <ElFormItem label="关键词">
          <ElInput
            v-model="filters.keyword"
            clearable
            placeholder="搜索圈子编号 / 名称 / 行业 / 圈主"
            style="width: 320px"
            @keyup.enter="loadCircles(1)"
          />
        </ElFormItem>
        <ElFormItem label="状态">
          <ElSelect v-model="filters.status" clearable style="width: 160px">
            <ElOption label="全部" value="" />
            <ElOption label="active" value="active" />
            <ElOption label="inactive" value="inactive" />
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
          <ElButton type="primary" @click="loadCircles(1)">查询</ElButton>
        </ElFormItem>
      </ElForm>
    </ElCard>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElTable
        v-loading="loading"
        :data="pageData.items"
        empty-text="暂无圈子数据"
        row-key="circle_code"
        stripe
      >
        <ElTableColumn label="圈子编号" min-width="170" prop="circle_code" />
        <ElTableColumn label="圈子名称" min-width="200" prop="name" />
        <ElTableColumn label="圈主" min-width="180">
          <template #default="{ row }">
            {{ row.owner_nickname || '--' }} ({{ row.owner_user_id || '--' }})
          </template>
        </ElTableColumn>
        <ElTableColumn label="行业" min-width="120" prop="industry_label" />
        <ElTableColumn label="成员 / 动态" min-width="110">
          <template #default="{ row }">
            {{ row.member_count }} / {{ row.post_count }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="状态" width="100">
          <template #default="{ row }">
            <ElTag :type="resolveStatusTagType(row.status)">
              {{ row.status }}
            </ElTag>
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
              :loading="actionLoadingCode === row.circle_code"
              link
              type="primary"
              @click="toggleCircleStatus(row)"
            >
              {{ row.status === 'active' ? '下线' : '上线' }}
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
          @current-change="loadCircles"
        />
      </div>
    </ElCard>
  </div>
</template>
