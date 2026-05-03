#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
从 test_model.json 生成 cases.csv 参数化文件

用法: python generate_csv.py <test_model.json> [输出目录]
"""

import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
from shared_utils import load_model, get_output_prefix, ensure_output_dir


CSV_FIELDS = [
    "caseId", "caseName", "caseType", "moduleName", "method", "path",
    "headers", "queryParams", "pathVariables", "body",
    "expectedHttpStatus", "expectedBizCode", "expectedMessageContains",
    "enabled", "riskLevel"
]


def flatten_case(tc):
    row = {}
    row["caseId"] = tc.get("caseId", "")
    row["caseName"] = tc.get("caseName", "")
    row["caseType"] = tc.get("caseType", "")
    row["moduleName"] = tc.get("moduleName", "")
    row["method"] = tc.get("method", "GET")
    row["path"] = tc.get("path", "")

    headers = tc.get("requestHeaders", {})
    if not headers:
        headers = {"Content-Type": "application/json", "Authorization": "Bearer ${token}"}
    row["headers"] = json.dumps(headers, ensure_ascii=False)

    row["queryParams"] = json.dumps(tc.get("queryParams", {}), ensure_ascii=False)
    row["pathVariables"] = json.dumps(tc.get("pathVariables", {}), ensure_ascii=False)

    body = tc.get("requestBody")
    row["body"] = json.dumps(body, ensure_ascii=False) if body else ""

    row["expectedHttpStatus"] = str(tc.get("expectedHttpStatus", ""))
    row["expectedBizCode"] = str(tc.get("expectedBizCode", ""))
    row["expectedMessageContains"] = tc.get("expectedMessageContains", "")
    row["enabled"] = str(tc.get("enabled", True)).lower()
    row["riskLevel"] = tc.get("riskLevel", "low")

    return row


def main():
    if len(sys.argv) < 2:
        print("用法: python generate_csv.py <test_model.json> [输出目录]")
        sys.exit(1)

    model_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(model_path)

    ensure_output_dir(output_dir)

    model = load_model(model_path)
    prefix = get_output_prefix(model)

    csv_path = os.path.join(output_dir, f"{prefix}_cases.csv")

    test_cases = model.get("testCases", [])
    rows = [flatten_case(tc) for tc in test_cases]

    with open(csv_path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        writer.writerows(rows)

    print(f"  生成: {csv_path}")
    print(f"  用例数: {len(rows)}")
    print("cases.csv 生成完成")


if __name__ == "__main__":
    main()
