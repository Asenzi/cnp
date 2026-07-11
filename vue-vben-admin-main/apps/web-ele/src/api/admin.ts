import type { UserInfo } from '@vben/types';

import { requestClient } from '#/api/request';

const ADMIN_HOME_PATH = '/dashboard/overview';

export interface AdminProfile {
  id: number;
  username: string;
  display_name: string;
  role: string;
  is_active: boolean;
  last_login_at: null | string;
}

export interface AdminLoginResponse {
  access_token: string;
  admin: AdminProfile;
  expires_in: number;
  token_type: string;
}

export interface PageResult<T> {
  items: T[];
  page: number;
  page_size: number;
  total: number;
}

export interface DashboardSummary {
  active_circle_total: number;
  active_resource_total: number;
  active_user_total: number;
  circle_total: number;
  notice_total: number;
  pending_verification_total: number;
  resource_total: number;
  user_total: number;
  verified_user_total: number;
}

export interface DashboardUserItem {
  city_name: string;
  created_at: null | string;
  id: number;
  industry_label: string;
  is_active: boolean;
  is_verified: boolean;
  nickname: string;
  phone: string;
  user_id: string;
}

export interface DashboardCircleItem {
  circle_code: string;
  created_at: null | string;
  industry_label: string;
  member_count: number;
  name: string;
  owner_nickname: string;
  owner_user_id: string;
  post_count: number;
  status: string;
}

export interface DashboardPostItem {
  author_nickname: string;
  author_user_id: string;
  created_at: null | string;
  industry_label: string;
  like_count: number;
  mode: string;
  post_code: string;
  status: string;
  title: string;
  view_count: number;
}

export interface DashboardRechargeItem {
  amount: number;
  created_at: null | string;
  nickname: string;
  order_no: string;
  paid_at: null | string;
  pay_channel: string;
  status: string;
  user_id: string;
}

export interface DashboardOverview {
  recent_circles: DashboardCircleItem[];
  recent_posts: DashboardPostItem[];
  recent_recharges?: DashboardRechargeItem[];
  recent_users: DashboardUserItem[];
  summary: DashboardSummary;
}

export interface ProductSafetyOverview {
  alerts: {
    review_failure_spike: boolean;
    review_rejection_spike: boolean;
  };
  new_users: number;
  punishments: number;
  reports: number;
  retry_pending: number;
  review_failed: number;
  review_rejected: number;
  risk_levels: Record<string, number>;
  window_hours: number;
}

export interface AdminUserItem {
  circle_count: number;
  city_name: string;
  company_name: string;
  created_at: null | string;
  id: number;
  industry_label: string;
  is_active: boolean;
  is_verified: boolean;
  network_count: number;
  nickname: string;
  phone: string;
  user_id: string;
}

export interface AdminCircleItem {
  circle_code: string;
  created_at: null | string;
  description: string;
  industry_label: string;
  last_active_at: null | string;
  member_count: number;
  name: string;
  owner_nickname: string;
  owner_user_id: string;
  post_count: number;
  status: string;
}

export interface AdminPostItem {
  author_nickname: string;
  author_user_id: string;
  comment_count: number;
  created_at: null | string;
  industry_label: string;
  is_pinned: boolean;
  like_count: number;
  mode: string;
  post_code: string;
  status: string;
  title: string;
  view_count: number;
}

export interface AdminVerificationItem {
  id: number;
  nickname: string;
  phone: string;
  real_name_profile: null | {
    id_back_url: null | string;
    id_front_url: null | string;
    id_number_masked: null | string;
    real_name: null | string;
    reject_reason: null | string;
    reviewed_at: null | string;
    status: string;
    submitted_at: null | string;
    verified_at: null | string;
  };
  reject_reason: null | string;
  reviewed_at: null | string;
  status: string;
  submitted_at: null | string;
  submit_payload: null | Record<string, unknown>;
  type: string;
  user_id: string;
}

export interface AdminCircleOwnerApplicationItem {
  experience: string;
  id: number;
  is_circle_owner: boolean;
  nickname: string;
  reason: string;
  reject_reason: string;
  reviewed_at: null | string;
  status: string;
  submitted_at: null | string;
  user_id: string;
  user_pk: number;
}

export interface AdminContentReviewItem {
  action_type: string;
  created_at: null | string;
  current_payload: null | Record<string, unknown>;
  fee_paid: boolean;
  id: number;
  reject_reason: null | string;
  review_fee_amount: number;
  review_type: string;
  reviewed_at: null | string;
  risk_tags: string[];
  status: string;
  submit_payload: null | Record<string, unknown>;
  submitter_nickname: string;
  submitter_user_id: string;
  target_circle_code: null | string;
  target_label: null | string;
  target_post_code: null | string;
  target_user_pk: null | number;
  trigger_reason: null | string;
}

