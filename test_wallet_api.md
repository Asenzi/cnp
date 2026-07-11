# 钱包页面接口测试文档

## 测试环境
- 后端地址: http://localhost:8000
- 需要登录token

## 1. 钱包首页 (pages/me/wallet/index) 接口测试

### 1.1 获取钱包概览
```bash
GET /api/v1/payment/member/center
Headers: Authorization: Bearer {token}
```

**预期返回:**
```json
{
  "code": 0,
  "data": {
    "wallet": {
      "balance": 0.00
    },
    "member": {
      "is_active": false,
      "expire_at": null
    }
  }
}
```

### 1.2 获取会员订单列表
```bash
GET /api/v1/payment/member/orders?cursor=&limit=20
Headers: Authorization: Bearer {token}
```

**预期返回:**
```json
{
  "code": 0,
  "data": {
    "items": [],
    "next_cursor": "",
    "has_more": false
  }
}
```

### 1.3 获取充值订单列表
```bash
GET /api/v1/payment/wallet/recharge/orders?cursor=&limit=20
Headers: Authorization: Bearer {token}
```

**预期返回:**
```json
{
  "code": 0,
  "data": {
    "items": [],
    "next_cursor": "",
    "has_more": false
  }
}
```

## 2. 充值页面 (pages/me/wallet/recharge/index) 接口测试

### 2.1 创建充值订单
```bash
POST /api/v1/payment/wallet/recharge
Headers:
  Authorization: Bearer {token}
  Content-Type: application/json
Body:
{
  "amount": 50.00,
  "pay_channel": "wxpay"
}
```

**预期返回 (开发环境模拟支付):**
```json
{
  "code": 0,
  "data": {
    "action": "mock_paid",
    "order_no": "WR202605060001"
  },
  "message": "充值成功"
}
```

**预期返回 (生产环境微信支付):**
```json
{
  "code": 0,
  "data": {
    "action": "wxpay_required",
    "order_no": "WR202605060001",
    "wxpay": {
      "timeStamp": "1234567890",
      "nonceStr": "abc123",
      "package": "prepay_id=xxx",
      "signType": "RSA",
      "paySign": "xxx"
    }
  },
  "message": "请完成微信支付"
}
```

### 2.2 确认充值支付
```bash
POST /api/v1/payment/wallet/recharge/{order_no}/confirm
Headers:
  Authorization: Bearer {token}
  Content-Type: application/json
Body:
{
  "transaction_id": "4200001234567890",
  "ext": {}
}
```

**预期返回:**
```json
{
  "code": 0,
  "data": {
    "paid": true,
    "balance": 50.00
  },
  "message": "充值确认成功"
}
```

### 2.3 查询充值订单状态
```bash
GET /api/v1/payment/wallet/recharge/{order_no}
Headers: Authorization: Bearer {token}
```

**预期返回:**
```json
{
  "code": 0,
  "data": {
    "order_no": "WR202605060001",
    "amount": 50.00,
    "paid": true,
    "created_at": "2026-05-06T12:00:00Z"
  }
}
```

## 3. 前端页面测试要点

### 3.1 钱包首页测试
- [ ] 页面加载时正确显示余额
- [ ] 余额卡片显示银行卡样式
- [ ] 充值按钮可点击跳转
- [ ] 交易列表正确显示会员订单和充值订单
- [ ] 时间筛选功能正常
- [ ] 类型筛选功能正常
- [ ] 下拉加载更多功能正常
- [ ] 空状态显示正确

### 3.2 充值页面测试
- [ ] 预设金额选择功能正常
- [ ] 自定义金额输入功能正常
- [ ] 金额验证正确(0.01-200000)
- [ ] 支付方式显示正确
- [ ] 应付金额计算正确
- [ ] 提交按钮状态正确
- [ ] 支付流程完整
- [ ] 支付成功后返回钱包页面
- [ ] 支付失败提示正确

## 4. 错误处理测试

### 4.1 未登录
- 访问接口返回401
- 前端跳转到登录页

### 4.2 金额验证
- 小于0.01提示错误
- 大于200000提示错误
- 非数字输入自动过滤

### 4.3 网络错误
- 接口超时提示
- 网络断开提示
- 服务器错误提示

## 5. 数据一致性测试

### 5.1 充值后余额更新
1. 记录充值前余额
2. 完成充值
3. 验证余额 = 原余额 + 充值金额

### 5.2 订单列表更新
1. 完成充值
2. 返回钱包页面
3. 验证订单列表包含新订单

### 5.3 订单状态同步
1. 创建订单
2. 查询订单状态
3. 验证状态一致
