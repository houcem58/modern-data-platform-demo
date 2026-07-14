
    
    

with child as (
    select PRIORITY_ID as from_field
    from "sales_platform"."marts"."fact_sales"
    where PRIORITY_ID is not null
),

parent as (
    select PRIORITY_ID as to_field
    from "sales_platform"."marts"."dim_priority"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


