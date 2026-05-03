#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 test_model.json 生成所有 Markdown 报告文件

用法: python generate_markdown.py <test_model.json> [输出目录]
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from shared_utils import load_model, get_output_prefix, ensure_output_dir


def write_file(path, content):
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  生成: {path}")


def esc(text):
    """转义 Markdown 表格中的管道符"""
    if text is None:
        return ""
    return str(text).replace("|", "\\|")


# ====== scan_summary.md ======
def gen_scan_summary(model, prefix):
    mode_map = {"full": "完整项目模式", "module": "模块级扫描模式", "controller": "单 Controller 模式"}
    mode_label = mode_map.get(model.get("scanMode", "full"), "未知")
    stats = model.get("statistics", {})

    rows = "\n".join(f"| {k} | {v} |" for k, v in stats.items()) if stats else "| - | - |"

    return f"""# 接口测试资产生成摘要

## 1. 扫描模式

- 扫描模式：{mode_label}
- 项目名称：{model.get("projectName", "")}
- 模块名称：{model.get("moduleName", "")}
- 扫描路径：{model.get("scanPath", "")}
- baseUrl：{model.get("baseUrl", "")}
- context-path：{model.get("contextPath", "")}
- 是否识别鉴权：{model.get("authDetected", False)}

## 2. 扫描结果统计

| 指标 | 数量 |
|---|---:|
{rows}

## 3. 生成文件清单

| 文件 | 说明 |
|---|---|
| {prefix}_test_cases.xlsx | Excel 格式测试用例 |
| test_cases.md | Markdown 格式测试用例 |
| {prefix}_test_plan.jmx | JMeter 脚本 |
| {prefix}_cases.csv | JMeter 参数化数据 |
| {prefix}_jmeter_variables.properties | JMeter 环境变量 |
| risk_report.md | 风险报告 |
| run_{prefix}.md | JMeter 执行说明 |
"""


# ====== api_list.md ======
def gen_api_list(model):
    lines = ["# 接口清单\n"]

    apis = model.get("apis", [])
    current_module = None
    current_controller = None

    counter = {}

    for api in apis:
        module = api.get("moduleName", "")
        controller = api.get("controllerName", "")

        if module != current_module:
            lines.append(f"\n## 模块：{module}\n")
            current_module = module
            current_controller = None
            counter = {}

        if controller != current_controller:
            lines.append(f"\n### Controller：{controller}\n")
            lines.append("| 序号 | 接口名称 | 请求方法 | 路径 | 入参类型 | 是否鉴权 | 是否危险 | 解析状态 |")
            lines.append("| ---: | --- | --- | --- | --- | --- | --- | --- |")
            current_controller = controller

        key = (module, controller)
        counter[key] = counter.get(key, 0) + 1
        idx = counter[key]
        lines.append(
            f"| {idx} | {esc(api.get('apiName', ''))} | {esc(api.get('method', ''))} | "
            f"{esc(api.get('path', ''))} | {esc(api.get('requestBodyType', ''))} | "
            f"{esc(api.get('authRequired', ''))} | {esc(api.get('dangerous', ''))} | "
            f"{esc(api.get('parseStatus', ''))} |"
        )

    if not apis:
        lines.append("未扫描到接口。")

    return "\n".join(lines)


# ====== test_cases.md ======
def gen_test_cases(model):
    lines = ["# 接口测试用例\n"]

    test_cases = model.get("testCases", [])
    current_api = None

    for tc in test_cases:
        api_key = f"{tc.get('method', '')} {tc.get('path', '')}"
        if api_key != current_api:
            lines.append(f"\n## 接口：{api_key}\n")
            lines.append("| caseId | 用例名称 | 类型 | 字段 | 入参变化 | 预期 HTTP | 预期业务码 | 启用 | 需确认 |")
            lines.append("| --- | --- | --- | --- | --- | ---: | --- | --- | --- |")
            current_api = api_key

        lines.append(
            f"| {esc(tc.get('caseId', ''))} | {esc(tc.get('caseName', ''))} | "
            f"{esc(tc.get('caseType', ''))} | {esc(tc.get('field', ''))} | "
            f"{esc(tc.get('description', ''))} | {tc.get('expectedHttpStatus', '')} | "
            f"{esc(tc.get('expectedBizCode', ''))} | {tc.get('enabled', True)} | "
            f"{tc.get('needManualConfirm', False)} |"
        )

    if not test_cases:
        lines.append("未生成测试用例。")

    return "\n".join(lines)


