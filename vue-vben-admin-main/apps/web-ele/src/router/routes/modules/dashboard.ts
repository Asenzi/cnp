import type { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    meta: {
      icon: 'lucide:layout-dashboard',
      order: -1,
      title: '仪表盘',
    },
    name: 'Dashboard',
    path: '/dashboard',
    children: [
      {
        name: 'DashboardOverview',
        path: '/dashboard/overview',
        component: () => import('#/views/admin/dashboard/index.vue'),
        meta: {
          affixTab: true,
          icon: 'lucide:area-chart',
          title: '概览',
        },
      },
    ],
  },
];

export default routes;
