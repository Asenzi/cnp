<script lang="ts" setup>
import type { VbenFormSchema } from '@vben/common-ui';

import { computed } from 'vue';

import { AuthenticationLogin, z } from '@vben/common-ui';

import { useAuthStore } from '#/store';

defineOptions({ name: 'Login' });

const authStore = useAuthStore();

const formSchema = computed((): VbenFormSchema[] => {
  return [
    {
      component: 'VbenInput',
      componentProps: {
        placeholder: '请输入管理员账号',
      },
      fieldName: 'username',
      label: '账号',
      rules: z.string().min(1, { message: '请输入管理员账号' }),
    },
    {
      component: 'VbenInputPassword',
      componentProps: {
        placeholder: '请输入管理员密码',
      },
      fieldName: 'password',
      label: '密码',
      rules: z.string().min(1, { message: '请输入管理员密码' }),
    },
  ];
});
</script>

<template>
  <AuthenticationLogin
    :form-schema="formSchema"
    :loading="authStore.loginLoading"
    :show-code-login="false"
    :show-forget-password="false"
    :show-qrcode-login="false"
    :show-register="false"
    :show-remember-me="false"
    :show-third-party-login="false"
    sub-title="使用后台管理员账号登录"
    submit-button-text="登录后台"
    title="欢迎进入 Friends Admin"
    @submit="authStore.authLogin"
  />
</template>
