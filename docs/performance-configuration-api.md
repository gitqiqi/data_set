# 绩效配置接入预留

## 当前落库

当前项目仍按 BI/Hologres 使用，绩效配置从这张表读取和保存：

```text
bi.performance_configuration
```

续报目标模块从这张表读取和保存：

```text
bi.bi_renewal_target_rate
```

续报目标的期次选择来自：

```text
book.db_renewal_period
```

页面展示 `book.db_renewal_period.period_name`，保存时仍写 `book.db_renewal_period.id` 到 `bi.bi_renewal_target_rate.renewal_period_id`。点击加号新增目标时可以选择多个期次；保存后这些期次会写入同一个 `renewal_period_group_key`，顶部筛选以后按一个组合选项展示，例如 `26秋自招大续报+26秋金杯大续报+26秋创新大续报`，不会再拆成多个独立筛选项。历史单期期次会自动按单期组合兼容。

顶部“筛选期次”用于查看配置时单选一个已配置的期次组合；只有点击加号新增目标时，期次选择才支持多选并创建新的组合。

经核验，以下四组期次的「年级 + 班型 + 版本」组合及 `all_rate/s_rate/a_rate/b_rate/c_rate/d_rate` 一致，已将有效记录统一回填为组合键：

| 组合键 | 期次名称 | 每期目标行 |
| --- | --- | ---: |
| `107+106` | 26暑78月物理续报 + 26暑78月数学续报 | 32 |
| `97+96` | 26春非待续囤课 + 26春初中非待续大联续 | 38 |
| `93+92` | 26春初中大联续 + 26春小学大续报 | 35 |
| `78+77` | 5月自然月物理续报 + 5月自然月数学续报 | 37 |

页面会将每组显示为一个组合期次，目标行按相同配置合并展示；底层仍保留每个原始 `renewal_period_id` 的记录，保存时分别更新，便于追溯。可复用的历史归并脚本见 [renewal_target_rate_merge.sql](/Users/cherry/Project/data_set/db/renewal_target_rate_merge.sql)。

续报目标按「期次组合 + 年级 + 班型 + 版本」明细展示；同一组合内可拖拽调整目标行顺序，顺序保存到目标表的 `sort_order`。删除目标使用 `del_flag = 1` 逻辑删除，列表只展示 `del_flag = 0` 的数据；重新配置相同自然键时会恢复为 `del_flag = 0`。已有目标表需要先执行 [renewal_target_rate.sql](/Users/cherry/Project/data_set/db/renewal_target_rate.sql) 的字段迁移。

前端切换到“续报目标”时会在请求体里传：

```json
{
  "moduleKey": "renewalTarget"
}
```

绩效配置建表和升级脚本见 [performance_configuration.sql](/Users/cherry/Project/data_set/db/performance_configuration.sql)，需要时手工执行。续报目标表结构脚本见 [renewal_target_rate.sql](/Users/cherry/Project/data_set/db/renewal_target_rate.sql)，历史期次归并脚本见 [renewal_target_rate_merge.sql](/Users/cherry/Project/data_set/db/renewal_target_rate_merge.sql)。后端服务运行时不会自动跑 DDL、字段检查或历史回填。

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
| period1 | period1 | 首个期别；普通指标为多选期别中的首期，带生数类指标为第一个期别 |
| period2 | period2 | 期别 2；仅带生数类指标使用，其他指标传空字符串 |
| periods | periods | 页面选择的期别数组；普通指标支持多选，带生数类指标由 `period1/period2` 汇总，例如 `["2026秋", "2026暑"]` |
| configType | config_type | 类型，仅 `带生数` / `刷题班带生数` 使用，固定为 `常规` / `招生季`；其他指标传空字符串 |
| sortOrder | sort_order | 同一月份下的指标展示顺序，拖拽调整后保存 |
| delFlag | del_flag | 逻辑删除，`0` 未删除，`1` 已删除 |

业务唯一键：

```text
configMonth + module
```

同一个月份下，一个指标只保留一条配置；期别、类型、时间范围和配置项都作为这条配置的可更新内容。

