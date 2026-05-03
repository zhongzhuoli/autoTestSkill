# 测试用例类型参考

## 生成强度模式

控制用例数量，防止"用例爆炸"。通过 `test_model.json` 的 `generationMode` 字段指定。

| 模式 | generationMode | 每接口用例数 | 说明 |
|---|---|---|---|
| 冒烟模式 | `smoke` | 1–3 条 | 仅正常值 + 核心必填缺失，用于快速冒烟验证 |
| 标准模式 | `standard` | 5–15 条 | 每个字段生成核心异常（必填缺失、null、类型错误），不展开全部边界 |
| 严格模式 | `strict` | 15–50 条 | 全边界值、全异常类型、全字段覆盖 |
| 安全模式 | `security` | 5–10 条 | 只生成 SQL 注入、XSS、超长输入、特殊字符等安全类用例 |
| 性能模式 | `performance` | 1–3 条 | 只保留正常链路用例和安全接口，用于压测基线 |

**默认值：** 用户未指定时使用 `standard`。

### 各模式包含的 caseType

| caseType | smoke | standard | strict | security | performance |
|---|:---:|:---:|:---:|:---:|:---:|
| 正常值测试 | ✓ | ✓ | ✓ | | ✓ |
| 必填字段缺失 | ✓（仅首个必填字段） | ✓ | ✓ | | |
| Null 值测试 | | ✓ | ✓ | | |
| 空字符串测试 | | ✓ | ✓ | | |
| 空白字符串测试 | | | ✓ | | |
| 类型错误测试 | | ✓ | ✓ | | |
| 边界值测试 | | | ✓ | | |
| 极限值测试 | | | ✓ | ✓（超长输入） | |
| 格式错误测试 | | ✓ | ✓ | | |
| 枚举非法值测试 | | ✓ | ✓ | | |
| 特殊字符测试 | | | ✓ | ✓ | |
| SQL 注入测试 | | | ✓ | ✓ | |
| XSS 测试 | | | ✓ | ✓ | |
| 数组集合异常测试 | | | ✓ | | |
| 嵌套对象异常测试 | | | ✓ | | |
| 鉴权缺失测试 | ✓ | ✓ | ✓ | | |
| 权限不足测试 | | | ✓ | | |
| 接口方法错误测试 | | | ✓ | | |
| Content-Type 错误测试 | | | ✓ | | |
| 业务规则测试 | | ✓ | ✓ | | |
| 接口链路测试 | ✓ | ✓ | ✓ | | ✓ |
| 危险接口确认测试 | | ✓ | ✓ | | |

### 各模式的 priority / enabled / riskLevel 默认值

| priority | 含义 | 默认 enabled | 说明 |
|---|---|---|---|
| P0 | 阻断性 | true | 正常值、鉴权缺失，必须通过 |
| P1 | 核心功能 | true | 必填缺失、null、类型错误、格式错误等 |
| P2 | 补充验证 | false | 边界值、极限值、特殊字符等，人工按需启用 |

| riskLevel | 含义 | 说明 |
|---|---|---|
| low | 常规用例 | 无特殊风险 |
| medium | 需关注 | 涉及跨模块依赖、动态参数等 |
| high | 高风险 | 危险接口（delete/pay/refund 等） |

**执行策略：** 默认只执行 P0 + P1（enabled=true），P2 标记为 enabled=false 供人工选择启用。

