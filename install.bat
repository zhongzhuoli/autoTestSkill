@echo off
chcp 65001 >nul 2>&1
setlocal enabledelayedexpansion

set "SKILL_NAME=java-api-test-expert"
set "SCRIPT_DIR=%~dp0"
set "SKILL_SOURCE=%SCRIPT_DIR%%SKILL_NAME%"

:: 检测 skills 目录
set "SKILLS_DIR=%USERPROFILE%\.claude\skills"

:: 创建目录
if not exist "%SKILLS_DIR%" mkdir "%SKILLS_DIR%"

:: 检查旧版本
set "TARGET=%SKILLS_DIR%\%SKILL_NAME%"
if exist "%TARGET%" (
    echo 检测到已存在旧版本，将更新为新版本...
    rmdir /s /q "%TARGET%"
)

:: 复制 skill
xcopy /e /i /q "%SKILL_SOURCE%" "%TARGET%\" >nul

:: 验证
if exist "%TARGET%\SKILL.md" (
    echo.
    echo 安装成功!
    echo.
    echo   Skill: %SKILL_NAME%
    echo   位置:  %TARGET%
    echo.
    echo 使用方法:
    echo   在 Claude Code 中直接对话触发，例如:
    echo   - "扫描这个 Java 项目，生成接口测试资产"
    echo   - "对 UserController 生成测试用例"
    echo.
    echo 依赖安装（如需 Excel 输出）:
    echo   pip install openpyxl
    echo.
) else (
    echo 安装失败: 未找到 SKILL.md
    exit /b 1
)
