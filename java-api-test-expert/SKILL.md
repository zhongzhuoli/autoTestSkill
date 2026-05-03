---
name: java-api-test-expert
description: >
  Java API 接口测试资产自动生成专家。扫描 Java 项目源码，自动生成测试用例、
  JMeter 脚本、CSV 参数化文件、Excel 工作簿和风险报告。支持三种模式：完整项目模式、
  模块级扫描模式、单 Controller 模式。
  触发场景：用户要求对 Java 项目/模块/Controller 生成接口测试、JMeter 脚本、
  测试用例、接口清单、风险报告；用户提到"生成测试用例""接口测试""JMeter 脚本"
  "测试资产""冒烟测试""回归测试""接口清单"等关键词时使用。
---

# Java API 测试专家

扫描 Java 项目源码，自动生成接口清单、测试用例矩阵、JMeter 脚本、CSV 参数化文件、Excel 工作簿和风险报告。

## 模式检测

| 用户输入 | 模式 |
|---|---|
| 单个 `.java` 文件 | 单 Controller 模式 |
| 目录路径、包名、Maven/Gradle 子模块名 | 模块级扫描模式 |
| 项目根目录、无明确目标 | 完整项目模式 |
| 输入模糊 | 列出候选，询问用户确认 |

## 执行流程

### 阶段一：模式检测与范围确定

1. 根据用户输入确定扫描模式
2. 定位目标路径，确定模块边界
3. 读取配置文件获取项目配置：
   - 查找 `application.yml`、`application.properties`、`application-*.yml`
   - 提取 `server.port`（默认 8080）、`server.servlet.context-path`
   - 提取 `server.address`（如果有）
   - 注意多 profile 时取默认值或激活的 profile
4. 如果匹配不明确，列出候选路径让用户选择

### 阶段二：源码扫描

扫描规则详见 [references/scan-rules.md](references/scan-rules.md)

1. 用 Glob 查找目标路径下所有 `*Controller.java` 文件
2. 读取每个 Controller，提取类级 `@RequestMapping` 路径
3. 逐方法提取：HTTP 方法、路径、参数来源（`@RequestBody`/`@PathVariable`/`@RequestParam`/`@RequestHeader`）
4. 拼接完整路径 = context-path + 类级路径 + 方法级路径
5. 对每个 `@RequestBody` 引用的 DTO，按解析顺序查找并读取源码
6. 解析 DTO 字段：类型、校验注解（`@NotNull`/`@Size`/`@Pattern` 等）、嵌套对象、枚举
7. 解析枚举类获取枚举值
8. 识别鉴权注解（`@RequiresAuth`/`@PreAuthorize`/Spring Security 等）
9. 标记跨模块依赖、危险接口、无法解析项

**模块边界控制：**
- 目标扫描路径下 → 完整扫描 + 生成测试
- common/framework/base 包 → 仅解析类型
- 其他业务模块 → 跳过接口，标记跨模块依赖

### 阶段三：测试用例设计

用例类型、生成强度模式和生成规则详见 [references/test-case-types.md](references/test-case-types.md)

**3.1 确定生成强度模式**

询问用户选择生成强度（用户未指定时默认 `standard`）：

| 模式 | 说明 | 每接口用例数 |
|---|---|---|
| `smoke` | 冒烟模式，仅 1-3 条核心用例 | 1–3 |
| `standard` | 标准模式，每字段生成核心异常 | 5–15 |
| `strict` | 严格模式，全边界全异常 | 15–50 |
| `security` | 安全模式，仅 SQL 注入/XSS/超长输入 | 5–10 |
| `performance` | 性能模式，仅正常链路 | 1–3 |

将选定的模式写入 `test_model.json` 的 `generationMode` 字段。

**3.2 按模式生成用例**

根据 generationMode 对应的 caseType 矩阵生成用例。关键控制：
- `smoke` 模式下必填缺失仅测试**首个**必填字段，非全部字段
- `standard` 模式下每个字段最多 1-2 条异常，不展开边界值组合
- `strict` 模式下所有字段所有异常类型全覆盖
- 每条用例标注 `priority`（P0/P1/P2）和 `enabled`（P0/P1 默认 true，P2 默认 false）

**3.3 用例属性规则**

| priority | 含义 | enabled 默认值 |
|---|---|---|
| P0 | 阻断性：正常值、鉴权缺失 | true |
| P1 | 核心功能：必填缺失、null、类型错误 | true |
| P2 | 补充验证：边界值、极限值、特殊字符 | false |

| riskLevel | 含义 | 说明 |
|---|---|---|
| low | 常规 | 无特殊风险 |
| medium | 需关注 | 跨模块依赖、动态参数 |
| high | 高风险 | 危险接口 |

**3.4 用例编号**：`TC_{MODULE}_{ACTION}_{SEQ}`

**3.5 危险接口识别**：delete/remove/pay/refund/transfer/approve/submit 等关键词 → riskLevel=high，不加入性能压测

**3.6 接口链路**：尝试识别 create→detail→update→list→delete 链路；跨模块链路仅标记不默认纳入