# ====== risk_report.md ======
def gen_risk_report(model):
    lines = ["# 风险报告\n"]

    risks = model.get("risks", [])
    if risks:
        lines.append("## 1. 风险列表\n")
        lines.append("| 接口 | 风险类型 | 原因 | 建议 |")
        lines.append("| --- | --- | --- | --- |")
        for r in risks:
            lines.append(
                f"| {esc(r.get('api', ''))} | {esc(r.get('riskType', ''))} | "
                f"{esc(r.get('reason', ''))} | {esc(r.get('suggestion', ''))} |"
            )
    else:
        lines.append("未识别到风险。")

    return "\n".join(lines)


# ====== manual_confirm_items.md ======
def gen_manual_confirm(model):
    lines = ["# 需人工确认项\n"]

    items = model.get("manualConfirmItems", [])
    if items:
        lines.append("| 编号 | 类型 | 位置 | 问题 | 建议 |")
        lines.append("| --- | --- | --- | --- | --- |")
        for item in items:
            lines.append(
                f"| {esc(item.get('id', ''))} | {esc(item.get('type', ''))} | "
                f"{esc(item.get('location', ''))} | {esc(item.get('problem', ''))} | "
                f"{esc(item.get('suggestion', ''))} |"
            )
    else:
        lines.append("无需人工确认项。")

    return "\n".join(lines)


