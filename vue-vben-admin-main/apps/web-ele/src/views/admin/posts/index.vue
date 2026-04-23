<script setup lang="ts">
import type { AdminPostItem, PageResult } from '#/api/admin';

import { onMounted, reactive, ref } from 'vue';

import {
  ElButton,
  ElCard,
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
  listAdminPostsApi,
  updateAdminPostPinApi,
  updateAdminPostStatusApi,
} from '#/api/admin';
import {
  formatDateTime,
  formatPostMode,
  resolveStatusTagType,
} from '#/utils/admin';

defineOptions({ name: 'AdminPostsPage' });

const loading = ref(false);
const actionLoadingCode = ref<string | null>(null);
const filters = reactive({
  keyword: '',
  mode: '',
  page: 1,
  page_size: 12,
  status: '',
});
const pageData = ref<PageResult<AdminPostItem>>({
  items: [],
  page: 1,
  page_size: 12,
  total: 0,
});

async function loadPosts(page = filters.page) {
  filters.page = page;
  loading.value = true;
  try {
    pageData.value = await listAdminPostsApi({
      keyword: filters.keyword.trim() || undefined,
      mode: filters.mode || undefined,
      page: filters.page,
      page_size: filters.page_size,
      status: filters.status || undefined,
    });
  } finally {
    loading.value = false;
  }
}

async function togglePostStatus(row: AdminPostItem) {
  const nextStatus = row.status === 'active' ? 'offline' : 'active';
  const actionText = nextStatus === 'active' ? '上线' : '下线';
  try {
    await ElMessageBox.confirm(
      `确认${actionText}资源 ${row.title || row.post_code} 吗？`,
      '更新资源状态',
      {
        type: 'warning',
      },
    );
    actionLoadingCode.value = row.post_code;
    await updateAdminPostStatusApi(row.post_code, nextStatus);
    ElMessage.success(`资源已${actionText}`);
    await loadPosts(filters.page);
  } catch (error) {
    if (error !== 'cancel' && error !== 'close') {
      throw error;
    }
  } finally {
    actionLoadingCode.value = null;
  }
}

async function togglePostPin(row: AdminPostItem) {
  actionLoadingCode.value = row.post_code;
  try {
    await updateAdminPostPinApi(row.post_code, !row.is_pinned);
    ElMessage.success(row.is_pinned ? '已取消置顶' : '已置顶资源');
    await loadPosts(filters.page);
  } finally {
    actionLoadingCode.value = null;
  }
}

onMounted(() => {
  void loadPosts();
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">资源管理</h1>
      <p class="text-sm text-slate-500">
        管理资源发布、上下线状态和置顶优先级。
      </p>
    </div>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElForm inline class="flex flex-wrap gap-x-4">
        <ElFormItem label="关键词">
          <ElInput
            v-model="filters.keyword"
            clearable
            placeholder="搜索资源编号 / 标题 / 作者 / 行业"
            style="width: 320px"
            @keyup.enter="loadPosts(1)"
          />
        </ElFormItem>
        <ElFormItem label="状态">
          <ElSelect v-model="filters.status" clearable style="width: 150px">
            <ElOption label="全部" value="" />
            <ElOption label="active" value="active" />
            <ElOption label="offline" value="offline" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem label="类型">
          <ElSelect v-model="filters.mode" clearable style="width: 150px">
            <ElOption label="全部" value="" />
            <ElOption label="找合作" value="cooperate" />
            <ElOption label="找资源" value="resource" />
          </ElSelect>
        </ElFormItem>
        <ElFormItem>
          <ElButton type="primary" @click="loadPosts(1)">查询</ElButton>
        </ElFormItem>
      </ElForm>
    </ElCard>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElTable
        v-loading="loading"
        :data="pageData.items"
        empty-text="暂无资源数据"
        row-key="post_code"
        stripe
      >
        <ElTableColumn label="资源编号" min-width="170" prop="post_code" />
        <ElTableColumn label="标题" min-width="240" prop="title" />
        <ElTableColumn label="类型" width="90">
          <template #default="{ row }">
            {{ formatPostMode(row.mode) }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="作者" min-width="180">
          <template #default="{ row }">
            {{ row.author_nickname || '--' }} ({{ row.author_user_id || '--' }})
          </template>
        </ElTableColumn>
        <ElTableColumn label="互动" min-width="120">
          <template #default="{ row }">
            {{ row.view_count }} / {{ row.like_count }} / {{ row.comment_count }}
          </template>
        </ElTableColumn>
        <ElTableColumn label="状态" width="100">
          <template #default="{ row }">
            <ElTag :type="resolveStatusTagType(row.status)">
              {{ row.status }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="置顶" width="90">
          <template #default="{ row }">
            <ElTag :type="row.is_pinned ? 'warning' : 'info'">
              {{ row.is_pinned ? '是' : '否' }}
            </ElTag>
          </template>
        </ElTableColumn>
        <ElTableColumn label="发布时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.created_at) }}
          </template>
        </ElTableColumn>
        <ElTableColumn fixed="right" label="操作" width="150">
          <template #default="{ row }">
            <div class="flex items-center gap-3">
              <ElButton
                :loading="actionLoadingCode === row.post_code"
                link
                type="primary"
                @click="togglePostStatus(row)"
              >
                {{ row.status === 'active' ? '下线' : '上线' }}
              </ElButton>
              <ElButton
                :loading="actionLoadingCode === row.post_code"
                link
                type="warning"
                @click="togglePostPin(row)"
              >
                {{ row.is_pinned ? '取消置顶' : '置顶' }}
              </ElButton>
            </div>
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
          @current-change="loadPosts"
        />
      </div>
    </ElCard>
  </div>
</template>
