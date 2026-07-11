# 支付系统配置检查清单

## ✅ 配置已完成

### 1. 微信支付配置
```env
WECHAT_PAY_ENABLED=true ✅
WECHAT_PAY_APP_ID=wxd801f2e147f4abb1 ✅
WECHAT_PAY_MCH_ID=1744441028 ✅
WECHAT_PAY_API_V2_KEY=fW8mX6OvRiqlrhlbkiOpljPnqQ6wYDvz ✅
WECHAT_PAY_NOTIFY_URL=https://cnptec.site/api/v1/payment/wechat/notify ✅ (已修正)
```

### 2. Redis 配置
```env
REDIS_ENABLED=true ✅ (已修正，队列需要)
```

---

## 📋 微信商户平台配置

### 需要在微信支付商户平台配置的内容

**登录地址：** https://pay.weixin.qq.com/

#### 1. 授权域名
**位置：** 产品中心 > 开发配置 > 支付授权目录

**需要添加：**
```
https://cnptec.site/
```

#### 2. 回调 IP 白名单（如果有限制）
**位置：** 账户中心 > API安全 > IP白名单

**需要添加：**
- 你的服务器公网 IP

#### 3. 验证 API 密钥
**位置：** 账户中心 > API安全 > API密钥

**确认：**
- API 密钥（V2）是否为：`fW8mX6OvRiqlrhlbkiOpljPnqQ6wYDvz`

---

## 🧪 测试步骤

### 第一步：测试 API 可访问性

```bash
# 1. 测试健康检查
curl https://cnptec.site/api/v1/payment/ping

# 应该返回
{
  "code": 0,
  "message": "payment module ready",
  "data": null
}

# 2. 测试回调接口（模拟微信回调）
curl -X POST https://cnptec.site/api/v1/payment/wechat/notify \
  -H "Content-Type: application/xml" \
  -d '<xml><return_code>SUCCESS</return_code></xml>'

# 应该返回 XML（不报错即可）
```

---

### 第二步：小程序端测试支付

#### 1. 会员订阅支付测试

**调用接口：**
```javascript
// 小程序端代码
const res = await uni.request({
  url: 'https://cnptec.site/api/v1/payment/member/subscribe',
  method: 'POST',
  header: {
    'Authorization': 'Bearer ' + token
  },
  data: {
    plan_id: 'monthly',        // 月度会员
    pay_channel: 'wxpay',      // 微信支付
    use_points_discount: false // 不使用积分
  }
});

console.log('订单创建结果：', res.data);

// 预期返回
{
  "code": 0,
  "message": "请完成微信支付",
  "data": {
    "action": "wxpay_required",
    "order_no": "M20260602XXXXXX",
    "amount": 29.9,
    "pay_params": {
      "prepay_id": "wx02xxxxx",
      "timeStamp": "1717315200",
      "nonceStr": "abc123",
      "package": "prepay_id=wx02xxxxx",
      "signType": "MD5",
      "paySign": "ABCD1234..."
    }
  }
}
```

#### 2. 调起微信支付

```javascript
// 拿到 pay_params 后调起支付
wx.requestPayment({
  timeStamp: res.data.data.pay_params.timeStamp,
  nonceStr: res.data.data.pay_params.nonceStr,
  package: res.data.data.pay_params.package,
  signType: res.data.data.pay_params.signType,
  paySign: res.data.data.pay_params.paySign,
  success: function(payRes) {
    console.log('支付成功', payRes);
    uni.showToast({ title: '支付成功' });

    // 查询订单状态
    checkOrderStatus(res.data.data.order_no);
  },
  fail: function(err) {
    console.error('支付失败', err);
    uni.showToast({
      title: '支付失败: ' + err.errMsg,
      icon: 'none'
    });
  }
});
```

#### 3. 查询订单状态

```javascript
async function checkOrderStatus(orderNo) {
  const res = await uni.request({
    url: `https://cnptec.site/api/v1/payment/member/orders/${orderNo}`,
    method: 'GET',
    header: {
      'Authorization': 'Bearer ' + token
    }
  });

  console.log('订单状态：', res.data);

  // 预期返回
  {
    "code": 0,
    "data": {
      "order_no": "M20260602XXXXXX",
      "status": "paid",          // 支付成功
      "amount": 29.9,
      "plan_id": "monthly",
      "member_status": "active", // 会员已激活
      "expires_at": "2026-07-02T12:00:00"
    }
  }
}
```

---

### 第三步：钱包充值测试

```javascript
// 1. 创建充值订单
const res = await uni.request({
  url: 'https://cnptec.site/api/v1/payment/wallet/recharge',
  method: 'POST',
  header: {
    'Authorization': 'Bearer ' + token
  },
  data: {
    amount: 100.00,           // 充值 100 元
    pay_channel: 'wxpay'
  }
});

// 2. 调起支付（同上）
wx.requestPayment({...});

// 3. 查询充值状态
const statusRes = await uni.request({
  url: `https://cnptec.site/api/v1/payment/wallet/recharge/${orderNo}`,
  method: 'GET',
  header: {
    'Authorization': 'Bearer ' + token
  }
});

