import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    name: 'Profile',
    path: '/profile',
    component: () => import('#/views/admin/profile/index.vue'),
    meta: {
      icon: 'lucide:user',
      hideInMenu: true,
      title: '管理员资料',
    },
  },
];

export default routes;
