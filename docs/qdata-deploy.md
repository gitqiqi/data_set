# qData 部署说明

这个项目可以直接作为 `qData` 跑在 `hm-bi-001` 上，页面和接口都由 `data_set/server/performance_configuration_server.py` 提供。

## 服务地址

服务器对外地址：

```text
http://10.4.230.23:18080
```

页面地址：

```text
http://10.4.230.23:18080/performance-configuration.html
```

未登录访问页面会自动跳到：

```text
http://10.4.230.23:18080/login.html
```

接口地址使用同域相对路径，不需要写死 IP：

```text
/data_set/performance/configuration/list
/data_set/performance/configuration/periodOptions
/data_set/performance/configuration/adminUserInfo
/data_set/performance/configuration/batchUpsert
/data_set/performance/configuration/delete
/data_set/performance/configuration/login
/data_set/performance/configuration/logout
/data_set/performance/configuration/me
```

## data_set 服务配置

在 `hm-bi-001` 的 `.env` 里保留 Hologres 参数，并加上：

```env
APP_NAME=qData
PUBLIC_URL=http://10.4.230.23:18080
BACKEND_HOST=0.0.0.0
BACKEND_PORT=18080
SESSION_MAX_AGE_SECONDS=28800
HOLO_RENEWAL_TARGET_TABLE=bi_renewal_target_rate
```

账号来自 `bi.dim_org_admin_user_info_hf`。登录页支持手机号、`admin_id` 或工号登录；密码只在服务端校验，不返回前端。权限规则是 `status = 1` 可查看，`permission_scope = 2` 可编辑，其他权限范围只能查看。

如果是从旧版本升级，先手工执行一次主表结构脚本，里面已经包含 `periods/sort_order` 字段新增和历史数据回填：

```sql
\i db/performance_configuration.sql
```

迁移后 `period1/period2` 是页面维护字段：普通指标只写 `period1`，`带生数` / `刷题班带生数` 写 `period1` 和 `period2`；`periods text[]` 是后端按两个字段合并出的查询字段，`sort_order` 是同月指标拖拽排序字段。服务启动和前端访问不会自动执行建表、字段检查或历史回填。

早于服务当前月份的绩效配置月份会被视为历史月份：页面置灰只读，保存和删除接口也会拒绝写入。

续报目标模块使用 `bi.bi_renewal_target_rate`，期次下拉来自 `book.db_renewal_period`，页面展示 `period_name`，保存时写 `id` 到 `renewal_period_id`。如果目标库还没有续报目标表，可以手工执行：

```sql
\i db/renewal_target_rate.sql
\i db/renewal_target_rate_merge.sql
```

该模块列表查询以 `book.db_renewal_period` 为主表 `LEFT JOIN` 目标表；目标表没有主键，页面保存时按 `renewal_period_group_key + renewal_period_id + grade + class_mode + class_version` 作为自然键更新。组合期次关系保存在 `bi.bi_renewal_target_rate.renewal_period_group_key`，原始 `renewal_period_id` 仍保留。

启动：

```bash
cd /path/to/data_set
./bin/qdata start
```

如果已经有进程占用 `18080`，先停掉旧项目，或者让域名反代到这个项目实际监听的端口。

常用命令：

```bash
./bin/qdata start
./bin/qdata stop
./bin/qdata restart
./bin/qdata status
./bin/qdata logs
```

## 域名切换

如果域名由 Nginx 管理，推荐域名入口反代到本机服务：

```nginx
server {
    listen 80;
    server_name qdata.example.com;

    location / {
        proxy_pass http://127.0.0.1:18080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

如果不用 Nginx，确保服务器防火墙和安全组允许访问 `10.4.230.23:18080`。
