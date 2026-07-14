
    
    

select
    PRIORITY_ID as unique_field,
    count(*) as n_records

from "sales_platform"."marts"."dim_priority"
where PRIORITY_ID is not null
group by PRIORITY_ID
having count(*) > 1


