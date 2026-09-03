# 绩效配置接入预留

## 当前落库

当前项目仍按 BI/Hologres 使用，配置内容只从这张表读取和保存：

```text
bi.performance_configuration
```

建表和查询脚本见 [performance_configuration.sql](/Users/cherry/Project/data_set/db/performance_configuration.sql)。通过 `data_set` 里的本地后端服务打开页面时，启动后会请求 `/data_set/performance/configuration/list` 读取这张表的数据。

字段命名按宿主项目风格保留，接口使用 camelCase，落库使用 snake_case。

| 接口字段 | 落库字段 | 说明 |
| --- | --- | --- |
| id | id | 后端生成；静态页面本地字符串 id 不作为后端主键提交 |
| createBy | create_by | 当前用户 adminId |
| updateBy | update_by | 当前用户 adminId |
| createDate | create_date | 新增时间 |
| updateDate | update_date | 更新时间 |
| configMonth | config_month | 配置月份，格式 `yyyy-mm`，例如 `2026-08` |
| module | module | 指标名称 |
| content | content | 指标口径说明，可为空 |
| timeStart | time_start | 生效开始日期，可为空 |
| timeEnd | time_end | 生效结束日期，可为空 |
| period1 | period1 | 期别 1 |
| period2 | period2 | 期别 2，没有时传空字符串 |
| configType | config_type | 类型，没有时传空字符串 |
| delFlag | del_flag | 逻辑删除，`0` 未删除，`1` 已删除 |

业务唯一键：

```text
configMonth + module
```

同一个月份下，一个指标只保留一条配置；期别、类型、时间范围和配置项都作为这条配置的可更新内容。

## 当前临时权限

当前项目可以先用这张表做权限源：

```text
bi.dim_org_admin_user_info_hf
```

页面已支持直接注入这张表的查询结果，字段可以是 snake_case，也可以是 camelCase。

推荐查询当前登录人：

```sql
SELECT
  admin_id,
  mobile,
  status,
  user_name,
  role_id,
  role_name,
  admin_organ_id,
  organ_name,
  is_full_view,
  permission_type,
  permission_scope,
  admin_organ_ids,
  parent_ids,
  teacher_uid,
  subject,
  is_group_leader
FROM bi.dim_org_admin_user_info_hf
WHERE status = 1
  AND (
    admin_id = :adminId
    OR mobile = :mobile
  );
```

临时映射规则：

| 表字段 | 含义 | 当前页面用法 |
| --- | --- | --- |
| status | 启用状态 | `1` 才认为有效 |
| permission_type | 权限类型 | `0` 查看，空值或 `1` 操作 |
| permission_scope | 权限范围 | 预留给后续数据范围过滤，当前配置页不按部门过滤 |
| is_full_view | 是否全量查看 | 作为后续数据范围预留 |
| admin_id | 后台用户 ID | 用作 `createBy/updateBy` |
| mobile | 手机号 | 无 adminId 时可用手机号匹配当前用户 |

页面权限结果：

```text
有匹配且 status = 1 的行：可查看
匹配行里存在 permission_type 为空或 1：可编辑
无匹配行：不可查看
```

## 当前页面注入方式

通过 `server/performance_configuration_server.py` 打开页面时，默认使用登录态识别当前用户。未登录访问配置页会跳到：

```text
/login.html
```

登录接口会查询 `bi.dim_org_admin_user_info_hf`，支持手机号、`admin_id` 或工号登录；`password` 字段只在服务端校验，不返回给前端。登录后写入 `qdata_session` HttpOnly cookie，页面再通过 `/data_set/performance/configuration/adminUserInfo` 获取当前用户权限。

本地 demo 默认不开权限，仍然可编辑。要启用临时权限，先设置：

```js
window.PERFORMANCE_CONFIGURATION_ENABLE_AUTH = true;
window.PERFORMANCE_CONFIGURATION_CURRENT_ADMIN_ID = 10001;
window.PERFORMANCE_CONFIGURATION_ADMIN_USER_INFO = [
  {
    admin_id: 10001,
    mobile: "13800000000",
    status: 1,
    user_name: "张三",
    role_id: 1,
    role_name: "运营",
    is_full_view: 1,
    permission_type: 1,
    permission_scope: 2,
    admin_organ_ids: "1,2",
    teacher_uid: 90001,
    subject: 1,
    is_group_leader: 0
  }
];
```

也可以用 URL 临时切用户：

```text
performance-configuration.html?adminId=10001
performance-configuration.html?mobile=13800000000
```

如果当前项目有后端接口查询这张维表，可以开启远程权限：