export interface AdminRechargeItem {
  amount: number;
  created_at: null | string;
  id: number;
  nickname: string;
  order_no: string;
  paid_at: null | string;
  pay_channel: string;
  pay_order_no: string;
  status: string;
  user_id: string;
}

export interface AdminConfigItem {
  config_group: string;
  config_key: string;
  config_value: string;
  description: string;
  id: number;
  updated_at: null | string;
}

export interface AdminContactPackagePlanItem {
  enabled: boolean;
  id?: string;
  name: string;
  price: number;
  view_count: number;
}

export interface AdminContactPackageConfig {
  display_enabled: boolean;
  plans: AdminContactPackagePlanItem[];
}

export interface AdminSplitConfig {
  auto_settle_enabled: boolean;
  biz_type: string;
  receiver_rate: number;
  service_fee_rate: number;
  updated_at: null | string;
  wechat_profit_sharing_enabled: boolean;
}

export interface AdminSplitTransactionItem {
  biz_type: string;
  circle_code: string;
  circle_name: string;
  created_at: null | string;
  executed_at: null | string;
  external_error: string;
  external_order_no: string;
  external_status: string;
  external_transaction_id: string;
  id: number;
  order_no: string;
  payer_nickname: string;
  payer_user_id: string;
  platform_fee: number;
  receiver_nickname: string;
  receiver_user_id: string;
  remark: string;
  split_amount: number;
  split_status: string;
  total_amount: number;
}

export interface AdminSettlementAccountItem {
  available_balance: number;
  frozen_balance: number;
  id: number;
  nickname: string;
  phone: string;
  total_income: number;
  total_withdrawn: number;
  updated_at: null | string;
  user_id: string;
  user_pk: number;
}

export interface AdminWithdrawalItem {
  actual_amount: number;
  amount: number;
  created_at: null | string;
  fee: number;
  id: number;
  nickname: string;
  order_no: string;
  phone: string;
  processed_at: null | string;
  remark: string;
  status: string;
  transaction_id: string;
  updated_at: null | string;
  user_id: string;
  user_pk: number;
  withdraw_account: string;
  withdraw_type: string;
}

export interface AdminUserInfo extends UserInfo {
  displayName: string;
  isActive: boolean;
  lastLoginAt: null | string;
  role: string;
}

export function formatRoleLabel(role: string) {
  if (role === 'super_admin') {
    return '超级管理员';
  }
  if (role === 'admin') {
    return '管理员';
  }
  return role || '管理员';
}

export function mapAdminProfileToUserInfo(
  profile: AdminProfile,
  token: null | string = null,
): AdminUserInfo {
  const username = String(profile.username || '');
  const displayName = String(profile.display_name || username || '管理员');
  const role = String(profile.role || 'super_admin');
  return {
    avatar: '',
    desc: formatRoleLabel(role),
    displayName,
    homePath: ADMIN_HOME_PATH,
    isActive: Boolean(profile.is_active),
    lastLoginAt: profile.last_login_at,
    realName: displayName,
    role,
    roles: [role],
    token: token || '',
    userId: String(profile.id),
    username,
  };
}

export async function loginAdminApi(payload: {
  password: string;
  username: string;
}) {
  return requestClient.post<AdminLoginResponse>('/auth/login', payload);
}

export async function getAdminProfileApi() {
  return requestClient.get<AdminProfile>('/auth/profile');
}

export async function getAdminDashboardOverviewApi() {
  return requestClient.get<DashboardOverview>('/dashboard/overview');
}

export async function getAdminProductSafetyOverviewApi() {
  return requestClient.get<ProductSafetyOverview>('/product-safety/overview');
}

export async function listAdminUsersApi(params: {
  created_from?: string;
  created_to?: string;
  is_active?: boolean | '';
  is_verified?: boolean | '';
  keyword?: string;
  page: number;
  page_size: number;
}) {
  return requestClient.get<PageResult<AdminUserItem>>('/users', { params });
}

export async function updateAdminUserStatusApi(
  userPk: number,
  isActive: boolean,
) {
  return requestClient.post(`/users/${userPk}/status`, {
    is_active: isActive,
  });
}

export async function listAdminCirclesApi(params: {
  created_from?: string;
  created_to?: string;
  keyword?: string;
  page: number;
  page_size: number;
  status?: string;
}) {
  return requestClient.get<PageResult<AdminCircleItem>>('/circles', { params });
}

export async function updateAdminCircleStatusApi(
  circleCode: string,
  status: 'active' | 'inactive',
) {
  return requestClient.post(`/circles/${encodeURIComponent(circleCode)}/status`, {
    status,
  });
}

