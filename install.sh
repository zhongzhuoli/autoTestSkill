#!/usr/bin/env bash
# -*- coding: utf-8 -*-
#
# Java API Test Expert Skill 一键安装脚本
# 用法: bash install.sh
#

set -e

SKILL_NAME="java-api-test-expert"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
SKILL_SOURCE="${SCRIPT_DIR}/${SKILL_NAME}"

# 检测 Claude Code skills 目录
if [ -n "$HOME" ]; then
    SKILLS_DIR="${HOME}/.claude/skills"
else
    echo "错误: 无法确定 HOME 目录"
    exit 1
fi

# 创建 skills 目录（如不存在）
mkdir -p "${SKILLS_DIR}"

# 检查是否已安装
TARGET="${SKILLS_DIR}/${SKILL_NAME}"
if [ -d "${TARGET}" ]; then
    echo "检测到已存在旧版本: ${TARGET}"
    echo "将更新为新版本..."
    rm -rf "${TARGET}"
fi

# 复制 skill
cp -r "${SKILL_SOURCE}" "${TARGET}"

# 验证
if [ -f "${TARGET}/SKILL.md" ]; then
    echo ""
    echo "安装成功!"
    echo ""
    echo "  Skill: ${SKILL_NAME}"
    echo "  位置:  ${TARGET}"
    echo ""
    echo "使用方法:"
    echo "  在 Claude Code 中直接对话触发，例如:"
    echo "  - \"扫描这个 Java 项目，生成接口测试资产\""
    echo "  - \"对 UserController 生成测试用例\""
    echo "  - \"扫描 user 模块，strict 模式\""
    echo ""
    echo "依赖安装（如需 Excel 输出）:"
    echo "  pip install openpyxl"
    echo ""
else
    echo "安装失败: 未找到 SKILL.md"
    exit 1
fi
