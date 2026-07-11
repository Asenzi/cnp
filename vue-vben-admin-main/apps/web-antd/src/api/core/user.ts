import type { UserInfo } from '@vben/types';

import { requestClient } from '#/api/request';

/**
 * 获取用户信息
 */
export async function getUserInfoApi() {
  const profile = await requestClient.get<{
    display_name?: string;
    id?: number | string;
    role?: string;
    username?: string;
  }>('/v1/admin/auth/profile');

  return {
    avatar: '',
    desc: profile.role || 'admin',
    homePath: '/analytics',
    realName: profile.display_name || profile.username || 'Admin',
    roles: [profile.role || 'super_admin'],
    userId: String(profile.id || ''),
    username: profile.username || '',
  } as UserInfo;
}
