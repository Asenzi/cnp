import type { UserInfo } from '@vben/types';

import { getAdminProfileApi, mapAdminProfileToUserInfo } from '#/api/admin';

export async function getUserInfoApi() {
  const profile = await getAdminProfileApi();
  return mapAdminProfileToUserInfo(profile) as UserInfo;
}