| 序号 | caseType | 说明 | 生成规则 |
|---:|---|---|---|
| 1 | 正常值测试 | 合法参数正常请求 | 每个接口至少1条 |
| 2 | 必填字段缺失 | 删除 @NotNull/@NotBlank 字段 | 每个必填字段1条 |
| 3 | Null 值测试 | 字段设为 null | 每个必填字段1条 |
| 4 | 空字符串测试 | String 字段设为 "" | 每个 String 字段1条 |
| 5 | 空白字符串测试 | String 字段设为 "   " | 每个 String 字段1条 |
| 6 | 类型错误测试 | 字段类型不匹配（如 age="abc"） | Number/Boolean 字段各1条 |
| 7 | 边界值测试 | @Min/@Max/@Size 边界 | 有约束字段各1-3条 |
| 8 | 极限值测试 | 超大值、超长字符串、最大整数值 | 关键字段各1条 |
| 9 | 格式错误测试 | @Pattern/@Email/@Phone 格式不匹配 | 有格式约束字段各1条 |
| 10 | 枚举非法值测试 | 枚举字段传入不存在的值 | 每个枚举字段1条 |
| 11 | 特殊字符测试 | 包含 `'\"<>&\|` 等字符 | String 字段1条 |
| 12 | SQL 注入测试 | 包含 `' OR 1=1--` 等 | String 字段1条 |
| 13 | XSS 测试 | 包含 `<script>` 标签 | String 字段1条 |
| 14 | 数组集合异常测试 | 空数组、超长数组、null 数组 | List/Set/Array 字段 |
| 15 | 嵌套对象异常测试 | 嵌套对象字段缺失/null | 嵌套 DTO 字段 |
| 16 | 鉴权缺失测试 | 不带 token 请求 | 需鉴权接口1条 |
| 17 | 权限不足测试 | 用低权限 token 请求 | 有权限注解的接口1条 |
| 18 | 接口方法错误测试 | 用 GET 请求 POST 接口 | 每个接口1条 |
| 19 | Content-Type 错误测试 | JSON 接口用 form-data | JSON 接口1条 |
| 20 | 业务规则测试 | 根据业务逻辑推断异常场景 | 视 Service 代码而定 |
| 21 | 接口链路测试 | 模块内 create→detail→update→list→delete | 可识别链路时生成 |
| 22 | 危险接口确认测试 | 对危险接口的确认/二次确认 | 危险接口各1条 |

## 用例生成优先级（向后兼容）

优先级与 generationMode 联动：
- **P0（阻断）**：正常值、鉴权缺失 → 始终 enabled=true
- **P1（核心）**：必填缺失、Null、空字符串、类型错误 → standard 模式下 enabled=true
- **P2（补充）**：边界值、极限值、特殊字符、SQL 注入、XSS → strict 模式下 enabled=true，其余模式 enabled=false
- **P3（按需）**：接口方法错误、Content-Type 错误、业务规则 → 仅 strict 模式生成，默认 enabled=false

## 用例编号规则

格式：`TC_{MODULE}_{API_ACTION}_{SEQ}`

示例：
- `TC_USER_CREATE_001` — 用户模块创建接口第1条用例
- `TC_USER_DETAIL_001` — 用户模块详情接口第1条用例
- `TC_ORDER_PAY_001` — 订单模块支付接口第1条用例

模块级扫描时也可用：`TC_MODULE_{MODULE}_{ACTION}_{SEQ}`

## 预期结果规则

### 正常值测试
- HTTP 状态码：200
- 业务 code：项目成功码（200/SUCCESS/0）
- message：包含 "success"/"成功"

### 参数校验失败类（必填缺失、null、空串、类型错误、边界非法、格式错误）
- HTTP 状态码：400（部分项目可能返回 200）
- 业务 code：参数错误码（40001/PARAM_ERROR）
- message：包含 "参数"/"不能为空"/"格式错误"等

### 鉴权失败类
- HTTP 状态码：401 或 403
- 业务 code：未登录/无权限
- message：包含 "未授权"/"token"/"权限"

### 安全类（SQL 注入、XSS）
- 不应返回 500 或执行注入语句
- 预期返回参数错误或被过滤后正常处理

## 异常用例判定原则

异常用例返回 400/401/403 **不代表失败**。只有当实际结果不符合该用例的 `expectedHttpStatus`、`expectedBizCode`、`expectedMessageContains` 时，才判定为失败。

## 危险接口识别

以下关键词的接口默认标记为危险接口：
- delete、remove、drop、clear、purge、reset
- pay、refund、transfer、withdraw
- approve、reject、submit、confirm
- sendSms、sendEmail、notify
- stock、deduct、freeze、lock
- cancel、close、terminate

危险接口：
- 默认 `riskLevel: high`
- 默认不加入性能压测
- 生成确认测试用例
