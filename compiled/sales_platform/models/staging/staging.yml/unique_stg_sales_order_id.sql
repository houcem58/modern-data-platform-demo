
    
    

select
    order_id as unique_field,
    count(*) as n_records

from "sales_platform"."staging"."stg_sales"
where order_id is not null
group by order_id
having count(*) > 1


