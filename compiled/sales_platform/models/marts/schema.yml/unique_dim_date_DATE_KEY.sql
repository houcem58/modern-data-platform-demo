
    
    

select
    DATE_KEY as unique_field,
    count(*) as n_records

from "sales_platform"."marts"."dim_date"
where DATE_KEY is not null
group by DATE_KEY
having count(*) > 1


