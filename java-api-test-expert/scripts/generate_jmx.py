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


def load_model(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_output_prefix(model):
    mode = model.get("scanMode", "full")
    if mode == "module" and model.get("moduleName"):
        return model["moduleName"] + "_module"
    elif mode == "controller" and model.get("controllerName"):
        return model["controllerName"]
    return "test_plan"


def generate_properties(model, output_dir):
    props = {
        "baseUrl": model.get("baseUrl", "http://localhost:8080"),
        "port": "8080",
        "contextPath": model.get("contextPath", ""),
        "token": "PLEASE_INPUT_TOKEN",
        "threadCount": "1",
        "rampUp": "1",
        "loopCount": "1",
        "connectTimeout": "5000",
        "responseTimeout": "10000",
    }
    content = "\n".join(f"{k}={v}" for k, v in props.items()) + "\n"
    path = os.path.join(output_dir, "jmeter_variables.properties")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"  生成: {path}")
    return path


def build_jmx(model):
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
    loop = ET.SubElement(thread_group, "stringProp", name="ThreadGroup.on_sample_error").text = "continue"
    loop_ctrl = ET.SubElement(thread_group, "elementProp", name="ThreadGroup.main_controller",
                              elementType="LoopController", guiclass="LoopControlPanel",
                              testclass="LoopController")
    ET.SubElement(loop_ctrl, "stringProp", name="LoopController.loops").text = "${loopCount}"

    tg_hash = ET.SubElement(tp_hash, "hashTree")

    # HTTP Request Defaults
    defaults = ET.SubElement(tg_hash, "ConfigTestElement", guiclass="HttpDefaultsGui",
                             testclass="ConfigTestElement", testname="HTTP Request Defaults")
    ET.SubElement(defaults, "stringProp", name="HTTPSampler.domain").text = "${baseUrl}"
    ET.SubElement(defaults, "stringProp", name="HTTPSampler.port").text = "${port}"
    ET.SubElement(defaults, "stringProp", name="HTTPSampler.protocol").text = "http"
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
    csv_config = ET.SubElement(tg_hash, "CSVDataSet", guiclass="TestBeanGUI",
                               testclass="CSVDataSet", testname="CSV Data Set Config")
    ET.SubElement(csv_config, "stringProp", name="delimiter").text = ","
    ET.SubElement(csv_config, "stringProp", name="fileEncoding").text = "UTF-8"
    ET.SubElement(csv_config, "stringProp", name="filename").text = "cases.csv"
    ET.SubElement(csv_config, "stringProp", name="variableNames").text = (
        "caseId,caseName,caseType,moduleName,method,path,headers,"
        "queryParams,pathVariables,body,expectedHttpStatus,"
        "expectedBizCode,expectedMessageContains,enabled,riskLevel"
    )
    ET.SubElement(csv_config, "boolProp", name="ignoreFirstLine").text = "true"
    ET.SubElement(csv_config, "boolProp", name="quotedData").text = "true"
    ET.SubElement(csv_config, "boolProp", name="recycle").text = "false"
    ET.SubElement(csv_config, "boolProp", name="stopThread").text = "true"

    # 为每条测试用例生成 HTTP Request
    test_cases = model.get("testCases", [])
    for tc in test_cases:
        enabled = tc.get("enabled", True)
        if not enabled:
            continue

        case_id = tc.get("caseId", "UNKNOWN")
        case_name = tc.get("caseName", "")
        label = f"${{caseId}}_${{caseName}}"

        # If Controller for enabled check
        if_ctrl = ET.SubElement(tg_hash, "IfController", guiclass="IfControllerPanel",
                                testclass="IfController",
                                testname=f"If {case_id}")
        ET.SubElement(if_ctrl, "stringProp", name="IfController.condition").text = "${enabled} == true"
        ET.SubElement(if_ctrl, "boolProp", name="IfController.evaluateAll").text = "false"

        if_hash = ET.SubElement(tg_hash, "hashTree")

        # HTTP Request
        sampler = ET.SubElement(if_hash, "HTTPSamplerProxy", guiclass="HttpTestSampleGui",
                                testclass="HTTPSamplerProxy", testname=label)
        ET.SubElement(sampler, "stringProp", name="HTTPSampler.method").text = "${method}"
        ET.SubElement(sampler, "stringProp", name="HTTPSampler.path").text = "${path}"
        ET.SubElement(sampler, "boolProp", name="HTTPSampler.use_keepalive").text = "true"
        ET.SubElement(sampler, "boolProp", name="HTTPSampler.follow_redirects").text = "true"
        ET.SubElement(sampler, "stringProp", name="HTTPSampler.connect_timeout").text = "${connectTimeout}"
        ET.SubElement(sampler, "stringProp", name="HTTPSampler.response_timeout").text = "${responseTimeout}"

        # Body for POST/PUT/PATCH
        method_val = tc.get("method", "GET")
        if method_val in ("POST", "PUT", "PATCH"):
            ET.SubElement(sampler, "boolProp", name="HTTPSampler.postBodyRaw").text = "true"
            coll_prop = ET.SubElement(sampler, "collectionProp", name="HTTPSampler.argument_list")
            arg = ET.SubElement(coll_prop, "elementProp", name="", elementType="HTTPArgument")
            ET.SubElement(arg, "stringProp", name="Argument.value").text = "${body}"

        sampler_hash = ET.SubElement(if_hash, "hashTree")

        # Response Assertion
        assertion = ET.SubElement(sampler_hash, "ResponseAssertion", guiclass="AssertionGui",
                                  testclass="ResponseAssertion", testname=f"Assert Status {case_id}")
        ET.SubElement(assertion, "intProp", name="Assertion.test_type").text = "8"
        ET.SubElement(assertion, "stringProp", name="Assertion.test_field").text = "Assertion.response_code"
        coll_a = ET.SubElement(assertion, "collectionProp", name="Asserion.test_strings")
        ET.SubElement(coll_a, "stringProp", name="0").text = "${expectedHttpStatus}"

        # JSR223 Assertion for message check
        jsr = ET.SubElement(sampler_hash, "JSR223Assertion", guiclass="TestBeanGUI",
                            testclass="JSR223Assertion", testname=f"Assert Message {case_id}")
        ET.SubElement(jsr, "stringProp", name="scriptLanguage").text = "groovy"
        expected_msg = tc.get("expectedMessageContains", "")
        if expected_msg:
            script = (
                'String expected = vars.get("expectedMessageContains");\n'
                'if (expected != null && !expected.isEmpty() && !expected.equals("null")) {\n'
                '    String response = prev.getResponseDataAsString();\n'
                '    if (!response.contains(expected)) {\n'
                '        AssertionResult result = new AssertionResult("Message check");\n'
                '        result.setFailure(true);\n'
                '        result.setFailureMessage("Response does not contain: " + expected);\n'
                '    }\n'
                '}'
            )
            ET.SubElement(jsr, "stringProp", name="script").text = script

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

    # 生成 jmeter_variables.properties
    generate_properties(model, output_dir)

    # 生成 .jmx
    jmx_root = build_jmx(model)
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
