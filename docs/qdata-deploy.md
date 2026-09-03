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
```

账号来自 `bi.dim_org_admin_user_info_hf`。登录页支持手机号、`admin_id` 或工号登录；密码只在服务端校验，不返回前端。权限规则是 `status = 1` 可查看，`permission_scope = 2` 可编辑，其他权限范围只能查看。

如果是从旧版本升级，先手工执行一次主表结构脚本，里面已经包含 `periods` 字段新增和历史数据回填：

```sql
\i db/performance_configuration.sql
```

迁移后 `periods text[]` 是当前查询字段；`period1/period2` 只作为旧数据兼容列保留，保存时由后端按 `periods` 派生写入。服务启动和前端访问不会自动执行建表、字段检查或历史回填。

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