**3.7 禁止伪造**：不得伪造源码中不存在的字段、token、业务状态、数据库 ID 或鉴权规则

**3.8 特殊场景处理：**
- **文件上传**（`@RequestPart`/`MultipartFile`）：标记 `needManualConfirm`，在 requestBody 中提示需配置测试文件路径
- **Date/LocalDateTime 字段**：生成 ISO 格式（`2024-01-01T00:00:00`）作为正常值，非法格式作为异常值
- **BigDecimal/Number 字段**：测试负数、零、极大值
- **Boolean 字段**：测试 `true`、`false`、非布尔值（如 `"yes"`）
- **泛型包装类**（如 `Result<T>`）：尝试解析泛型参数；无法解析时标记 `needManualConfirm`
- **Map<String,Object>/JSONObject 请求体**：标记 `needManualConfirm`，建议用户补充接口文档

### 阶段四：构建 JSON 中间模型

将扫描结果和测试用例整合为 `test_model.json`，结构如下：

```json
{
  "projectName": "",
  "scanMode": "full|module|controller",
  "generationMode": "smoke|standard|strict|security|performance",
  "jmeterMode": "csv-driven|per-case",
  "moduleName": "",
  "controllerName": "",
  "scanPath": "",
  "baseUrl": "",
  "contextPath": "",
  "authDetected": false,
  "statistics": {
    "Controller 数量": 0,
    "接口数量": 0,
    "可完整解析接口": 0,
    "需人工确认接口": 0,
    "危险接口": 0,
    "生成测试用例数量": 0
  },
  "apis": [
    {
      "moduleName": "",
      "controllerName": "",
      "apiName": "",
      "method": "GET|POST|PUT|DELETE|PATCH",
      "path": "",
      "requestBodyType": "",
      "authRequired": false,
      "dangerous": false,
      "parseStatus": "完整|部分|失败"
    }
  ],
  "testCases": [],
  "risks": [
    {
      "api": "",
      "riskType": "",
      "reason": "",
      "suggestion": ""
    }
  ],
  "manualConfirmItems": [
    {
      "id": "",
      "type": "",
      "location": "",
      "problem": "",
      "suggestion": ""
    }
  ],
  "dangerousApis": [
    {
      "apiName": "",
      "method": "",
      "path": "",
      "dangerKeyword": "",
      "riskLevel": "high",
      "excludeFromPerf": true
    }
  ],
  "crossModuleDependencies": [
    {
      "from": "",
      "to": "",
      "type": "",
      "description": ""
    }
  ]
}
```

每条 testCase 必须包含：caseId、moduleName、controllerName、apiName、method、path、caseName、caseType、field、description、precondition、requestHeaders、pathVariables、queryParams、requestBody、expectedHttpStatus、expectedBizCode、expectedMessageContains、expectedJsonPath、expectedResult、priority、riskLevel、enabled、needManualConfirm、manualConfirmReason、remark

**JSON 校验检查项（写入文件前必须验证）：**
1. `scanMode` 必须是 `full`/`module`/`controller` 之一
2. 每个 testCase 的 `caseId` 必须唯一
3. 每个 testCase 的 `method` 必须是 GET/POST/PUT/DELETE/PATCH
4. 每个 testCase 的 `expectedHttpStatus` 必须是整数
5. `apis` 和 `testCases` 数组不能为空（除非确实无接口）
6. 如果 `scanMode=module`，`moduleName` 不能为空
7. 如果 `scanMode=controller`，`controllerName` 不能为空

### 阶段五：调用脚本生成输出

**输出目录命名规则：** 每次生成创建带时间戳的新目录，格式 `api-test-output-{yyyyMMddHHmmSSS}`（年月日时分毫秒），例如 `api-test-output-20260503162500137`。多次运行不会删除或覆盖旧目录。

使用 Bash 生成时间戳：
```bash
echo "api-test-output-$(date +%Y%m%d%H%M%S%3N)"
```
将输出结果作为本次的输出目录名 `OUTPUT_DIR`。

将 `test_model.json` 保存到 `${OUTPUT_DIR}/` 目录，同时将 `apis` 数组单独写入 `${OUTPUT_DIR}/01_api_summary/api_list.json`，然后依次运行：

```bash
python scripts/generate_jmx.py ${OUTPUT_DIR}/test_model.json ${OUTPUT_DIR}/03_jmeter/
python scripts/generate_csv.py ${OUTPUT_DIR}/test_model.json ${OUTPUT_DIR}/03_jmeter/
python scripts/generate_excel.py ${OUTPUT_DIR}/test_model.json ${OUTPUT_DIR}/02_test_cases/
python scripts/generate_markdown.py ${OUTPUT_DIR}/test_model.json ${OUTPUT_DIR}/04_reports/ ${OUTPUT_DIR}/05_risks/
```

注意：Markdown 报告中的 `scan_summary.md`、`api_list.md`、`test_cases.md`、`README.md` 由脚本生成到 `${OUTPUT_DIR}/` 根目录，风险和参考文档生成到对应子目录。

**不得删除、清空或覆盖已有的 `api-test-output-*` 目录。**

输出目录结构：

