<script setup lang="ts">
import type { AdminConfigItem } from '#/api/admin';

import { onMounted, reactive, ref } from 'vue';

import {
  ElButton,
  ElCard,
  ElForm,
  ElFormItem,
  ElMessage,
  ElSwitch,
} from 'element-plus';

import { listAdminConfigsApi, saveAdminConfigApi } from '#/api/admin';

defineOptions({ name: 'FeedVisibilityConfigCard' });

const loading = ref(false);
const saving = ref(false);
const formState = reactive({
  showSelfCircle: false,
  showSelfNetwork: false,
  showSelfResource: false,
});

const configMeta = {
  showSelfCircle: {
    description: '圈子推荐流是否允许当前用户看到自己创建的圈子，1=显示，0=隐藏',
    key: 'feed.visibility.show_self_circle',
    label: '圈子页显示自己的圈子',
  },
  showSelfNetwork: {
    description: '人脉推荐流是否允许当前用户看到自己的人脉卡片，1=显示，0=隐藏',
    key: 'feed.visibility.show_self_network',
    label: '人脉页显示自己',
  },
  showSelfResource: {
    description: '资源推荐流是否允许当前用户看到自己发布的资源，1=显示，0=隐藏',
    key: 'feed.visibility.show_self_resource',
    label: '资源页显示自己的资源',
  },
} as const;

function toEnabled(value: unknown) {
  return ['1', 'true', 'yes', 'on', 'enabled', 'show', 'visible'].includes(
    String(value ?? '0').trim().toLowerCase(),
  );
}

function applyConfig(items: AdminConfigItem[]) {
  const values = new Map(items.map((item) => [item.config_key, item.config_value]));
  formState.showSelfNetwork = toEnabled(values.get(configMeta.showSelfNetwork.key));
  formState.showSelfResource = toEnabled(values.get(configMeta.showSelfResource.key));
  formState.showSelfCircle = toEnabled(values.get(configMeta.showSelfCircle.key));
}

async function loadConfig() {
  loading.value = true;
  try {
    const result = await listAdminConfigsApi({
      keyword: 'feed.visibility.',
      page: 1,
      page_size: 20,
    });
    applyConfig(result.items);
  } finally {
    loading.value = false;
  }
}

async function saveConfig() {
  saving.value = true;
  try {
    const rows = [
      [configMeta.showSelfNetwork, formState.showSelfNetwork ? '1' : '0'],
      [configMeta.showSelfResource, formState.showSelfResource ? '1' : '0'],
      [configMeta.showSelfCircle, formState.showSelfCircle ? '1' : '0'],
    ] as const;
    await Promise.all(
      rows.map(([meta, configValue]) =>
        saveAdminConfigApi(meta.key, {
          config_group: 'feed_visibility',
          config_value: configValue,
          description: meta.description,
        }),
      ),
    );
    ElMessage.success('推荐流自我展示配置已保存');
    await loadConfig();
  } finally {
    saving.value = false;
  }
}

onMounted(() => {
  void loadConfig();
});
</script>

<template>
  <ElCard shadow="never" class="rounded-2xl border-0">
    <template #header>
      <div class="flex items-center justify-between gap-4">
        <div>
          <div class="text-base font-semibold text-slate-900">
            推荐流自我展示
          </div>
          <div class="mt-1 text-sm text-slate-500">
            控制小程序人脉、资源、圈子三个首页推荐流是否允许用户刷到自己的内容。默认隐藏自己。
          </div>
        </div>
        <ElButton :loading="saving" type="primary" @click="saveConfig">
          保存展示配置
        </ElButton>
      </div>
    </template>

    <ElForm v-loading="loading" label-position="top">
      <div class="grid gap-4 md:grid-cols-3">
        <ElFormItem :label="configMeta.showSelfNetwork.label">
          <div class="flex items-center gap-3">
            <ElSwitch v-model="formState.showSelfNetwork" />
            <span class="text-sm text-slate-500">
              {{ formState.showSelfNetwork ? '允许显示' : '隐藏自己' }}
            </span>
          </div>
        </ElFormItem>
        <ElFormItem :label="configMeta.showSelfResource.label">
          <div class="flex items-center gap-3">
            <ElSwitch v-model="formState.showSelfResource" />
            <span class="text-sm text-slate-500">
              {{ formState.showSelfResource ? '允许显示' : '隐藏自己' }}
            </span>
          </div>
        </ElFormItem>
        <ElFormItem :label="configMeta.showSelfCircle.label">
          <div class="flex items-center gap-3">
            <ElSwitch v-model="formState.showSelfCircle" />
            <span class="text-sm text-slate-500">
              {{ formState.showSelfCircle ? '允许显示' : '隐藏自己' }}
            </span>
          </div>
        </ElFormItem>
      </div>
    </ElForm>
  </ElCard>
</template>
