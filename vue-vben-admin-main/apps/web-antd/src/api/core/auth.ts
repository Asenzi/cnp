import { baseRequestClient, requestClient } from '#/api/request';

export namespace AuthApi {
  /** 登录接口参数 */
  export interface LoginParams {
    password?: string;
    username?: string;
  }

  /** 登录接口返回值 */
export interface LoginResult {
  accessToken: string;
}

  export interface RefreshTokenResult {
    data: string;
    status: number;
  }
}

/**
 * 登录
 */
export async function loginApi(data: AuthApi.LoginParams) {
  const result = await requestClient.post<{
    access_token?: string;
    accessToken?: string;
  }>('/v1/admin/auth/login', data);

  return {
    accessToken: result.accessToken || result.access_token || '',
  };
}

/**
 * 刷新accessToken
 */
export async function refreshTokenApi() {
  return baseRequestClient.post<AuthApi.RefreshTokenResult>('/v1/admin/auth/refresh', {
    withCredentials: true,
  });
}

/**
 * 退出登录
 */
export async function logoutApi() {
  return Promise.resolve();
}

/**
 * 获取用户权限码
 */
export async function getAccessCodesApi() {
  return Promise.resolve(['AC_100100', 'AC_100110', 'AC_100120', 'AC_100010']);
}