```js
window.PERFORMANCE_CONFIGURATION_ENABLE_AUTH = true;
window.PERFORMANCE_CONFIGURATION_REMOTE_AUTH = true;
window.PERFORMANCE_CONFIGURATION_ADMIN_INFO_URL = "/data_set/performance/configuration/adminUserInfo";
window.PERFORMANCE_CONFIGURATION_CURRENT_ADMIN_ID = 10001;
```

页面会用 `POST` 请求：

```http
POST /data_set/performance/configuration/adminUserInfo
Content-Type: application/json
token: ${token}
```

请求体：

```json
{
  "adminId": 10001,
  "mobile": null
}
```

返回可以是数组，也可以包在 `data`、`rows` 或 `list` 里。

调试当前解析结果：

```js
window.getPerformanceConfigurationPermissionState();
```

## 接口预留

正式接后端时继续保留宿主项目风格：

```http
POST /data_set/performance/configuration/list
POST /data_set/performance/configuration/periodOptions
POST /data_set/performance/configuration/batchUpsert
POST /data_set/performance/configuration/delete
Content-Type: application/json
token: ${token}
```

直接打开 HTML 文件时默认按本地模式工作，不会请求接口，保存也只写入浏览器 `localStorage`。通过 `server/performance_configuration_server.py` 打开页面时会自动开启远程数据源，配置内容读取 `bi.performance_configuration`。本地服务接口都在 `data_set` 目录内实现：

```js
window.PERFORMANCE_CONFIGURATION_REMOTE_DATA = true;
window.PERFORMANCE_CONFIGURATION_REMOTE_SAVE = true;
window.PERFORMANCE_CONFIGURATION_API_BASE = "/data_set/performance/configuration";
window.PERFORMANCE_CONFIGURATION_TOKEN = "<当前登录 token>";
```

本地脱离后端调试时保持或显式设置：

```js
window.PERFORMANCE_CONFIGURATION_REMOTE_DATA = false;
window.PERFORMANCE_CONFIGURATION_REMOTE_SAVE = false;
```

列表接口请求体：

```json
{
  "configMonth": null,
  "delFlag": 0
}
```

列表接口返回字段可以用 `bi.performance_configuration` 的 snake_case，也可以用页面接口的 camelCase。推荐直接返回：

```json
[
  {
    "id": 1,
    "create_by": 10001,
    "update_by": 10001,
    "create_date": "2026-09-01T10:00:00+08:00",
    "update_date": "2026-09-01T10:00:00+08:00",
    "config_month": "2026-09",
    "module": "带生数",
    "content": "历史学生上课次数：历史期别课消人次",
    "time_start": "2026-08-01",
    "time_end": "2026-08-31",
    "period1": "2026秋",
    "period2": "2026暑",
    "config_type": "常规",
    "del_flag": 0
  }
]
```

期别下拉也走远程接口；开启远程数据源时页面会自动请求，也可以单独指定接口：

```js
window.PERFORMANCE_CONFIGURATION_REMOTE_PERIODS = true;
window.PERFORMANCE_CONFIGURATION_PERIOD_OPTIONS_URL = "/data_set/performance/configuration/periodOptions";
```

如果需要手动刷新配置或期别，可以调用：

```js
window.reloadPerformanceConfigurationRows();
window.reloadPerformanceConfigurationPeriodOptions();
```

期别接口建议直接用 [performance_period_options.sql](/Users/cherry/Project/data_set/db/performance_period_options.sql) 的查询逻辑，返回按期别降序排列：

```json
[
  { "periodName": "2026秋" },
  { "periodName": "2026暑" }
]
```

保存 payload：

```json
[
  {
    "id": null,
    "configMonth": "2026-08",
    "module": "带生数",
    "content": "历史学生上课次数：历史期别课消人次",
    "timeStart": "2026-08-01",
    "timeEnd": "2026-08-31",
    "period1": "2026秋",
    "period2": "2026暑",
    "configType": "常规",
    "delFlag": 0
  }
]
```

## 后续迁移

后续迁移到宿主项目时，把临时权限源替换为宿主项目菜单权限即可：

```text
performanceConfiguration
performanceConfiguration:view
performanceConfiguration:edit
```

前端只需要把 `/admin/sysManage/getUserLoginInfo` 返回的 `menuList.menuKey` 写入：

```js
window.PERFORMANCE_CONFIGURATION_PERMISSIONS = [
  "performanceConfiguration:view",
  "performanceConfiguration:edit"
];
```

后端权限规则：

```text
list：performanceConfiguration:view 或 performanceConfiguration:edit
batchUpsert/delete：performanceConfiguration:edit
```
