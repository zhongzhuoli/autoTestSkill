#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
公共工具模块 - 供 generate_*.py 脚本共享使用
"""

import json
import os


def load_model(path):
    """加载 test_model.json"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def get_output_prefix(model):
    """根据 scanMode 生成文件名前缀"""
    mode = model.get("scanMode", "full")
    if mode == "module" and model.get("moduleName"):
        return model["moduleName"] + "_module"
    elif mode == "controller" and model.get("controllerName"):
        return model["controllerName"]
    return "test_plan"


def ensure_output_dir(output_dir):
    """确保输出目录存在"""
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
