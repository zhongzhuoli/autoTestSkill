# 扫描规则参考

## 模式检测

| 用户输入 | 扫描模式 |
|---|---|
| 单个 `.java` 文件 | 单 Controller 模式 |
| 目录路径、包名、Maven/Gradle 子模块名 | 模块级扫描模式 |
| 项目根目录、无明确目标 | 完整项目模式 |
| 输入模糊 | 列出候选列表，询问用户 |

## 路径解析优先级

1. 直接文件路径 → 直接使用
2. Maven 子模块名（如 `user-service`）→ 在项目根目录下查找匹配目录
3. Java 包名（如 `com.example.modules.user`）→ 转换为路径 `com/example/modules/user`
4. 业务名称（如"用户模块"）→ 搜索匹配的目录/Controller 名称
5. IDE 右键上下文 → 使用选中的文件夹路径

如果匹配到多个候选，列出所有路径供用户选择。

## 模块边界控制

三类资源：

1. **当前模块接口** — 生成测试用例
2. **依赖类**（common/framework/base 包）— 仅用于解析字段类型、枚举、校验规则
3. **其他模块接口** — 不生成测试；标记为跨模块依赖

### 判定规则

| 来源位置 | 处理方式 |
|---|---|
| 目标扫描路径下 | 完整扫描 + 生成测试 |
| common/framework/base/shared/core/ 下 | 仅解析类型 |
| 其他业务模块路径下 | 跳过；标记跨模块依赖 |

## 扫描范围（按目标）

1. Controller → `@RestController`、`@Controller`、类级 `@RequestMapping`
2. 方法 → `@GetMapping`、`@PostMapping`、`@PutMapping`、`@DeleteMapping`、`@PatchMapping`、`@RequestMapping`
3. 参数 → `@RequestBody`、`@PathVariable`、`@RequestParam`、`@RequestHeader`、`@CookieValue`、`@RequestPart`
4. DTO/VO/Entity/Request/Response → 字段类型、嵌套对象、泛型
5. 枚举 → 枚举值，用于边界值和非法值测试用例
6. 校验器 → `@NotNull`、`@NotBlank`、`@NotEmpty`、`@Size`、`@Min`、`@Max`、`@Pattern`、`@Email`、`@Phone`、自定义注解
7. Swagger/OpenAPI → `@Api`、`@ApiOperation`、`@ApiParam`、`@Schema`、`@Operation`、`@Tag`
8. Jackson/Fastjson → `@JsonProperty`、`@JSONField`、`@JsonIgnore`
9. Service → 仅辅助，用于识别业务规则
10. Mapper/Repository → 仅辅助，用于识别数据字段和风险
11. 配置文件 → `application.yml`、`application.properties`，获取 context-path、端口等

## 路径拼接规则

```
完整路径 = context-path + 类级 @RequestMapping + 方法级映射
```

示例：
- 类：`@RequestMapping("/api/user")`，方法：`@PostMapping("/create")` → `POST /api/user/create`
- 类：无注解，方法：`@GetMapping("/detail/{id}")` → `GET /detail/{id}`
- 配置 `server.servlet.context-path=/v2` → 所有路径前缀加 `/v2`

## 过滤配置

用户需要精细控制时：
- `includePaths` / `excludePaths` — 目录过滤
- `includePackages` / `excludePackages` — Java 包过滤
- `includeControllerPattern` / `excludeControllerPattern` — Controller 名称正则
- `includeTags` — Swagger 标签过滤

## DTO 解析顺序

1. 在当前模块目录中查找
2. 在 common/framework/base 包中查找
3. 在其他业务模块中找到 → 标记为跨模块依赖，源码可读则尝试解析
4. 未找到源码 → 生成占位模板，标记 `needManualConfirm`
