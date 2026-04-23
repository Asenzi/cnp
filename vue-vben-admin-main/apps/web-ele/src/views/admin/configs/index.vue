<script setup lang="ts">
import type { AdminConfigItem, PageResult } from '#/api/admin';

import { onMounted, reactive, ref } from 'vue';

import {
  ElButton,
  ElCard,
  ElForm,
  ElFormItem,
  ElInput,
  ElMessage,
  ElPagination,
  ElTable,
  ElTableColumn,
} from 'element-plus';

import { listAdminConfigsApi, saveAdminConfigApi } from '#/api/admin';
import { formatDateTime } from '#/utils/admin';

import ContactPackageConfigCard from './components/ContactPackageConfigCard.vue';

defineOptions({ name: 'AdminConfigsPage' });

const loading = ref(false);
const savingKey = ref<null | string>(null);
const filters = reactive({
  config_group: '',
  keyword: '',
  page: 1,
  page_size: 12,
});
const draft = reactive({
  config_group: '',
  config_key: '',
  config_value: '',
  description: '',
});
const pageData = ref<PageResult<AdminConfigItem>>({
  items: [],
  page: 1,
  page_size: 12,
  total: 0,
});

async function loadConfigs(page = filters.page) {
  filters.page = page;
  loading.value = true;
  try {
    const result = await listAdminConfigsApi({
      config_group: filters.config_group.trim() || undefined,
      keyword: filters.keyword.trim() || undefined,
      page: filters.page,
      page_size: filters.page_size,
    });
    pageData.value = {
      ...result,
      items: result.items.map((item) => ({ ...item })),
    };
  } finally {
    loading.value = false;
  }
}

async function saveConfig(item: AdminConfigItem) {
  if (!item.config_key) {
    ElMessage.error('配置键不能为空');
    return;
  }
  savingKey.value = item.config_key;
  try {
    await saveAdminConfigApi(item.config_key, {
      config_group: item.config_group || '',
      config_value: item.config_value || '',
      description: item.description || '',
    });
    ElMessage.success('配置已保存');
    await loadConfigs(filters.page);
  } finally {
    savingKey.value = null;
  }
}

async function saveDraft() {
  if (!draft.config_key.trim()) {
    ElMessage.error('请输入配置键');
    return;
  }
  savingKey.value = draft.config_key.trim();
  try {
    await saveAdminConfigApi(draft.config_key.trim(), {
      config_group: draft.config_group.trim(),
      config_value: draft.config_value,
      description: draft.description,
    });
    ElMessage.success('配置已保存');
    draft.config_group = '';
    draft.config_key = '';
    draft.config_value = '';
    draft.description = '';
    await loadConfigs(1);
  } finally {
    savingKey.value = null;
  }
}

onMounted(() => {
  void loadConfigs();
});
</script>

<template>
  <div class="space-y-4 p-5">
    <div class="space-y-1">
      <h1 class="text-2xl font-semibold text-slate-900">系统配置</h1>
      <p class="text-sm text-slate-500">
        上方维护专用业务配置，下方继续保留通用系统配置项的在线编辑能力。
      </p>
    </div>

    <ContactPackageConfigCard />

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElForm inline class="flex flex-wrap gap-x-4">
        <ElFormItem label="关键词">
          <ElInput
            v-model="filters.keyword"
            clearable
            placeholder="搜索配置键 / 值 / 描述"
            style="width: 300px"
            @keyup.enter="loadConfigs(1)"
          />
        </ElFormItem>
        <ElFormItem label="分组">
          <ElInput
            v-model="filters.config_group"
            clearable
            placeholder="按分组筛选"
            style="width: 180px"
            @keyup.enter="loadConfigs(1)"
          />
        </ElFormItem>
        <ElFormItem>
          <ElButton type="primary" @click="loadConfigs(1)">查询</ElButton>
        </ElFormItem>
      </ElForm>
    </ElCard>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <template #header>
        <div class="font-semibold text-slate-900">新增 / 更新通用配置</div>
      </template>
      <ElForm label-position="top">
        <div class="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
          <ElFormItem label="配置键">
            <ElInput v-model="draft.config_key" placeholder="例如：site.title" />
          </ElFormItem>
          <ElFormItem label="配置分组">
            <ElInput v-model="draft.config_group" placeholder="例如：app" />
          </ElFormItem>
          <ElFormItem label="配置值">
            <ElInput v-model="draft.config_value" placeholder="请输入配置值" />
          </ElFormItem>
          <ElFormItem label="描述">
            <ElInput v-model="draft.description" placeholder="请输入描述" />
          </ElFormItem>
        </div>
        <ElButton
          :loading="savingKey === draft.config_key.trim()"
          type="primary"
          @click="saveDraft"
        >
          保存配置
        </ElButton>
      </ElForm>
    </ElCard>

    <ElCard shadow="never" class="rounded-2xl border-0">
      <ElTable
        v-loading="loading"
        :data="pageData.items"
        empty-text="暂无配置数据"
        row-key="id"
        stripe
      >
        <ElTableColumn label="配置键" min-width="220" prop="config_key" />
        <ElTableColumn label="分组" min-width="140">
          <template #default="{ row }">
            <ElInput v-model="row.config_group" placeholder="分组" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="配置值" min-width="180">
          <template #default="{ row }">
            <ElInput v-model="row.config_value" placeholder="配置值" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="描述" min-width="220">
          <template #default="{ row }">
            <ElInput v-model="row.description" placeholder="描述" />
          </template>
        </ElTableColumn>
        <ElTableColumn label="更新时间" min-width="160">
          <template #default="{ row }">
            {{ formatDateTime(row.updated_at) }}
          </template>
        </ElTableColumn>
        <ElTableColumn fixed="right" label="操作" width="100">
          <template #default="{ row }">
            <ElButton
              :loading="savingKey === row.config_key"
              link
              type="primary"
              @click="saveConfig(row)"
            >
              保存
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
          @current-change="loadConfigs"
        />
      </div>
    </ElCard>
  </div>
</template>
