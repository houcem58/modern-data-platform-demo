
    
    

select
    PRODUCT_ID as unique_field,
    count(*) as n_records

from "sales_platform"."marts"."dim_product"
where PRODUCT_ID is not null
group by PRODUCT_ID
having count(*) > 1