// 预期返回
{
  "code": 0,
  "data": {
    "order_no": "R20260602XXXXXX",
    "status": "paid",
    "amount": 100.00,
    "balance": 100.00  // 当前钱包余额
  }
}
```

---

## 🐛 常见问题排查

### 问题 1：调用统一下单失败

**现象：**
```
订单创建返回错误：调用微信统一下单失败
```

**排查步骤：**
1. 检查 API 密钥是否正确（32位）
2. 检查商户号是否正确
3. 检查服务器时间是否准确
4. 查看后端日志中的详细错误信息

**解决方案：**
```bash
# 查看后端日志
tail -f logs/app.log
```

---

### 问题 2：支付成功但订单状态未更新

**现象：**
- 用户已支付
- 查询订单状态仍然是 `pending`

**排查步骤：**
1. 检查回调 URL 是否配置正确
2. 检查回调 URL 是否可以从外网访问
3. 查看微信支付商户平台的回调日志

**解决方案：**
```bash
# 1. 测试回调 URL 是否可访问
curl -X POST https://cnptec.site/api/v1/payment/wechat/notify

# 2. 查看后端是否收到回调
grep "wechat.*notify" logs/app.log

# 3. 如果没有收到回调，检查防火墙/Nginx配置
```

---

### 问题 3：签名验证失败

**现象：**
```
回调日志显示：签名验证失败
```

**原因：**
- API 密钥配置错误
- 签名算法不匹配

**解决方案：**
1. 确认 API 密钥（V2）是否正确
2. 确认使用的是 MD5 签名（不是 HMAC-SHA256）

---

### 问题 4：HTTPS 证书问题

**现象：**
```
小程序调用接口报错：request:fail ssl hand shake error
```

**解决方案：**
1. 确保域名已配置 HTTPS 证书
2. 确保证书有效且未过期
3. 在微信小程序后台配置服务器域名白名单

**微信小程序后台配置：**
- 登录 https://mp.weixin.qq.com/
- 开发 > 开发管理 > 开发设置 > 服务器域名
- 添加：`https://cnptec.site`

---

## 📊 监控建议

### 1. 订单监控

**关键指标：**
- 订单创建成功率
- 支付成功率
- 回调接收成功率
- 订单完成时长

**查询 SQL：**
```sql
-- 今日订单统计
SELECT
  COUNT(*) as total_orders,
  SUM(CASE WHEN status='paid' THEN 1 ELSE 0 END) as paid_orders,
  SUM(CASE WHEN status='pending' THEN 1 ELSE 0 END) as pending_orders,
  SUM(CASE WHEN status='failed' THEN 1 ELSE 0 END) as failed_orders,
  SUM(CASE WHEN status='paid' THEN amount ELSE 0 END) as total_amount
FROM member_orders
WHERE DATE(created_at) = CURDATE();

-- 待处理订单（超过30分钟仍未支付）
SELECT order_no, user_pk, amount, created_at
FROM member_orders
WHERE status = 'pending'
  AND created_at < NOW() - INTERVAL 30 MINUTE
ORDER BY created_at DESC;
```

---

### 2. 日志监控

**重要日志关键词：**
```bash
# 微信支付相关
grep "wechat.*pay" logs/app.log | tail -100

# 订单创建
grep "subscribe_member_plan\|create_wallet_recharge" logs/app.log

# 回调处理
grep "handle_wechat_pay_notify" logs/app.log

# 错误日志
grep "ERROR\|FAIL" logs/app.log | tail -50
```

---

## 🚀 上线检查清单

### 部署前

- [x] 微信支付参数已配置
- [x] Redis 已启用
- [x] 回调 URL 已更新为正式域名
- [ ] HTTPS 证书已配置
- [ ] 微信商户平台已配置授权域名
- [ ] 微信小程序后台已配置服务器域名

### 部署后

- [ ] 健康检查接口可访问
- [ ] 回调接口可从外网访问
- [ ] 小程序可以成功调起支付
- [ ] 支付成功后订单状态正确更新
- [ ] 会员权益正确发放
- [ ] 钱包余额正确到账

### 监控

- [ ] 订单监控脚本已部署
- [ ] 日志监控已配置
- [ ] 告警机制已设置
- [ ] 异常订单处理流程已明确

---

## 📞 应急联系

### 微信支付问题
- 商户平台：https://pay.weixin.qq.com/
- 技术支持：商户平台 > 服务支持 > 在线客服

### 域名/证书问题
- 检查 DNS 解析
- 检查证书有效期
- 检查 Nginx/服务器配置

---

## 📝 优化建议（上线后）

### 短期（1周内）
1. ✅ 添加支付成功通知
2. ✅ 前端订单状态轮询
3. ✅ 管理后台订单管理

### 中期（1个月内）
1. 订单数据统计
2. 异常订单告警
3. 退款流程优化

### 长期（3个月内）
1. 支付数据分析
2. 优惠券系统
3. 支付宝支付

---

**配置日期：** 2026-06-02
**域名：** cnptec.site
**环境：** 生产环境
