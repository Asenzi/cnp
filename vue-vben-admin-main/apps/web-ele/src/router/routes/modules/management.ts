import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    name: 'UserManagement',
    path: '/users',
    component: () => import('#/views/admin/users/index.vue'),
    meta: {
      icon: 'lucide:users',
      order: 1,
      title: '人员管理',
    },
  },
  {
    name: 'CircleManagement',
    path: '/circles',
    component: () => import('#/views/admin/circles/index.vue'),
    meta: {
      icon: 'lucide:circle-fading-plus',
      order: 2,
      title: '圈子管理',
    },
  },
  {
    name: 'PostManagement',
    path: '/posts',
    component: () => import('#/views/admin/posts/index.vue'),
    meta: {
      icon: 'lucide:briefcase-business',
      order: 3,
      title: '资源管理',
    },
  },
  {
    meta: {
      icon: 'lucide:shield-check',
      order: 4,
      title: '审核',
    },
    name: 'ReviewManagement',
    path: '/reviews',
    children: [
      {
        name: 'VerificationManagement',
        path: '/reviews/verifications',
        component: () => import('#/views/admin/verifications/index.vue'),
        meta: {
          icon: 'lucide:badge-check',
          title: '认证审核',
        },
      },
      {
        name: 'CircleOwnerApplicationManagement',
        path: '/reviews/circle-owners',
        component: () => import('#/views/admin/circle-owner-applications/index.vue'),
        meta: {
          icon: 'lucide:crown',
          title: '圈主申请',
        },
      },
      {
        name: 'ProfileReviewManagement',
        path: '/reviews/profiles',
        component: () => import('#/views/admin/content-reviews/index.vue'),
        meta: {
          icon: 'lucide:user-search',
          reviewType: 'profile',
          title: '个人信息审核',
        },
      },
      {
        name: 'CircleReviewManagement',
        path: '/reviews/circles',
        component: () => import('#/views/admin/content-reviews/index.vue'),
        meta: {
          icon: 'lucide:orbit',
          reviewType: 'circle',
          title: '圈子信息审核',
        },
      },
      {
        name: 'PostReviewManagement',
        path: '/reviews/posts',
        component: () => import('#/views/admin/content-reviews/index.vue'),
        meta: {
          icon: 'lucide:file-search',
          reviewType: 'post',
          title: '资源信息审核',
        },
      },
    ],
  },
  {
    name: 'ProductSafetyManagement',
    path: '/product-safety',
    component: () => import('#/views/admin/product-safety/index.vue'),
    meta: {
      icon: 'lucide:shield-alert',
      order: 5,
      title: '产品安全',
    },
  },
  {
    name: 'ConfigManagement',
    path: '/configs',
    component: () => import('#/views/admin/configs/index.vue'),
    meta: {
      icon: 'lucide:settings-2',
      order: 6,
      title: '系统配置',
    },
  },
  {
    meta: {
      icon: 'lucide:landmark',
      order: 7,
      title: '分账结算',
    },
    name: 'SettlementManagement',
    path: '/settlement',
    children: [
      {
        name: 'SplitConfigManagement',
        path: '/settlement/config',
        component: () => import('#/views/admin/settlement/config.vue'),
        meta: {
          icon: 'lucide:settings',
          title: '分账配置',
        },
      },
      {
        name: 'SplitTransactionManagement',
        path: '/settlement/transactions',
        component: () => import('#/views/admin/settlement/transactions.vue'),
        meta: {
          icon: 'lucide:receipt-text',
          title: '分账订单',
        },
      },
      {
        name: 'SettlementAccountManagement',
        path: '/settlement/accounts',
        component: () => import('#/views/admin/settlement/accounts.vue'),
        meta: {
          icon: 'lucide:wallet',
          title: '结算账户',
        },
      },
      {
        name: 'WithdrawalManagement',
        path: '/settlement/withdrawals',
        component: () => import('#/views/admin/settlement/withdrawals.vue'),
        meta: {
          icon: 'lucide:hand-coins',
          title: '提现审核',
        },
      },
    ],
  },
];

export default routes;
