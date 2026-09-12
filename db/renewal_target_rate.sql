CREATE SCHEMA IF NOT EXISTS bi;

CREATE TABLE IF NOT EXISTS bi.bi_renewal_target_rate (
  renewal_period_id bigint,
  grade bigint,
  class_mode text,
  class_version text,
  all_rate numeric(38, 10),
  s_rate numeric(38, 10),
  a_rate numeric(38, 10),
  b_rate numeric(38, 10),
  c_rate numeric(38, 10),
  d_rate numeric(38, 10),
  renewal_period_group_key text,
  sort_order integer DEFAULT 0,
  del_flag smallint NOT NULL DEFAULT 0
);

ALTER TABLE bi.bi_renewal_target_rate
  ADD COLUMN IF NOT EXISTS sort_order integer DEFAULT 0;

ALTER TABLE bi.bi_renewal_target_rate
  ADD COLUMN IF NOT EXISTS renewal_period_group_key text;

ALTER TABLE bi.bi_renewal_target_rate
  ADD COLUMN IF NOT EXISTS del_flag smallint DEFAULT 0;

ALTER TABLE bi.bi_renewal_target_rate
  ALTER COLUMN del_flag SET DEFAULT 0;

-- Hologres does not allow DML in the same transaction as ALTER TABLE.
-- If historical rows need explicit singleton group keys, run this UPDATE
-- separately after the DDL statements above:
-- UPDATE bi.bi_renewal_target_rate
-- SET renewal_period_group_key = CAST(renewal_period_id AS text)
-- WHERE renewal_period_group_key IS NULL
--    OR trim(renewal_period_group_key) = '';

-- 已核验的历史数据归并见 db/renewal_target_rate_merge.sql。以下四组期次的
-- 年级、班型、版本及 all_rate/s_rate/a_rate/b_rate/c_rate/d_rate 一致，按组合期次展示：
--   107+106、97+96、93+92、78+77
-- 归并脚本必须在本文件的 DDL 执行完成后单独执行。

COMMENT ON TABLE bi.bi_renewal_target_rate IS '续报目标率配置表';
COMMENT ON COLUMN bi.bi_renewal_target_rate.renewal_period_id IS '续报期 ID';
COMMENT ON COLUMN bi.bi_renewal_target_rate.grade IS '年级';
COMMENT ON COLUMN bi.bi_renewal_target_rate.class_mode IS '班型';
COMMENT ON COLUMN bi.bi_renewal_target_rate.class_version IS '版本';
COMMENT ON COLUMN bi.bi_renewal_target_rate.all_rate IS '总目标率';
COMMENT ON COLUMN bi.bi_renewal_target_rate.s_rate IS 'S 档目标率';
COMMENT ON COLUMN bi.bi_renewal_target_rate.a_rate IS 'A 档目标率';
COMMENT ON COLUMN bi.bi_renewal_target_rate.b_rate IS 'B 档目标率';
COMMENT ON COLUMN bi.bi_renewal_target_rate.c_rate IS 'C 档目标率';
COMMENT ON COLUMN bi.bi_renewal_target_rate.d_rate IS 'D 档目标率';
COMMENT ON COLUMN bi.bi_renewal_target_rate.renewal_period_group_key IS '续报期组合键，多个期次 ID 用 + 连接';
COMMENT ON COLUMN bi.bi_renewal_target_rate.sort_order IS '同一期次下的目标展示顺序';
COMMENT ON COLUMN bi.bi_renewal_target_rate.del_flag IS '逻辑删除标记，0 未删除，1 已删除';

-- The application treats the following columns as the natural key:
-- renewal_period_group_key + renewal_period_id + grade + class_mode + class_version
