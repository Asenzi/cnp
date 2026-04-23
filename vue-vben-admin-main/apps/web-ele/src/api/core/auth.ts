import {
  getAdminProfileApi,
  loginAdminApi,
  mapAdminProfileToUserInfo,
} from '#/api/admin';

export namespace AuthApi {
  export interface LoginParams {
    password?: string;
    username?: string;
  }

  export interface LoginResult {
    accessToken: string;
    userInfo: ReturnType<typeof mapAdminProfileToUserInfo>;
  }

  export interface RefreshTokenResult {
    data: string;
    status: number;
  }
}

export async function loginApi(data: AuthApi.LoginParams) {
  const result = await loginAdminApi({
    password: String(data.password || ''),
    username: String(data.username || ''),
  });
  return {
    accessToken: result.access_token,
    userInfo: mapAdminProfileToUserInfo(result.admin, result.access_token),
  };
}

export async function refreshTokenApi() {
  return {
    data: '',
    status: 200,
  };
}

export async function logoutApi() {
  return true;
}

export async function getAccessCodesApi() {
  const profile = await getAdminProfileApi();
  return [String(profile.role || 'super_admin')];
}
