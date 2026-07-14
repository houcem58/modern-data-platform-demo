
    
    

with child as (
    select SHIP_DATE_KEY as from_field
    from "sales_platform"."marts"."fact_sales"
    where SHIP_DATE_KEY is not null
),

parent as (
    select DATE_KEY as to_field
    from "sales_platform"."marts"."dim_date"
)

select
    from_field

from child
left join parent
    on child.from_field = parent.to_field

where parent.to_field is null


