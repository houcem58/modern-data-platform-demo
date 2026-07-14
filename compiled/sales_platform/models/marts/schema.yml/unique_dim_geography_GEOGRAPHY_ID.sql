
    
    

select
    GEOGRAPHY_ID as unique_field,
    count(*) as n_records

from "sales_platform"."marts"."dim_geography"
where GEOGRAPHY_ID is not null
group by GEOGRAPHY_ID
having count(*) > 1


