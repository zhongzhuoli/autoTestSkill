# JMeter 生成规范参考

## JMX 文件结构

```
Test Plan
├── User Defined Variables (from jmeter_variables.properties)
├── Thread Group
│   ├── Number of Threads: ${threadCount}
│   ├── Ramp-Up Period: ${rampUp}
│   ├── Loop Count: ${loopCount}
│   │
│   ├── HTTP Request Defaults
│   │   ├── Protocol: http
│   │   ├── Server Name: ${baseUrl}
│   │   └── Port: ${port}
│   │
│   ├── HTTP Header Manager
│   │   ├── Content-Type: application/json
│   │   └── Authorization: Bearer ${token}
│   │
│   ├── HTTP Cookie Manager
│   │
│   ├── CSV Data Set Config
│   │   ├── Filename: cases.csv
│   │   ├── Variable Names: caseId,caseName,...
│   │   ├── Delimiter: ,
│   │   └── Recycle on EOF: false
│   │
│   ├── If Controller (${enabled} == true)
│   │   └── HTTP Request (${caseId}_${caseName})
│   │       ├── Method: ${method}
│   │       ├── Path: ${path}
│   │       ├── Body Data: ${body}
│   │       │
│   │       ├── Response Assertion
│   │       │   └── Field: Response Code / Pattern: ${expectedHttpStatus}
│   │       │
│   │       ├── JSON Assertion (如需要)
│   │       │   └── JSON Path: ${expectedJsonPath}
│   │       │   └── Expected Value: ${expectedBizCode}
│   │       │
│   │       └── JSR223 Assertion (高级断言)
│   │           └── 检查 expectedMessageContains
│   │
│   ├── Summary Report (仅调试模式)
│   └── View Results Tree (仅调试模式)
```

## cases.csv 字段

```csv
caseId,caseName,caseType,moduleName,method,path,headers,queryParams,pathVariables,body,expectedHttpStatus,expectedBizCode,expectedMessageContains,enabled,riskLevel
```

### 示例行

```csv
TC_USER_CREATE_001,正常创建用户,正常值测试,user,POST,/api/user/create,"{""Content-Type"":""application/json"",""Authorization"":""Bearer ${token}""}","{}","{}","{""username"":""test001"",""age"":18}",200,200,success,true,low
TC_USER_CREATE_002,username缺失,必填字段缺失,user,POST,/api/user/create,"{""Content-Type"":""application/json"",""Authorization"":""Bearer ${token}""}","{}","{}","{""age"":18}",400,40001,参数,true,low
```

## jmeter_variables.properties

```properties
baseUrl=http://localhost:8080
port=8080
contextPath=
token=PLEASE_INPUT_TOKEN
threadCount=1
rampUp=1
loopCount=1
connectTimeout=5000
responseTimeout=10000
```

## 断言规则

1. **Response Assertion** — 验证 HTTP 状态码匹配 `expectedHttpStatus`
2. **JSON Assertion** — 验证 JSON Path 处的值匹配 `expectedBizCode`
3. **JSR223 Assertion** — 验证响应体包含 `expectedMessageContains` 文本

### 异常用例断言

异常测试用例的 `expectedHttpStatus` 为 400/401/403 时：
- Response Assertion 应匹配对应的错误码，不应断言 200
- JSON Assertion 应匹配预期的错误业务码
- 不应因返回非 200 而判定失败

## result.jtl 解析规则

### 用例识别

从 JMeter label 字段提取：
```
label = TC_USER_CREATE_001_正常创建用户
caseId = TC_USER_CREATE_001
caseName = 正常创建用户
```

### 通过/失败判断

| 字段 | 说明 |
|---|---|
| responseCode | 实际 HTTP 状态码 |
| success | JMeter 断言是否通过 |
| assertionFailureMessage | 断言失败原因 |
| label | 用例编号和名称 |
| elapsed | 响应时间 |

### 结果报告字段

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

## 文件命名规则

| 扫描模式 | JMX 命名 | CSV 命名 |
|---|---|---|
| 完整项目 | `test_plan.jmx` | `cases.csv` |
| 模块级 | `{module}_module_test_plan.jmx` | `{module}_module_cases.csv` |
| 单 Controller | `{Controller}_test_plan.jmx` | `{Controller}_cases.csv` |