export async function listAdminPostsApi(params: {
  keyword?: string;
  mode?: string;
  page: number;
  page_size: number;
  status?: string;
}) {
  return requestClient.get<PageResult<AdminPostItem>>('/posts', { params });
}

export async function updateAdminPostStatusApi(
  postCode: string,
  status: 'active' | 'offline',
) {
  return requestClient.post(`/posts/${encodeURIComponent(postCode)}/status`, {
    status,
  });
}

export async function updateAdminPostPinApi(postCode: string, pinned: boolean) {
  return requestClient.post(`/posts/${encodeURIComponent(postCode)}/pin`, {
    pinned,
  });
}

export async function listAdminVerificationsApi(params: {
  page: number;
  page_size: number;
  status?: string;
  verify_type?: string;
}) {
  return requestClient.get<PageResult<AdminVerificationItem>>('/verifications', {
    params,
  });
}

export async function reviewAdminVerificationApi(
  verificationId: number,
  payload: {
    action: 'approve' | 'reject';
    reject_reason?: string;
  },
) {
  return requestClient.post(`/verifications/${verificationId}/review`, payload);
}

export async function listAdminCircleOwnerApplicationsApi(params: {
  page: number;
  page_size: number;
  status?: string;
}) {
  return requestClient.get<PageResult<AdminCircleOwnerApplicationItem>>(
    '/circle-owner-applications',
    { params },
  );
}

export async function reviewAdminCircleOwnerApplicationApi(
  applicationId: number,
  payload: {
    action: 'approve' | 'reject';
    reject_reason?: string;
  },
) {
  return requestClient.post(
    `/circle-owner-applications/${applicationId}/review`,
    payload,
  );
}

export async function listAdminContentReviewsApi(params: {
  page: number;
  page_size: number;
  review_type?: string;
  status?: string;
}) {
  return requestClient.get<PageResult<AdminContentReviewItem>>('/content-reviews', {
    params,
  });
}

export async function reviewAdminContentReviewApi(
  reviewId: number,
  payload: {
    action: 'approve' | 'reject';
    reject_reason?: string;
  },
) {
  return requestClient.post(`/content-reviews/${reviewId}/review`, payload);
}

export async function listAdminRechargesApi(params: {
  keyword?: string;
  page: number;
  page_size: number;
  status?: string;
}) {
  return requestClient.get<PageResult<AdminRechargeItem>>('/recharges', {
    params,
  });
}

export async function listAdminConfigsApi(params: {
  config_group?: string;
  keyword?: string;
  page: number;
  page_size: number;
}) {
  return requestClient.get<PageResult<AdminConfigItem>>('/configs', { params });
}

export async function saveAdminConfigApi(
  configKey: string,
  payload: {
    config_group?: string;
    config_value: string;
    description?: string;
  },
) {
  return requestClient.put(`/configs/${encodeURIComponent(configKey)}`, payload);
}

export async function getAdminContactPackageConfigApi() {
  return requestClient.get<AdminContactPackageConfig>('/contact-package-config');
}

export async function saveAdminContactPackageConfigApi(
  payload: AdminContactPackageConfig,
) {
  return requestClient.put<AdminContactPackageConfig>(
    '/contact-package-config',
    payload,
  );
}

export async function getAdminSplitConfigApi() {
  return requestClient.get<AdminSplitConfig>('/split/config');
}

export async function saveAdminSplitConfigApi(payload: {
  auto_settle_enabled: boolean;
  service_fee_rate: number;
  wechat_profit_sharing_enabled: boolean;
}) {
  return requestClient.put<AdminSplitConfig>('/split/config', payload);
}

export async function listAdminSplitTransactionsApi(params: {
  keyword?: string;
  page: number;
  page_size: number;
  status?: string;
}) {
  return requestClient.get<PageResult<AdminSplitTransactionItem>>(
    '/split/transactions',
    { params },
  );
}

export async function retryAdminSplitTransactionApi(splitId: number) {
  return requestClient.post(`/split/transactions/${splitId}/retry`);
}

export async function listAdminSettlementAccountsApi(params: {
  keyword?: string;
  page: number;
  page_size: number;
}) {
  return requestClient.get<PageResult<AdminSettlementAccountItem>>(
    '/split/settlements',
    { params },
  );
}

export async function listAdminWithdrawalsApi(params: {
  keyword?: string;
  page: number;
  page_size: number;
  status?: string;
}) {
  return requestClient.get<PageResult<AdminWithdrawalItem>>(
    '/split/withdrawals',
    { params },
  );
}

export async function reviewAdminWithdrawalApi(
  withdrawalId: number,
  payload: {
    action: 'approve' | 'reject';
    remark?: string;
    transaction_id?: string;
  },
) {
  return requestClient.post(
    `/split/withdrawals/${withdrawalId}/review`,
    payload,
  );
}
