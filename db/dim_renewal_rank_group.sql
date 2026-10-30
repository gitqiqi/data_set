-- 先执行本文件，再执行 renewal_target_rate.sql；应用运行时不执行 DDL。
CREATE SCHEMA IF NOT EXISTS bi;
CREATE TABLE IF NOT EXISTS bi.dim_renewal_rank_group (
  id bigint PRIMARY KEY,
  group_name text NOT NULL
);
COMMENT ON TABLE bi.dim_renewal_rank_group IS '续报排名分组维度表';
COMMENT ON COLUMN bi.dim_renewal_rank_group.id IS '分组ID，由服务生成';
COMMENT ON COLUMN bi.dim_renewal_rank_group.group_name IS '分组名称，可跨期次复用';
