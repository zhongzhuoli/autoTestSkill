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
3. 读取配置文件（`application.yml`/`application.properties`）获取 context-path、端口
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

用例类型和生成规则详见 [references/test-case-types.md](references/test-case-types.md)

为每个接口按优先级生成测试用例：

**P1（必须）**：正常值、必填缺失、Null、空字符串、类型错误
**P2（推荐）**：边界值、格式错误、枚举非法值、特殊字符、SQL 注入、XSS
**P3（可选）**：极限值、数组异常、嵌套对象异常、鉴权缺失、权限不足
**P4（按需）**：接口方法错误、Content-Type 错误、业务规则、接口链路、危险接口确认

**用例编号**：`TC_{MODULE}_{ACTION}_{SEQ}`

**危险接口识别**：delete/remove/pay/refund/transfer/approve/submit 等关键词 → 标记 high risk，不加入性能压测

**接口链路**：尝试识别 create→detail→update→list→delete 链路；跨模块链路仅标记不默认纳入

**禁止伪造**：不得伪造源码中不存在的字段、token、业务状态、数据库 ID 或鉴权规则

### 阶段四：构建 JSON 中间模型

将扫描结果和测试用例整合为 `test_model.json`，结构如下：

```json
{
  "projectName": "",
  "scanMode": "full|module|controller",
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
  "apis": [],
  "testCases": [],
  "risks": [],
  "manualConfirmItems": [],
  "dangerousApis": [],
  "crossModuleDependencies": []
}
```

每条 testCase 必须包含：caseId、moduleName、controllerName、apiName、method、path、caseName、caseType、field、description、precondition、requestHeaders、pathVariables、queryParams、requestBody、expectedHttpStatus、expectedBizCode、expectedMessageContains、expectedJsonPath、expectedResult、priority、riskLevel、enabled、needManualConfirm、manualConfirmReason、remark

### 阶段五：调用脚本生成输出

将 `test_model.json` 保存到 `api-test-output/` 目录，然后依次运行：

```bash
python scripts/generate_jmx.py api-test-output/test_model.json api-test-output/03_jmeter/
python scripts/generate_csv.py api-test-output/test_model.json api-test-output/03_jmeter/
python scripts/generate_excel.py api-test-output/test_model.json api-test-output/02_test_cases/
python scripts/generate_markdown.py api-test-output/test_model.json api-test-output/
```

输出目录结构：

```
api-test-output/
├── 01_api_summary/
│   ├── scan_summary.md
│   ├── api_list.md
│   └── api_list.json
├── 02_test_cases/
│   └── {prefix}_test_cases.xlsx
├── 03_jmeter/
│   ├── {prefix}_test_plan.jmx
│   ├── {prefix}_cases.csv
│   ├── jmeter_variables.properties
│   └── run_{prefix}.md
├── 04_reports/
│   ├── expected_result_reference.md
│   ├── result_jtl_parse_rule.md
│   └── dangerous_api_list.md
├── 05_risks/
│   ├── risk_report.md
│   └── manual_confirm_items.md
├── test_cases.md
├── scan_summary.md
├── README.md
└── test_model.json
```

文件命名规则：
- 完整项目模式：`test_plan`、`test_cases` 等
- 模块级模式：`{module}_module_test_plan`、`{module}_module_cases` 等
- 单 Controller 模式：`{Controller}_test_plan`、`{Controller}_cases` 等

### 阶段六：向用户展示结果

简洁列出所有生成文件，包含扫描摘要统计。格式：

```markdown
已完成接口测试资产生成。

## 生成结果

| 类型 | 文件 | 说明 |
|---|---|---|
| 扫描摘要 | scan_summary.md | 扫描范围、接口数量、风险统计 |
| 接口清单 | api_list.md | 已识别接口列表 |
| 测试用例 | {prefix}_test_cases.xlsx | 可人工审核和二次编辑 |
| JMeter 脚本 | {prefix}_test_plan.jmx | 可直接导入 JMeter |
| 参数化数据 | {prefix}_cases.csv | 每行一条测试用例 |
| 执行说明 | run_{prefix}.md | 运行命令和注意事项 |
| 风险报告 | risk_report.md | 危险接口、跨模块依赖、需确认项 |

## 重要提示

- 异常用例返回 400/401/403 不一定是失败，以断言规则判断
- 危险接口默认未加入性能压测
- 需人工确认：token、baseUrl、业务成功码、真实测试数据
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

关键规则：
- HTTP Request 名称：`${caseId}_${caseName}`
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
