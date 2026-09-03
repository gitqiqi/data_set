ALTER TABLE bi.performance_configuration
  ADD COLUMN IF NOT EXISTS periods text[] NOT NULL DEFAULT ARRAY[]::text[];

COMMENT ON COLUMN bi.performance_configuration.periods IS '期别数组，例如 ARRAY[''2026秋'', ''2026暑'']，用于 ANY/&& 查询';

UPDATE bi.performance_configuration
SET periods = ARRAY(
  SELECT DISTINCT btrim(period_name)
  FROM unnest(regexp_split_to_array(concat_ws(',', period1, period2), '[,，、/]')) AS period_name
  WHERE btrim(period_name) <> ''
)
WHERE periods IS NULL
   OR cardinality(periods) = 0;

-- 单个期别匹配：
-- WHERE '2026暑' = ANY(periods)

-- 多个期别任一匹配：
-- WHERE periods && ARRAY['2026暑', '2026秋']
