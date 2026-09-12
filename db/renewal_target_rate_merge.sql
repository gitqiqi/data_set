-- 续报目标历史期次归并
--
-- 请在 db/renewal_target_rate.sql 的 DDL 完成后单独执行。
-- renewal_period_id 保留原始期次；组合关系写入 renewal_period_group_key。
-- 以下四组已核验其业务配置一致：
--   107+106: 26暑78月物理续报 + 26暑78月数学续报
--   97+96:   26春非待续囤课 + 26春初中非待续大联续
--   93+92:   26春初中大联续 + 26春小学大续报
--   78+77:   5月自然月物理续报 + 5月自然月数学续报

UPDATE bi.bi_renewal_target_rate
SET renewal_period_group_key = CASE renewal_period_id
  WHEN 107 THEN '107+106'
  WHEN 106 THEN '107+106'
  WHEN 97 THEN '97+96'
  WHEN 96 THEN '97+96'
  WHEN 93 THEN '93+92'
  WHEN 92 THEN '93+92'
  WHEN 78 THEN '78+77'
  WHEN 77 THEN '78+77'
END
WHERE renewal_period_id IN (107, 106, 97, 96, 93, 92, 78, 77)
  AND COALESCE(del_flag, 0) = 0;
