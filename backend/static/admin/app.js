const { createApp } = Vue;

createApp({
  data() {
    return {
      storageKey: 'friends_admin_access_token',
      token: '',
      profile: null,
      activeView: 'dashboard',
      loginLoading: false,
      pageLoading: false,
      loginForm: {
        username: 'admin',
        password: ''
      },
      toast: {
        show: false,
        message: '',
        type: 'success'
      },
      dashboard: {
        summary: {},
        recent_users: [],
        recent_circles: [],
        recent_posts: [],
        recent_recharges: []
      },
      users: {
        items: [],
        total: 0,
        page: 1,
        page_size: 12,
        keyword: '',
        is_active: ''
      },
      circles: {
        items: [],
        total: 0,
        page: 1,
        page_size: 12,
        keyword: '',
        status: ''
      },
      posts: {
        items: [],
        total: 0,
        page: 1,
        page_size: 12,
        keyword: '',
        status: '',
        mode: ''
      },
      verifications: {
        items: [],
        total: 0,
        page: 1,
        page_size: 12,
        status: 'pending',
        verify_type: ''
      },
      recharges: {
        items: [],
        total: 0,
        page: 1,
        page_size: 12,
        keyword: '',
        status: ''
      },
      configs: {
        items: [],
        total: 0,
        page: 1,
        page_size: 12,
        keyword: '',
        config_group: ''
      },
      configDraft: {
        config_key: '',
        config_group: '',
        config_value: '',
        description: ''
      },
      reviewModal: {
        visible: false,
        item: null,
        action: 'approve',
        reject_reason: ''
      },
      pageTitleMap: {
        dashboard: '仪表盘',
        users: '用户管理',
        circles: '圈子管理',
        posts: '资源管理',
        verifications: '认证审核',
        recharges: '充值订单',
        configs: '系统配置'
      },
      pageDescMap: {
        dashboard: '快速查看平台规模、待处理事项和最新业务动态。',
        users: '统一管理用户状态、认证标记和增长情况。',
        circles: '审核圈子上线状态，定位异常圈子和运营表现。',
        posts: '管理资源发布、上下架和置顶优先级。',
        verifications: '集中处理实名认证、企业认证与名片认证。',
        recharges: '查看钱包充值订单、支付状态和金额流水。',
        configs: '维护系统配置项，支持在线编辑与新增。'
      }
    };
  },
  computed: {
    menuItems() {
      return [
        { key: 'dashboard', label: '仪表盘', icon: '◧' },
        { key: 'users', label: '用户管理', icon: '◎' },
        { key: 'circles', label: '圈子管理', icon: '◌' },
        { key: 'posts', label: '资源管理', icon: '▤' },
        { key: 'verifications', label: '认证审核', icon: '✓' },
        { key: 'recharges', label: '充值订单', icon: '¥' },
        { key: 'configs', label: '系统配置', icon: '⚙' }
      ];
    },
    adminInitial() {
      const name = this.profile && this.profile.display_name ? String(this.profile.display_name) : 'A';
      return name.slice(0, 1).toUpperCase();
    },
    statCards() {
      const summary = this.dashboard.summary || {};
      return [
        {
          key: 'users',
          label: '总用户',
          value: this.formatNumber(summary.user_total),
          desc: `活跃 ${this.formatNumber(summary.active_user_total)} / 已认证 ${this.formatNumber(summary.verified_user_total)}`,
          icon: 'U'
        },
        {
          key: 'circles',
          label: '总圈子',
          value: this.formatNumber(summary.circle_total),
          desc: `活跃圈子 ${this.formatNumber(summary.active_circle_total)}`,
          icon: 'C'
        },
        {
          key: 'posts',
          label: '资源总量',
          value: this.formatNumber(summary.resource_total),
          desc: `在线资源 ${this.formatNumber(summary.active_resource_total)}`,
          icon: 'R'
        },
        {
          key: 'verify',
          label: '待审认证',
          value: this.formatNumber(summary.pending_verification_total),
          desc: `系统通知 ${this.formatNumber(summary.notice_total)}`,
          icon: 'V'
        },
        {
          key: 'recharge',
          label: '已支付充值单',
          value: this.formatNumber(summary.paid_recharge_total),
          desc: `待支付 ${this.formatNumber(summary.pending_recharge_total)}`,
          icon: 'P'
        },
        {
          key: 'money',
          label: '充值金额',
          value: this.formatAmount(summary.recharge_amount_total),
          desc: '累计已支付充值金额',
          icon: '$'
        }
      ];
    }
  },
  methods: {
    showToast(message, type = 'success') {
      this.toast.message = message;
      this.toast.type = type;
      this.toast.show = true;
      clearTimeout(this.toastTimer);
      this.toastTimer = setTimeout(() => {
        this.toast.show = false;
      }, 2400);
    },
    async request(path, options = {}) {
      const method = options.method || 'GET';
      const headers = Object.assign({}, options.headers || {});
      if (this.token && options.auth !== false) {
        headers.Authorization = `Bearer ${this.token}`;
      }
      if (options.body && !headers['Content-Type']) {
        headers['Content-Type'] = 'application/json';
      }

      const response = await fetch(path, {
        method,
        headers,
        body: options.body ? JSON.stringify(options.body) : undefined
      });

      let payload = null;
      try {
        payload = await response.json();
      } catch (error) {
        payload = null;
      }

      if (!response.ok || !payload || payload.code !== 0) {
        const message = payload && payload.message ? payload.message : `请求失败 (${response.status})`;
        if (response.status === 401 || response.status === 403) {
          this.logout(false);
        }
        throw new Error(message);
      }
      return payload.data;
    },
    buildQuery(params) {
      const query = new URLSearchParams();
      Object.keys(params).forEach((key) => {
        const value = params[key];
        if (value === '' || value === null || value === undefined) {
          return;
        }
        query.set(key, String(value));
      });
      return query.toString();
    },
    totalPages(section) {
      const total = Number(section.total || 0);
      const pageSize = Math.max(Number(section.page_size || 12), 1);
      return Math.max(Math.ceil(total / pageSize), 1);
    },
    formatDate(value) {
      if (!value) {
        return '--';
      }
      const date = new Date(value);
      if (Number.isNaN(date.getTime())) {
        return '--';
      }
      const year = date.getFullYear();
      const month = `${date.getMonth() + 1}`.padStart(2, '0');
      const day = `${date.getDate()}`.padStart(2, '0');
      const hour = `${date.getHours()}`.padStart(2, '0');
      const minute = `${date.getMinutes()}`.padStart(2, '0');
      return `${year}-${month}-${day} ${hour}:${minute}`;
    },
    formatAmount(value) {
      const number = Number(value || 0);
      if (!Number.isFinite(number)) {
        return '0.00';
      }
      return number.toFixed(2);
    },
    formatNumber(value) {
      const number = Number(value || 0);
      if (!Number.isFinite(number)) {
        return '0';
      }
      if (number >= 10000) {
        return `${(number / 10000).toFixed(1)}w`;
      }
      return `${Math.round(number)}`;
    },
    formatJson(value) {
      try {
        return JSON.stringify(value || {}, null, 2);
      } catch (error) {
        return '{}';
      }
    },
    verificationStatusClass(status) {
      if (status === 'approved' || status === 'paid' || status === 'active') {
        return 'status-success';
      }
      if (status === 'pending') {
        return 'status-warning';
      }
      if (status === 'rejected' || status === 'failed' || status === 'inactive' || status === 'offline') {
        return 'status-danger';
      }
      return 'status-muted';
    },
    async bootstrap() {
      const storedToken = localStorage.getItem(this.storageKey);
      if (!storedToken) {
        return;
      }
      this.token = storedToken;
      try {
        await this.loadProfile();
        await this.changeView('dashboard');
      } catch (error) {
        this.logout(false);
      }
    },
    async handleLogin() {
      if (!this.loginForm.username.trim() || !this.loginForm.password) {
        this.showToast('请输入管理员账号和密码', 'error');
        return;
      }
      this.loginLoading = true;
      try {
        const data = await this.request('/api/v1/admin/auth/login', {
          method: 'POST',
          auth: false,
          body: {
            username: this.loginForm.username.trim(),
            password: this.loginForm.password
          }
        });
        this.token = data.access_token || '';
        localStorage.setItem(this.storageKey, this.token);
        this.profile = data.admin || null;
        this.loginForm.password = '';
        await this.changeView('dashboard');
        this.showToast('登录成功');
      } catch (error) {
        this.showToast(error.message || '登录失败', 'error');
      } finally {
        this.loginLoading = false;
      }
    },
    async loadProfile() {
      this.profile = await this.request('/api/v1/admin/auth/profile');
    },
    logout(showMessage = true) {
      this.token = '';
      this.profile = null;
      localStorage.removeItem(this.storageKey);
      this.activeView = 'dashboard';
      if (showMessage) {
        this.showToast('已退出登录');
      }
    },
    async changeView(view) {
      this.activeView = view;
      this.pageLoading = true;
      try {
        if (!this.profile && this.token) {
          await this.loadProfile();
        }
        if (view === 'dashboard') {
          await this.loadDashboard();
        } else if (view === 'users') {
          await this.loadUsers(1);
        } else if (view === 'circles') {
          await this.loadCircles(1);
        } else if (view === 'posts') {
          await this.loadPosts(1);
        } else if (view === 'verifications') {
          await this.loadVerifications(1);
        } else if (view === 'recharges') {
          await this.loadRecharges(1);
        } else if (view === 'configs') {
          await this.loadConfigs(1);
        }
      } catch (error) {
        this.showToast(error.message || '页面加载失败', 'error');
      } finally {
        this.pageLoading = false;
      }
    },
    async loadDashboard() {
      this.dashboard = await this.request('/api/v1/admin/dashboard/overview');
    },
    async loadUsers(page = this.users.page) {
      this.users.page = Math.max(page, 1);
      const query = this.buildQuery({
        keyword: this.users.keyword,
        is_active: this.users.is_active,
        page: this.users.page,
        page_size: this.users.page_size
      });
      const data = await this.request(`/api/v1/admin/users?${query}`);
      this.users.items = data.items || [];
      this.users.total = data.total || 0;
      this.users.page = data.page || 1;
    },
    async toggleUserStatus(item) {
      const actionText = item.is_active ? '禁用' : '启用';
      if (!window.confirm(`确认${actionText}用户 ${item.nickname || item.user_id} 吗？`)) {
        return;
      }
      try {
        await this.request(`/api/v1/admin/users/${item.id}/status`, {
          method: 'POST',
          body: { is_active: !item.is_active }
        });
        this.showToast(`用户已${actionText}`);
        await this.loadUsers(this.users.page);
      } catch (error) {
        this.showToast(error.message || '用户状态更新失败', 'error');
      }
    },
    async loadCircles(page = this.circles.page) {
      this.circles.page = Math.max(page, 1);
      const query = this.buildQuery({
        keyword: this.circles.keyword,
        status: this.circles.status,
        page: this.circles.page,
        page_size: this.circles.page_size
      });
      const data = await this.request(`/api/v1/admin/circles?${query}`);
      this.circles.items = data.items || [];
      this.circles.total = data.total || 0;
      this.circles.page = data.page || 1;
    },
    async toggleCircleStatus(item) {
      const nextStatus = item.status === 'active' ? 'inactive' : 'active';
      const actionText = nextStatus === 'active' ? '上线' : '下线';
      if (!window.confirm(`确认${actionText}圈子 ${item.name || item.circle_code} 吗？`)) {
        return;
      }
      try {
        await this.request(`/api/v1/admin/circles/${encodeURIComponent(item.circle_code)}/status`, {
          method: 'POST',
          body: { status: nextStatus }
        });
        this.showToast(`圈子已${actionText}`);
        await this.loadCircles(this.circles.page);
      } catch (error) {
        this.showToast(error.message || '圈子状态更新失败', 'error');
      }
    },
    async loadPosts(page = this.posts.page) {
      this.posts.page = Math.max(page, 1);
      const query = this.buildQuery({
        keyword: this.posts.keyword,
        status: this.posts.status,
        mode: this.posts.mode,
        page: this.posts.page,
        page_size: this.posts.page_size
      });
      const data = await this.request(`/api/v1/admin/posts?${query}`);
      this.posts.items = data.items || [];
      this.posts.total = data.total || 0;
      this.posts.page = data.page || 1;
    },
    async togglePostStatus(item) {
      const nextStatus = item.status === 'active' ? 'offline' : 'active';
      const actionText = nextStatus === 'active' ? '上线' : '下线';
      if (!window.confirm(`确认${actionText}资源 ${item.title || item.post_code} 吗？`)) {
        return;
      }
      try {
        await this.request(`/api/v1/admin/posts/${encodeURIComponent(item.post_code)}/status`, {
          method: 'POST',
          body: { status: nextStatus }
        });
        this.showToast(`资源已${actionText}`);
        await this.loadPosts(this.posts.page);
      } catch (error) {
        this.showToast(error.message || '资源状态更新失败', 'error');
      }
    },
    async togglePostPin(item) {
      const nextPinned = !item.is_pinned;
      const actionText = nextPinned ? '置顶' : '取消置顶';
      try {
        await this.request(`/api/v1/admin/posts/${encodeURIComponent(item.post_code)}/pin`, {
          method: 'POST',
          body: { pinned: nextPinned }
        });
        this.showToast(`资源已${actionText}`);
        await this.loadPosts(this.posts.page);
      } catch (error) {
        this.showToast(error.message || '资源置顶更新失败', 'error');
      }
    },
    async loadVerifications(page = this.verifications.page) {
      this.verifications.page = Math.max(page, 1);
      const query = this.buildQuery({
        status: this.verifications.status,
        verify_type: this.verifications.verify_type,
        page: this.verifications.page,
        page_size: this.verifications.page_size
      });
      const data = await this.request(`/api/v1/admin/verifications?${query}`);
      this.verifications.items = data.items || [];
      this.verifications.total = data.total || 0;
      this.verifications.page = data.page || 1;
    },
    openVerificationModal(item, action) {
      this.reviewModal.visible = true;
      this.reviewModal.item = item;
      this.reviewModal.action = action;
      this.reviewModal.reject_reason = '';
    },
    closeReviewModal() {
      this.reviewModal.visible = false;
      this.reviewModal.item = null;
      this.reviewModal.action = 'approve';
      this.reviewModal.reject_reason = '';
    },
    async submitVerificationReview() {
      const item = this.reviewModal.item;
      if (!item) {
        return;
      }
      if (this.reviewModal.action === 'reject' && !this.reviewModal.reject_reason.trim()) {
        this.showToast('请输入驳回原因', 'error');
        return;
      }
      try {
        await this.request(`/api/v1/admin/verifications/${item.id}/review`, {
          method: 'POST',
          body: {
            action: this.reviewModal.action,
            reject_reason: this.reviewModal.action === 'reject' ? this.reviewModal.reject_reason.trim() : ''
          }
        });
        this.showToast(this.reviewModal.action === 'approve' ? '认证已通过' : '认证已驳回');
        this.closeReviewModal();
        await this.loadVerifications(this.verifications.page);
      } catch (error) {
        this.showToast(error.message || '审核处理失败', 'error');
      }
    },
    async loadRecharges(page = this.recharges.page) {
      this.recharges.page = Math.max(page, 1);
      const query = this.buildQuery({
        keyword: this.recharges.keyword,
        status: this.recharges.status,
        page: this.recharges.page,
        page_size: this.recharges.page_size
      });
      const data = await this.request(`/api/v1/admin/recharges?${query}`);
      this.recharges.items = data.items || [];
      this.recharges.total = data.total || 0;
      this.recharges.page = data.page || 1;
    },
    async loadConfigs(page = this.configs.page) {
      this.configs.page = Math.max(page, 1);
      const query = this.buildQuery({
        keyword: this.configs.keyword,
        config_group: this.configs.config_group,
        page: this.configs.page,
        page_size: this.configs.page_size
      });
      const data = await this.request(`/api/v1/admin/configs?${query}`);
      this.configs.items = (data.items || []).map((item) => Object.assign({}, item));
      this.configs.total = data.total || 0;
      this.configs.page = data.page || 1;
    },
    async saveConfig(item) {
      if (!item.config_key) {
        this.showToast('配置键不能为空', 'error');
        return;
      }
      try {
        await this.request(`/api/v1/admin/configs/${encodeURIComponent(item.config_key)}`, {
          method: 'PUT',
          body: {
            config_value: item.config_value || '',
            config_group: item.config_group || '',
            description: item.description || ''
          }
        });
        this.showToast('配置已保存');
        await this.loadConfigs(this.configs.page);
      } catch (error) {
        this.showToast(error.message || '配置保存失败', 'error');
      }
    },
    async saveDraftConfig() {
      if (!this.configDraft.config_key.trim()) {
        this.showToast('请输入配置键', 'error');
        return;
      }
      try {
        await this.request(`/api/v1/admin/configs/${encodeURIComponent(this.configDraft.config_key.trim())}`, {
          method: 'PUT',
          body: {
            config_value: this.configDraft.config_value || '',
            config_group: this.configDraft.config_group || '',
            description: this.configDraft.description || ''
          }
        });
        this.showToast('配置已保存');
        this.configDraft = {
          config_key: '',
          config_group: '',
          config_value: '',
          description: ''
        };
        await this.loadConfigs(1);
      } catch (error) {
        this.showToast(error.message || '配置保存失败', 'error');
      }
    }
  },
  mounted() {
    this.bootstrap();
  }
}).mount('#app');
