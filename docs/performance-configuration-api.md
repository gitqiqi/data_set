# 绩效配置接入预留

## 当前落库

当前项目仍按 BI/Hologres 使用，配置内容只从这张表读取和保存：

```text
bi.performance_configuration
```

建表和升级脚本见 [performance_configuration.sql](/Users/cherry/Project/data_set/db/performance_configuration.sql)，需要时手工执行。后端服务运行时不会自动跑 DDL、字段检查或历史回填，只会请求 `/data_set/performance/configuration/list` 读取这张表的数据。

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
| periods | periods | 当前期别数组，`text[]`，例如 `["2026秋", "2026暑"]` |
| period1 | period1 | 旧期别兼容列，由后端从 `periods` 派生 |
| period2 | period2 | 旧期别兼容列，由后端从 `periods` 派生 |
| configType | config_type | 类型，没有时传空字符串 |
| delFlag | del_flag | 逻辑删除，`0` 未删除，`1` 已删除 |

业务唯一键：

```text
configMonth + module
```

同一个月份下，一个指标只保留一条配置；期别、类型、时间范围和配置项都作为这条配置的可更新内容。

页面和保存接口都以 `periods` 为准；`period1` 和 `period2` 只保留做旧数据兼容。后续查询使用 `periods`：

```sql
-- 单个期别
WHERE '2026暑' = ANY(periods)

-- 多个期别任意命中
WHERE periods && ARRAY['2026暑', '2026秋']
```

已有表新增字段和回填逻辑已合并在 [performance_configuration.sql](/Users/cherry/Project/data_set/db/performance_configuration.sql)，只作为手工迁移脚本使用。

## 当前临时权限

当前项目可以先用这张表做权限源：

```text
bi.dim_org_admin_user_info_hf
```

服务端登录时会查询这张表，并把当前用户权限返回给页面。

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
| permission_type | 权限类型 | 仅展示/保留，不作为当前配置页操作权限 |
| permission_scope | 权限范围 | `2` 可操作，其他值只查看 |
| is_full_view | 是否全量查看 | 作为后续数据范围预留 |
| admin_id | 后台用户 ID | 用作 `createBy/updateBy` |
| mobile | 手机号 | 无 adminId 时可用手机号匹配当前用户 |

页面权限结果：

```text
有匹配且 status = 1 的行：可查看
匹配行里存在 permission_scope = 2：可编辑
无匹配行：不可查看
```

## 当前页面访问方式

通过 `server/performance_configuration_server.py` 打开页面时，默认使用登录态识别当前用户。未登录访问配置页会跳到：

```text
/login.html
```

登录接口会查询 `bi.dim_org_admin_user_info_hf`，支持手机号、`admin_id` 或工号登录；`password` 字段只在服务端校验，不返回给前端。登录后写入 `qdata_session` HttpOnly cookie，页面再通过 `/data_set/performance/configuration/adminUserInfo` 获取当前用户权限。

页面会用当前 cookie 登录态请求：

```http
POST /data_set/performance/configuration/adminUserInfo
Content-Type: application/json
```

请求体固定为空对象：

```json
{}
```

调试当前解析结果：

```js
window.getPerformanceConfigurationPermissionState();
```

## 当前接口

```http
POST /data_set/performance/configuration/list
POST /data_set/performance/configuration/periodOptions
POST /data_set/performance/configuration/batchUpsert
POST /data_set/performance/configuration/delete
Content-Type: application/json
```

页面固定请求 qData 后端，配置内容读取和保存到 `bi.performance_configuration`。

列表接口请求体：

```json
{
  "configMonth": null,
  "delFlag": 0
}
```

列表接口返回：

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "records": [
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
        "periods": ["2026秋", "2026暑"],
        "config_type": "常规",
        "del_flag": 0
      }
    ],
    "months": ["2026-09"],
    "activeMonth": "2026-09"
  }
}
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
    "periods": ["2026秋", "2026暑"],
    "configType": "常规",
    "delFlag": 0
  }
]
```
