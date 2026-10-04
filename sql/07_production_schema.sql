create table if not exists dim_item (
    item_code varchar(100) primary key,
    item_name text not null,
    brand_name varchar(255),
    category_path text,
    created_at timestamp default current_timestamp,
    updated_at timestamp default current_timestamp
);

create table if not exists dim_variant (
    variant_code varchar(100) primary key,
    item_code varchar(100) not null,
    variant_ref varchar(255),
    unit_price numeric(12, 2),
    color_name varchar(100),
    size_label varchar(100),
    stock_status varchar(50),
    new_in_stock_date date,
    created_at timestamp default current_timestamp,
    updated_at timestamp default current_timestamp,

    constraint fk_variant_item
        foreign key (item_code)
        references dim_item(item_code)
);

create table if not exists variant_enrichment_history (
    enrichment_id bigserial primary key,
    variant_code varchar(100) not null,
    enrichment_description text,
    status varchar(50) not null,
    latency_ms integer,
    created_at timestamp default current_timestamp,

    constraint fk_enrichment_variant
        foreign key (variant_code)
        references dim_variant(variant_code)
);

create index if not exists idx_variant_item_code
    on dim_variant(item_code);

create index if not exists idx_variant_stock_status
    on dim_variant(stock_status);

create index if not exists idx_variant_category_lookup
    on dim_item(category_path);

create index if not exists idx_enrichment_variant_created
    on variant_enrichment_history(variant_code, created_at desc);

create index if not exists idx_enrichment_status
    on variant_enrichment_history(status);