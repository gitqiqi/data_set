SELECT DISTINCT
  concat(class_year, class_season) AS period_name
FROM bi.dim_org_box_class_hf b
WHERE shelf_status = 1
  AND class_year > ''
  AND tag_name = '大班'
  AND is_valen = '正价'
  AND class_name NOT LIKE '%测试%'
  AND del_flag = 0
ORDER BY period_name DESC;
