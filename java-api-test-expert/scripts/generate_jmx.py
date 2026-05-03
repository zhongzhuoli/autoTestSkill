#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 test_model.json 生成 JMeter .jmx 脚本和 jmeter_variables.properties

用法: python generate_jmx.py <test_model.json> [输出目录]
"""

import json
import os
import sys
import xml.etree.ElementTree as ET
from xml.dom import minidom

sys.path.insert(0, os.path.dirname(__file__))
from shared_utils import load_model, get_output_prefix, ensure_output_dir


def generate_properties(model, output_dir, prefix):
    base_url = model.get("baseUrl", "http://localhost:8080")
    port_str = "8080"
    if ":" in base_url.replace("https://", "").replace("http://", ""):
        port_str = base_url.replace("https://", "").replace("http://", "").split(":")[1]
    elif base_url.startswith("https"):
        port_str = "443"

    props = {
        "baseUrl": base_url.split("://")[-1].split(":")[0] if "://" in base_url else base_url.split(":")[0],
        "port": port_str,
        "contextPath": model.get("contextPath", ""),
        "token": "PLEASE_INPUT_TOKEN",
        "threadCount": "1",
        "rampUp": "1",
        "loopCount": "1",
        "connectTimeout": "5000",
        "responseTimeout": "10000",
    }
    content = "\n".join(f"{k}={v}" for k, v in props.items()) + "\n"
    path = os.path.join(output_dir, f"{prefix}_jmeter_variables.properties")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  生成: {path}")
    return path


def build_jmx(model, prefix):
    """根据 jmeterMode 或用例数量自动选择生成模式"""
    test_cases = model.get("testCases", [])
    jmeter_mode = model.get("jmeterMode", "")

    if not jmeter_mode:
        if len(test_cases) <= 10:
            jmeter_mode = "per-case"
        elif model.get("scanMode") == "controller" and len(test_cases) <= 20:
            jmeter_mode = "per-case"
        else:
            jmeter_mode = "csv-driven"

    if jmeter_mode == "per-case":
        return _build_per_case_jmx(model, prefix)
    else:
        return _build_csv_driven_jmx(model, prefix)


def _build_csv_driven_jmx(model, prefix):
    """CSV 参数化模式：一个通用 HTTPSampler + CSV 循环"""
    root = ET.Element("jmeterTestPlan", version="1.2", properties="5.0", jmeter="5.6.3")

    hashTree = ET.SubElement(root, "hashTree")
    test_plan = ET.SubElement(hashTree, "TestPlan", guiclass="TestPlanGui",
                              testclass="TestPlan", testname="API Test Plan")
    ET.SubElement(test_plan, "boolProp", name="TestPlan.functional_mode").text = "false"
    ET.SubElement(test_plan, "boolProp", name="TestPlan.serialize_threadgroups").text = "false"

    tp_hash = ET.SubElement(hashTree, "hashTree")

    thread_group = ET.SubElement(tp_hash, "ThreadGroup", guiclass="ThreadGroupGui",
                                 testclass="ThreadGroup", testname="Thread Group")
    ET.SubElement(thread_group, "intProp", name="ThreadGroup.num_threads").text = "${threadCount}"
    ET.SubElement(thread_group, "intProp", name="ThreadGroup.ramp_time").text = "${rampUp}"
    ET.SubElement(thread_group, "boolProp", name="ThreadGroup.same_user_on_next_iteration").text = "true"
    ET.SubElement(thread_group, "stringProp", name="ThreadGroup.on_sample_error").text = "continue"
    loop_ctrl = ET.SubElement(thread_group, "elementProp", name="ThreadGroup.main_controller",
                              elementType="LoopController", guiclass="LoopControlPanel",
                              testclass="LoopController")
    ET.SubElement(loop_ctrl, "stringProp", name="LoopController.loops").text = "${loopCount}"

    tg_hash = ET.SubElement(tp_hash, "hashTree")

    # HTTP Request Defaults
    defaults = ET.SubElement(tg_hash, "ConfigTestElement", guiclass="HttpDefaultsGui",
                             testclass="ConfigTestElement", testname="HTTP Request Defaults")
    base_url = model.get("baseUrl", "http://localhost:8080")
    protocol = "https" if base_url.startswith("https") else "http"
    ET.SubElement(defaults, "stringProp", name="HTTPSampler.domain").text = "${baseUrl}"
    ET.SubElement(defaults, "stringProp", name="HTTPSampler.port").text = "${port}"
    ET.SubElement(defaults, "stringProp", name="HTTPSampler.protocol").text = protocol
    ET.SubElement(defaults, "stringProp", name="HTTPSampler.contentEncoding").text = "UTF-8"

    # HTTP Header Manager
    header_mgr = ET.SubElement(tg_hash, "HeaderManager", guiclass="HeaderPanel",
                               testclass="HeaderManager", testname="HTTP Header Manager")
    coll = ET.SubElement(header_mgr, "collectionProp", name="HeaderManager.headers")
    h1 = ET.SubElement(coll, "elementProp", name="", elementType="Header")
    ET.SubElement(h1, "stringProp", name="Header.name").text = "Content-Type"
    ET.SubElement(h1, "stringProp", name="Header.value").text = "application/json"
    h2 = ET.SubElement(coll, "elementProp", name="", elementType="Header")
    ET.SubElement(h2, "stringProp", name="Header.name").text = "Authorization"
    ET.SubElement(h2, "stringProp", name="Header.value").text = "Bearer ${token}"

    # HTTP Cookie Manager
    ET.SubElement(tg_hash, "CookieManager", guiclass="CookiePanel",
                  testclass="CookieManager", testname="HTTP Cookie Manager")

    # CSV Data Set Config
    csv_filename = f"{prefix}_cases.csv"
    csv_config = ET.SubElement(tg_hash, "CSVDataSet", guiclass="TestBeanGUI",
                               testclass="CSVDataSet", testname="CSV Data Set Config")
    ET.SubElement(csv_config, "stringProp", name="delimiter").text = ","
    ET.SubElement(csv_config, "stringProp", name="fileEncoding").text = "UTF-8"
    ET.SubElement(csv_config, "stringProp", name="filename").text = csv_filename
    ET.SubElement(csv_config, "stringProp", name="variableNames").text = (
        "caseId,caseName,caseType,moduleName,method,path,headers,"
        "queryParams,pathVariables,body,expectedHttpStatus,"
        "expectedBizCode,expectedMessageContains,enabled,riskLevel"
    )
    ET.SubElement(csv_config, "boolProp", name="ignoreFirstLine").text = "true"
    ET.SubElement(csv_config, "boolProp", name="quotedData").text = "true"
    ET.SubElement(csv_config, "boolProp", name="recycle").text = "false"
    ET.SubElement(csv_config, "boolProp", name="stopThread").text = "true"

    # CSV 驱动的 If Controller + 单个通用 HTTP Sampler
    if_ctrl = ET.SubElement(tg_hash, "IfController", guiclass="IfControllerPanel",
                            testclass="IfController", testname="Skip disabled cases")
    ET.SubElement(if_ctrl, "stringProp", name="IfController.condition").text = "${enabled} == true"
    ET.SubElement(if_ctrl, "boolProp", name="IfController.evaluateAll").text = "false"

    if_hash = ET.SubElement(tg_hash, "hashTree")

    sampler = ET.SubElement(if_hash, "HTTPSamplerProxy", guiclass="HttpTestSampleGui",
                            testclass="HTTPSamplerProxy", testname="${caseId}_${caseName}")
    ET.SubElement(sampler, "stringProp", name="HTTPSampler.method").text = "${method}"
    ET.SubElement(sampler, "stringProp", name="HTTPSampler.path").text = "${path}"
    ET.SubElement(sampler, "boolProp", name="HTTPSampler.use_keepalive").text = "true"
    ET.SubElement(sampler, "boolProp", name="HTTPSampler.follow_redirects").text = "true"
    ET.SubElement(sampler, "stringProp", name="HTTPSampler.connect_timeout").text = "${connectTimeout}"
    ET.SubElement(sampler, "stringProp", name="HTTPSampler.response_timeout").text = "${responseTimeout}"
    ET.SubElement(sampler, "boolProp", name="HTTPSampler.postBodyRaw").text = "true"
    coll_prop = ET.SubElement(sampler, "collectionProp", name="HTTPSampler.argument_list")
    arg = ET.SubElement(coll_prop, "elementProp", name="", elementType="HTTPArgument")
    ET.SubElement(arg, "stringProp", name="Argument.value").text = "${body}"

    sampler_hash = ET.SubElement(if_hash, "hashTree")

    # Response Assertion - HTTP 状态码
    assertion = ET.SubElement(sampler_hash, "ResponseAssertion", guiclass="AssertionGui",
                              testclass="ResponseAssertion", testname="Assert HTTP Status")
    ET.SubElement(assertion, "intProp", name="Assertion.test_type").text = "8"
    ET.SubElement(assertion, "stringProp", name="Assertion.test_field").text = "Assertion.response_code"
    coll_a = ET.SubElement(assertion, "collectionProp", name="Assertion.test_strings")
    ET.SubElement(coll_a, "stringProp", name="0").text = "${expectedHttpStatus}"

    # JSR223 Assertion - 业务码和消息检查
    jsr = ET.SubElement(sampler_hash, "JSR223Assertion", guiclass="TestBeanGUI",
                        testclass="JSR223Assertion", testname="Assert Biz Code & Message")
    ET.SubElement(jsr, "stringProp", name="scriptLanguage").text = "groovy"
    jsr_script = (
        'import org.apache.jmeter.assertions.AssertionResult;\n'
        '\n'
        'String expectedBizCode = vars.get("expectedBizCode");\n'
        'String expectedMsg = vars.get("expectedMessageContains");\n'
        'String response = prev.getResponseDataAsString();\n'
        '\n'
        'if (expectedBizCode != null && !expectedBizCode.isEmpty() && !expectedBizCode.equals("null")) {\n'
        '    try {\n'
        '        def json = new groovy.json.JsonSlurper().parseText(response);\n'
        '        def actualCode = json.code != null ? json.code.toString() : "";\n'
        '        if (actualCode != expectedBizCode) {\n'
        '            prev.setSuccessful(false);\n'
        '            prev.addAssertionResult(new AssertionResult("BizCode check"));\n'
        '            prev.getAssertionResults()[-1].setFailure(true);\n'
        '            prev.getAssertionResults()[-1].setFailureMessage(\n'
        '                "Expected bizCode=" + expectedBizCode + ", actual=" + actualCode);\n'
        '        }\n'
        '    } catch (Exception e) {\n'
        '        // JSON 解析失败时不阻断\n'
        '    }\n'
        '}\n'
        '\n'
        'if (expectedMsg != null && !expectedMsg.isEmpty() && !expectedMsg.equals("null")) {\n'
        '    if (response == null || !response.contains(expectedMsg)) {\n'
        '        prev.setSuccessful(false);\n'
        '        prev.addAssertionResult(new AssertionResult("Message check"));\n'
        '        prev.getAssertionResults()[-1].setFailure(true);\n'
        '        prev.getAssertionResults()[-1].setFailureMessage(\n'
        '            "Response does not contain: " + expectedMsg);\n'
        '    }\n'
        '}'
    )
    ET.SubElement(jsr, "stringProp", name="script").text = jsr_script

    return root


def _build_per_case_jmx(model, prefix):
    """逐用例模式：每条用例一个独立 HTTPSampler，适合小规模调试"""
    root = ET.Element("jmeterTestPlan", version="1.2", properties="5.0", jmeter="5.6.3")

    hashTree = ET.SubElement(root, "hashTree")
    test_plan = ET.SubElement(hashTree, "TestPlan", guiclass="TestPlanGui",
                              testclass="TestPlan", testname="API Test Plan")
    ET.SubElement(test_plan, "boolProp", name="TestPlan.functional_mode").text = "false"
    ET.SubElement(test_plan, "boolProp", name="TestPlan.serialize_threadgroups").text = "false"

    tp_hash = ET.SubElement(hashTree, "hashTree")

    thread_group = ET.SubElement(tp_hash, "ThreadGroup", guiclass="ThreadGroupGui",
                                 testclass="ThreadGroup", testname="Thread Group")
    ET.SubElement(thread_group, "intProp", name="ThreadGroup.num_threads").text = "1"
    ET.SubElement(thread_group, "intProp", name="ThreadGroup.ramp_time").text = "1"
    ET.SubElement(thread_group, "boolProp", name="ThreadGroup.same_user_on_next_iteration").text = "true"
    ET.SubElement(thread_group, "stringProp", name="ThreadGroup.on_sample_error").text = "continue"
    loop_ctrl = ET.SubElement(thread_group, "elementProp", name="ThreadGroup.main_controller",
                              elementType="LoopController", guiclass="LoopControlPanel",
                              testclass="LoopController")
    ET.SubElement(loop_ctrl, "stringProp", name="LoopController.loops").text = "1"

    tg_hash = ET.SubElement(tp_hash, "hashTree")

    base_url = model.get("baseUrl", "http://localhost:8080")
    protocol = "https" if base_url.startswith("https") else "http"

    defaults = ET.SubElement(tg_hash, "ConfigTestElement", guiclass="HttpDefaultsGui",
                             testclass="ConfigTestElement", testname="HTTP Request Defaults")
    ET.SubElement(defaults, "stringProp", name="HTTPSampler.domain").text = base_url.split("://")[-1].split(":")[0] if "://" in base_url else base_url
    port_str = base_url.replace("https://", "").replace("http://", "").split(":")[1] if ":" in base_url.replace("https://", "").replace("http://", "") else ("443" if protocol == "https" else "8080")
    ET.SubElement(defaults, "stringProp", name="HTTPSampler.port").text = port_str
    ET.SubElement(defaults, "stringProp", name="HTTPSampler.protocol").text = protocol
    ET.SubElement(defaults, "stringProp", name="HTTPSampler.contentEncoding").text = "UTF-8"

    header_mgr = ET.SubElement(tg_hash, "HeaderManager", guiclass="HeaderPanel",
                               testclass="HeaderManager", testname="HTTP Header Manager")
    coll = ET.SubElement(header_mgr, "collectionProp", name="HeaderManager.headers")
    h1 = ET.SubElement(coll, "elementProp", name="", elementType="Header")
    ET.SubElement(h1, "stringProp", name="Header.name").text = "Content-Type"
    ET.SubElement(h1, "stringProp", name="Header.value").text = "application/json"
    h2 = ET.SubElement(coll, "elementProp", name="", elementType="Header")
    ET.SubElement(h2, "stringProp", name="Header.name").text = "Authorization"
    ET.SubElement(h2, "stringProp", name="Header.value").text = "Bearer ${token}"

    ET.SubElement(tg_hash, "CookieManager", guiclass="CookiePanel",
                  testclass="CookieManager", testname="HTTP Cookie Manager")

    # 每条用例独立 HTTPSampler
    for tc in model.get("testCases", []):
        case_id = tc.get("caseId", "UNKNOWN")
        case_name = tc.get("caseName", "")
        label = f"{case_id}_{case_name}"

        sampler = ET.SubElement(tg_hash, "HTTPSamplerProxy", guiclass="HttpTestSampleGui",
                                testclass="HTTPSamplerProxy", testname=label)
        ET.SubElement(sampler, "stringProp", name="HTTPSampler.method").text = tc.get("method", "GET")
        path = tc.get("path", "")
        context_path = model.get("contextPath", "")
        if context_path:
            path = context_path + path
        ET.SubElement(sampler, "stringProp", name="HTTPSampler.path").text = path
        ET.SubElement(sampler, "boolProp", name="HTTPSampler.use_keepalive").text = "true"
        ET.SubElement(sampler, "boolProp", name="HTTPSampler.follow_redirects").text = "true"

        method = tc.get("method", "GET")
        body = tc.get("requestBody")
        if method in ("POST", "PUT", "PATCH") and body:
            ET.SubElement(sampler, "boolProp", name="HTTPSampler.postBodyRaw").text = "true"
            coll_prop = ET.SubElement(sampler, "collectionProp", name="HTTPSampler.argument_list")
            arg = ET.SubElement(coll_prop, "elementProp", name="", elementType="HTTPArgument")
            ET.SubElement(arg, "stringProp", name="Argument.value").text = json.dumps(body, ensure_ascii=False)

        # Path variables
        pv = tc.get("pathVariables", {})
        if pv:
            for k, v in pv.items():
                pv_elem = ET.SubElement(sampler, "elementProp", name="", elementType="HTTPArgument")
                ET.SubElement(pv_elem, "stringProp", name="Argument.name").text = k
                ET.SubElement(pv_elem, "stringProp", name="Argument.value").text = str(v)

        sampler_hash = ET.SubElement(tg_hash, "hashTree")

        # Response Assertion
        expected_status = str(tc.get("expectedHttpStatus", 200))
        assertion = ET.SubElement(sampler_hash, "ResponseAssertion", guiclass="AssertionGui",
                                  testclass="ResponseAssertion", testname=f"Assert {case_id}")
        ET.SubElement(assertion, "intProp", name="Assertion.test_type").text = "8"
        ET.SubElement(assertion, "stringProp", name="Assertion.test_field").text = "Assertion.response_code"
        coll_a = ET.SubElement(assertion, "collectionProp", name="Assertion.test_strings")
        ET.SubElement(coll_a, "stringProp", name="0").text = expected_status

    return root


def prettify_xml(elem):
    rough = ET.tostring(elem, encoding="unicode")
    parsed = minidom.parseString(rough)
    lines = parsed.toprettyxml(indent="  ").split("\n")
    return "\n".join(line for line in lines if line.strip())


def main():
    if len(sys.argv) < 2:
        print("用法: python generate_jmx.py <test_model.json> [输出目录]")
        sys.exit(1)

    model_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(model_path)

    os.makedirs(output_dir, exist_ok=True)

    model = load_model(model_path)
    prefix = get_output_prefix(model)

    # 判断 JMeter 模式
    test_cases = model.get("testCases", [])
    jmeter_mode = model.get("jmeterMode", "")
    if not jmeter_mode:
        if len(test_cases) <= 10:
            jmeter_mode = "per-case"
        elif model.get("scanMode") == "controller" and len(test_cases) <= 20:
            jmeter_mode = "per-case"
        else:
            jmeter_mode = "csv-driven"
    model["jmeterMode"] = jmeter_mode
    print(f"  JMeter 模式: {jmeter_mode} (用例数: {len(test_cases)})")

    # 生成 jmeter_variables.properties
    generate_properties(model, output_dir, prefix)

    # 生成 .jmx
    jmx_root = build_jmx(model, prefix)
    jmx_content = prettify_xml(jmx_root)
    jmx_path = os.path.join(output_dir, f"{prefix}_test_plan.jmx")
    with open(jmx_path, "w", encoding="utf-8") as f:
        f.write(jmx_content)
    print(f"  生成: {jmx_path}")

    # 生成 run_jmeter.md
    run_md = generate_run_jmeter_md(prefix)
    run_path = os.path.join(output_dir, f"run_{prefix}.md")
    with open(run_path, "w", encoding="utf-8") as f:
        f.write(run_md)
    print(f"  生成: {run_path}")

    print("JMeter 文件生成完成")


def generate_run_jmeter_md(prefix):
    return f"""# JMeter 执行说明

## 1. 执行前准备

| 配置项 | 当前值 | 是否需修改 |
|---|---|---|
| baseUrl | http://localhost:8080 | 是 |
| token | PLEASE_INPUT_TOKEN | 是 |
| threadCount | 1 | 视情况 |
| loopCount | 1 | 视情况 |
| cases.csv | 已生成 | 否 |

## 2. GUI 调试方式

```bash
jmeter -t {prefix}_test_plan.jmx
```

GUI 模式仅用于调试，不建议正式压测。

## 3. 非 GUI 执行方式

```bash
jmeter -n -t {prefix}_test_plan.jmx -l result.jtl -e -o report
```

## 4. 结果查看

- result.jtl
- report/index.html

## 5. 注意事项

1. 异常测试用例返回 400/401/403 不一定是失败，应以断言预期为准。
2. 危险接口默认禁用或标记高风险，执行前必须人工确认。
3. 如果 token、签名、验证码、数据库 ID 未配置，相关用例可能无法执行。
4. 正式压测请使用非 GUI 模式。
"""


if __name__ == "__main__":
    main()
