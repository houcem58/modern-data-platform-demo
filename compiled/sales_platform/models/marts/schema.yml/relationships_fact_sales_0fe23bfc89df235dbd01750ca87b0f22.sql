
    
    

with child as (
    select CHANNEL_ID as from_field
    from "sales_platform"."marts"."fact_sales"
    where CHANNEL_ID is not null
),

parent as (
    select CHANNEL_ID as to_field
    from "sales_platform"."marts"."dim_channel"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