# ====== dangerous_api_list.md ======
def gen_dangerous_apis(model):
    lines = ["# 危险接口清单\n"]

    apis = model.get("dangerousApis", [])
    if apis:
        lines.append("| 接口 | 方法 | 路径 | 危险关键词 | 风险等级 | 压测排除 |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for api in apis:
            lines.append(
                f"| {esc(api.get('apiName', ''))} | {esc(api.get('method', ''))} | "
                f"{esc(api.get('path', ''))} | {esc(api.get('dangerKeyword', ''))} | "
                f"{esc(api.get('riskLevel', 'high'))} | {api.get('excludeFromPerf', True)} |"
            )
    else:
        lines.append("未识别到危险接口。")

    return "\n".join(lines)


# ====== expected_result_reference.md ======
def gen_expected_result_reference():
    return """# 测试结果参考

## 1. 正常值测试

预期：
- HTTP 状态码：200
- 业务 code：成功码（200/SUCCESS/0）
- message：success/操作成功

## 2. 参数校验失败类用例

包括：必填字段缺失、null、空字符串、类型错误、边界值非法、格式错误

预期：
- HTTP 状态码：400（部分项目可能返回 200）
- 业务 code：参数错误码（40001/PARAM_ERROR）
- message：包含"参数""不能为空""格式错误"等

## 3. 鉴权失败类用例

预期：
- HTTP 状态码：401 或 403
- 业务 code：未登录/无权限
- message：包含"未授权""token""权限"

## 4. 安全类用例

SQL 注入和 XSS 测试：
- 不应返回 500 或执行注入语句
- 预期返回参数错误或被过滤后正常处理

## 5. 异常用例判定原则

异常用例返回 400/401/403 **不代表失败**。只有当实际结果不符合该用例的 expectedHttpStatus、expectedBizCode 和 expectedMessageContains 时，才判定为失败。
"""


# ====== result_jtl_parse_rule.md ======
def gen_jtl_parse_rule():
    return """# result.jtl 解析规则

## 1. 用例识别

JMeter 执行结果中的 label 字段包含 caseId：

```
TC_USER_CREATE_001_正常创建用户
```

解析时从 label 中提取：
- caseId = TC_USER_CREATE_001
- caseName = 正常创建用户

## 2. 通过/失败判断

以 JMeter 的 success 字段作为基础判断：

| 判断项 | 说明 |
|---|---|
| responseCode | 实际 HTTP 状态码 |
| success | JMeter 断言是否通过 |
| assertionFailureMessage | 断言失败原因 |
| label | 用例编号和名称 |
| elapsed | 响应时间 |

## 3. 结果报告字段

| 字段 | 说明 |
|---|---|
| caseId | 用例编号 |
| caseName | 用例名称 |
| moduleName | 模块 |
| api | 接口 |
| expectedHttpStatus | 预期 HTTP 状态 |
| actualHttpStatus | 实际 HTTP 状态 |
| expectedBizCode | 预期业务码 |
| actualBizCode | 实际业务码 |
| elapsed | 响应时间 |
| passed | 是否通过 |
| failureReason | 失败原因 |
"""


# ====== README.md ======
def gen_readme(model, prefix):
    return f"""# API 测试资产说明

## 1. 本次生成内容

- 接口清单
- 测试用例
- JMeter 脚本
- 参数化 CSV
- 风险报告
- 执行说明
- 结果解析规则

## 2. 推荐使用顺序

1. 先查看 scan_summary.md
2. 再查看 api_list.md
3. 审核 {prefix}_test_cases.xlsx
4. 修改 jmeter_variables.properties
5. 执行 {prefix}_test_plan.jmx
6. 查看 result.jtl 和 report
7. 根据 risk_report.md 处理风险项

## 3. 文件说明

| 文件 | 用途 |
|---|---|
| {prefix}_test_cases.xlsx | 人工评审测试用例 |
| {prefix}_test_plan.jmx | JMeter 脚本 |
| {prefix}_cases.csv | 参数化测试数据 |
| run_{prefix}.md | 执行说明 |
| risk_report.md | 风险与待确认项 |

## 4. 重要提示

- 异常用例返回 400/401/403 不一定是失败，应以断言规则判断
- 危险接口默认未加入性能压测
- 以下内容仍需人工确认：token、baseUrl、业务成功码、真实测试数据
"""


def main():
    if len(sys.argv) < 2:
        print("用法: python generate_markdown.py <test_model.json> [reports_dir] [risks_dir]")
        print("  reports_dir 和 risks_dir 可选，默认均使用 test_model.json 所在目录")
        sys.exit(1)

    model_path = sys.argv[1]
    reports_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(model_path)
    risks_dir = sys.argv[3] if len(sys.argv) > 3 else reports_dir

    ensure_output_dir(reports_dir)
    ensure_output_dir(risks_dir)

    model = load_model(model_path)
    prefix = get_output_prefix(model)

    # Reports 目录文件
    report_files = {
        "scan_summary.md": gen_scan_summary(model, prefix),
        "api_list.md": gen_api_list(model),
        "test_cases.md": gen_test_cases(model),
        "dangerous_api_list.md": gen_dangerous_apis(model),
        "expected_result_reference.md": gen_expected_result_reference(),
        "result_jtl_parse_rule.md": gen_jtl_parse_rule(),
        "README.md": gen_readme(model, prefix),
    }

    # Risks 目录文件
    risk_files = {
        "risk_report.md": gen_risk_report(model),
        "manual_confirm_items.md": gen_manual_confirm(model),
    }

    for filename, content in report_files.items():
        write_file(os.path.join(reports_dir, filename), content)

    for filename, content in risk_files.items():
        write_file(os.path.join(risks_dir, filename), content)

    print("Markdown 报告生成完成")


if __name__ == "__main__":
    main()
