# 风险识别规则参考

## 风险类型分类

### 1. 危险接口

接口路径或方法名包含以下关键词时标记为危险接口：

| 分类 | 关键词 |
|---|---|
| 删除类 | delete、remove、drop、clear、purge、reset |
| 财务类 | pay、refund、transfer、withdraw、recharge |
| 审批类 | approve、reject、submit、confirm |
| 通知类 | sendSms、sendEmail、notify、push |
| 库存类 | stock、deduct、freeze、lock |
| 终止类 | cancel、close、terminate、abort |

处理规则：
- `riskLevel: high`
- 默认不加入性能压测
- 生成确认测试用例（caseType: 危险接口确认测试）
- 在 risk_report.md 中单独列出

### 2. 跨模块依赖

| 场景 | 识别规则 | 处理方式 |
|---|---|---|
| 引用其他模块 DTO | DTO 类位于其他业务模块包下 | 标记跨模块依赖，提示人工确认 |
| 调用其他模块 Service | Service 类位于其他业务模块包下 | 生成外部依赖提示 |
| 依赖其他模块数据状态 | 接口参数需要其他模块的数据 ID | 标记数据依赖 |
| 接口路径冲突 | 不同模块有相同路径前缀 | 标记路径冲突风险 |

### 3. 无法静态推断

| 场景 | 标记原因 | 建议 |
|---|---|---|
| `Map<String,Object>` 请求体 | 无法确定字段结构 | 补充接口文档或前端 payload |
| `JSONObject` 请求体 | 同上 | 同上 |
| 泛型无法解析 | 泛型参数在运行时确定 | 标记 `needManualConfirm` |
| Token 获取方式未知 | 无法确定认证流程 | 配置登录接口或手动填写 |
| 签名/加密规则未知 | 涉及自定义签名算法 | 手动配置签名策略 |
| 验证码 | 无法自动获取验证码 | 配置验证码绕过策略 |
| 真实数据库 ID | 需要已存在的数据 | 提供测试数据或前置创建接口 |
| 文件上传 | 需要实际文件 | 配置测试文件路径 |
| 外部系统依赖 | 调用第三方 API | 配置 mock 或沙箱环境 |

### 4. 鉴权风险

| 场景 | 识别规则 |
|---|---|
| 无鉴权注解但其他接口有 | 对比同 Controller 内其他方法 |
| 自定义鉴权注解 | 无法确定 token 传递方式 |
| 多角色权限 | 有角色注解但无法确定测试账号 |

## 风险报告格式

### risk_report.md

```markdown
# 风险报告

## 1. 危险接口
| 接口 | 风险类型 | 原因 | 默认处理 |
|---|---|---|---|
| DELETE /api/user/delete/{id} | 删除接口 | 可能删除真实数据 | 默认不加入性能压测 |

## 2. 跨模块依赖
| 接口 | 依赖模块 | 依赖类型 | 建议 |
|---|---|---|---|
| POST /api/user/bindOrder | order | DTO + Service | 仅生成入参校验用例 |

## 3. 无法静态推断
| 接口 | 原因 | 建议 |
|---|---|---|
| POST /api/user/query | Map<String,Object> 请求体 | 补充接口文档 |

## 4. 鉴权风险
| 接口 | 问题 | 建议 |
|---|---|---|
| /api/user/create | token 获取方式未知 | 配置登录接口 |
```

### manual_confirm_items.md

```markdown
# 需人工确认项
| 编号 | 类型 | 位置 | 问题 | 建议 |
|---|---|---|---|---|
| M001 | DTO 字段 | UserCreateDTO | 未找到源码 | 上传 DTO 或手动补充 |
| M002 | 鉴权 | 全局 | token 获取方式未知 | 配置登录接口 |
```

### dangerous_api_list.md

```markdown
# 危险接口清单
| 接口 | 方法 | 路径 | 危险关键词 | 风险等级 | 压测排除 |
|---|---|---|---|---|---|
| 删除用户 | DELETE | /api/user/delete/{id} | delete | high | 是 |
```