```
api-test-output-{yyyyMMddHHmmSSS}/
├── 01_api_summary/
│   ├── api_list.md
│   └── api_list.json
├── 02_test_cases/
│   └── {prefix}_test_cases.xlsx
├── 03_jmeter/
│   ├── {prefix}_test_plan.jmx
│   ├── {prefix}_cases.csv
│   ├── {prefix}_jmeter_variables.properties
│   └── run_{prefix}.md
├── 04_reports/
│   ├── expected_result_reference.md
│   ├── result_jtl_parse_rule.md
│   ├── dangerous_api_list.md
│   ├── scan_summary.md
│   ├── test_cases.md
│   └── README.md
├── 05_risks/
│   ├── risk_report.md
│   └── manual_confirm_items.md
└── test_model.json
```

文件命名规则：
- 完整项目模式：`test_plan`、`test_cases` 等
- 模块级模式：`{module}_module_test_plan`、`{module}_module_cases` 等
- 单 Controller 模式：`{Controller}_test_plan`、`{Controller}_cases` 等

### 阶段六：向用户展示结果

简洁列出所有生成文件，包含扫描摘要统计。格式：

```markdown
已完成接口测试资产生成。输出目录：api-test-output-{yyyyMMddHHmmSSS}/

## 生成结果

| 类型 | 文件 | 说明 |
|---|---|---|
| 扫描摘要 | 04_reports/scan_summary.md | 扫描范围、接口数量、风险统计 |
| 接口清单 | 01_api_summary/api_list.md | 已识别接口列表 |
| 测试用例 | 02_test_cases/{prefix}_test_cases.xlsx | 可人工审核和二次编辑 |
| JMeter 脚本 | 03_jmeter/{prefix}_test_plan.jmx | 可直接导入 JMeter |
| 参数化数据 | 03_jmeter/{prefix}_cases.csv | 每行一条测试用例 |
| 执行说明 | 03_jmeter/run_{prefix}.md | 运行命令和注意事项 |
| 风险报告 | 05_risks/risk_report.md | 危险接口、跨模块依赖、需确认项 |

## 重要提示

- 异常用例返回 400/401/403 不一定是失败，以断言规则判断
- 危险接口默认未加入性能压测
- 需人工确认：token、baseUrl、业务成功码、真实测试数据
- 旧输出目录保留不删除，如需清理请手动操作
```

## 风险识别

风险识别规则详见 [references/risk-rules.md](references/risk-rules.md)

必须识别并报告：
1. **危险接口** — delete/remove/pay/refund/transfer 等关键词
2. **跨模块依赖** — DTO/Service 引用其他业务模块
3. **无法静态推断** — Map<String,Object>、JSONObject、泛型、token、签名、验证码
4. **鉴权风险** — token 获取方式未知、权限配置不明

所有无法确定的内容必须标记 `needManualConfirm`，不得伪造。

## JMeter 生成规范

JMX 结构、CSV 格式、断言规则详见 [references/jmeter-spec.md](references/jmeter-spec.md)

### 双模式支持

根据 `test_model.json` 的 `jmeterMode` 字段选择 JMeter 生成模式（默认自动判断）：

| 模式 | jmeterMode | 触发条件 | 说明 |
|---|---|---|---|
| CSV 参数化模式 | `csv-driven` | 用例数 > 10，或完整项目/模块级扫描 | 一个通用 HTTPSampler + CSV 循环驱动 |
| 逐用例模式 | `per-case` | 用例数 <= 10，或单 Controller 模式 | 每条用例一个独立 HTTPSampler |

**CSV 参数化模式优势：**
- .jmx 文件轻量，不受用例数影响
- 用例全部在 cases.csv 中维护，前端可直接编辑
- result.jtl 通过 `${caseId}_${caseName}` 追踪每条用例
- 适合批量生成和持续集成

**逐用例模式适用场景：**
- 用例数少（<=10），需要在 JMeter GUI 中逐个调试
- 每个 HTTPSampler 独立可见，方便断点排查

**自动判断规则：** `jmeterMode` 未指定时：
- 用例总数 <= 10 → 自动使用 `per-case`
- 用例总数 > 10 → 自动使用 `csv-driven`
- scanMode=controller 且用例 <= 20 → `per-case`

关键规则：
- CSV 模式 Sampler label：`${caseId}_${caseName}`
- 逐用例模式 Sampler label：`{caseId}_{caseName}`
- cases.csv 包含所有用例参数
- 异常用例断言匹配 expectedHttpStatus（如 400），不统一断言 200
- 正式压测使用非 GUI 模式：`jmeter -n -t xxx.jmx -l result.jtl -e -o report`

## 脚本说明

| 脚本 | 功能 | 依赖 |
|---|---|---|
| `scripts/generate_jmx.py` | JSON → JMeter .jmx + .properties | 无 |
| `scripts/generate_csv.py` | JSON → cases.csv | 无 |
| `scripts/generate_excel.py` | JSON → .xlsx 多 Sheet 工作簿 | openpyxl |
| `scripts/generate_markdown.py` | JSON → 所有 .md 报告 | 无 |

所有脚本用法：`python <script> <test_model.json> [输出目录]`
