# Java API Test Expert - Claude Code Skill

Java API 接口测试资产自动生成专家。扫描 Java 项目源码，自动生成测试用例、JMeter 脚本、CSV 参数化文件、Excel 工作簿和风险报告。

## 一键安装

### 方式一：使用安装脚本（推荐）

```bash
# 克隆仓库并安装
git clone https://github.com/<your-username>/autoTestSkill.git
cd autoTestSkill
bash install.sh
```

### 方式二：手动安装

```bash
# 将 skill 目录复制到 Claude Code skills 目录
git clone https://github.com/<your-username>/autoTestSkill.git
cp -r autoTestSkill/java-api-test-expert ~/.claude/skills/
```

### 方式三：直接下载 .skill 文件

从 [Releases](../../releases) 下载最新的 `.skill` 文件，解压到 `~/.claude/skills/` 目录。

## 功能特性

### 三种扫描模式

| 模式 | 输入 | 适用场景 |
|---|---|---|
| 完整项目模式 | 项目根目录 | 全量接口测试 |
| 模块级扫描模式 | 模块目录/包名/Maven 子模块 | 单模块回归 |
| 单 Controller 模式 | 单个 .java 文件 | 局部快速生成 |

### 五种生成强度

| 模式 | 每接口用例数 | 说明 |
|---|---|---|
| smoke | 1–3 | 冒烟验证 |
| standard | 5–15 | 核心异常（默认） |
| strict | 15–50 | 全边界全异常 |
| security | 5–10 | SQL 注入/XSS |
| performance | 1–3 | 压测基线 |

### 输出产物

| 产物 | 格式 | 说明 |
|---|---|---|
| 接口清单 | .md + .json | 按模块/Controller 分组 |
| 测试用例 | .xlsx + .md | 26 个字段完整模型 |
| JMeter 脚本 | .jmx | CSV 驱动/逐用例双模式 |
| 参数化数据 | .csv | 每行一条测试用例 |
| 风险报告 | .md | 危险接口、跨模块依赖、待确认项 |
| 执行说明 | .md | JMeter 运行命令 |

## 使用方法

安装后在 Claude Code 中直接对话触发：

```
# 完整项目扫描
扫描这个 Java 项目，生成接口测试资产

# 模块级扫描（标准模式）
扫描 user 模块，生成测试用例

# 指定生成强度
对 UserController 生成严格模式测试用例

# 安全模式
对订单模块生成安全测试用例
```

## 输出目录

每次生成创建带时间戳的独立目录，不覆盖旧结果：

```
api-test-output-20260503162500137/
├── 01_api_summary/          # 接口清单
├── 02_test_cases/           # Excel 测试用例
├── 03_jmeter/               # JMeter 脚本 + CSV
├── 04_reports/              # 报告文档
├── 05_risks/                # 风险报告
└── test_model.json          # JSON 中间模型
```

## 依赖

- **Python 3.8+** — 脚本运行环境
- **openpyxl** — Excel 生成（`pip install openpyxl`）
- **JMeter 5.0+** — 执行生成的 .jmx 脚本

## 项目结构

```
java-api-test-expert/
├── SKILL.md                     # 主工作流指令
├── scripts/
│   ├── shared_utils.py          # 公共模块
│   ├── generate_jmx.py          # JSON → JMeter .jmx
│   ├── generate_csv.py          # JSON → cases.csv
│   ├── generate_excel.py        # JSON → .xlsx 工作簿
│   └── generate_markdown.py     # JSON → Markdown 报告
└── references/
    ├── scan-rules.md            # 扫描规则
    ├── test-case-types.md       # 用例类型 + 生成强度
    ├── jmeter-spec.md           # JMeter 规范
    └── risk-rules.md            # 风险识别规则
```

## License

MIT
