
    
    

select
    CHANNEL_ID as unique_field,
    count(*) as n_records

from "sales_platform"."marts"."dim_channel"
where CHANNEL_ID is not null
group by CHANNEL_ID
having count(*) > 1