早于服务当前月份的绩效配置月份视为历史月份，页面仅支持查看，保存和删除接口也会拒绝写入。

页面维护期别时，普通指标可以多选，选中的完整列表落到 `periods`，`period1` 保存首期，`period2` 为空；`带生数` / `刷题班带生数` 使用 `period1/period2` 两个独立期别，`periods` 由两者汇总。后续查询统一使用 `periods`：

```sql
-- 单个期别
WHERE '2026暑' = ANY(periods)

-- 多个期别任意命中
WHERE periods && ARRAY['2026暑', '2026秋']
```

已有表新增 `periods/sort_order` 字段和历史回填逻辑已合并在 [performance_configuration.sql](/Users/cherry/Project/data_set/db/performance_configuration.sql)，只作为手工迁移脚本使用。

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

页面固定请求 qData 后端，绩效配置读取和保存到 `bi.performance_configuration`；续报目标模块传 `moduleKey: "renewalTarget"` 后读取和保存到 `bi.bi_renewal_target_rate`。

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
        "period1": "2026秋",
        "period2": "2026暑",
        "periods": ["2026秋", "2026暑"],
        "config_type": "常规",
        "sort_order": 1,
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
    "period1": "2026秋",
    "period2": "2026暑",
    "periods": ["2026秋", "2026暑"],
    "configType": "常规",
    "sortOrder": 1,
    "delFlag": 0
  }
]
```

续报目标列表请求体：

```json
{
  "moduleKey": "renewalTarget"
}
```

续报目标返回字段：

```json
{
  "records": [
    {
      "renewal_period_id": 107,
      "renewal_period_name": "2026暑3期",
      "renewal_period_group_key": "107",
      "grade": 2,
      "class_mode": "笃学",
      "class_version": "",
      "all_rate": null,
      "s_rate": "0.56",
      "a_rate": "0.64",
      "b_rate": "0.48",
      "c_rate": "0.24",
      "d_rate": "0.16",
      "del_flag": 0
    }
  ],
  "renewalPeriodIds": ["107", "106"],
  "renewalPeriodOptions": [
    { "id": "107", "periodGroupKey": "107", "periodIds": [107], "periodName": "2026暑3期" },
    { "id": "106", "periodGroupKey": "106", "periodIds": [106], "periodName": "2026暑2期" },
    { "id": "107+106", "periodGroupKey": "107+106", "periodIds": [107, 106], "periodName": "2026暑3期+2026暑2期" }
  ],
  "availableRenewalPeriodOptions": [
    { "id": 118, "periodGroupKey": "118", "periodIds": [118], "periodName": "2026秋续报" },
    { "id": 107, "periodGroupKey": "107", "periodIds": [107], "periodName": "2026暑3期" }
  ],
  "activeRenewalPeriodId": "107"
}
```

续报目标保存 payload：

```json
{
  "moduleKey": "renewalTarget",
  "rows": [
    {
      "renewalPeriodId": 107,
      "renewalPeriodGroupKey": "107+106",
      "grade": 2,
      "classMode": "笃学",
      "classVersion": "",
      "allRate": null,
      "sRate": "0.56",
      "aRate": "0.64",
      "bRate": "0.48",
      "cRate": "0.24",
      "dRate": "0.16",
      "originalRenewalPeriodId": 107,
      "originalRenewalPeriodGroupKey": "107",
      "originalGrade": 2,
      "originalClassMode": "笃学",
      "originalClassVersion": "",
      "delFlag": 0
    }
  ]
}
```

续报目标没有数据库主键，服务端按自然键更新：

```text
renewal_period_group_key + renewal_period_id + grade + class_mode + class_version
```

续报目标删除时仍按同一自然键更新数据库，不执行物理删除：

```json
{
  "renewalPeriodId": 107,
  "renewalPeriodGroupKey": "107+106",
  "grade": 2,
  "classMode": "笃学",
  "classVersion": "",
  "originalRenewalPeriodId": 107,
  "originalRenewalPeriodGroupKey": "107+106",
  "originalGrade": 2,
  "originalClassMode": "笃学",
  "originalClassVersion": "",
  "delFlag": 1
}
```
