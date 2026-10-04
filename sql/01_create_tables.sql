-- ============================================================
-- part A: core tables
-- ============================================================

create table if not exists stg_catalog_extract (
    item_code varchar(100),
    variant_code varchar(100),
    variant_ref varchar(255),
    item_name text,
    brand_name varchar(255),
    category_path text,
    unit_price numeric(12, 2),
    color_name varchar(100),
    size_label varchar(100),
    stock_status varchar(50),
    new_in_stock_date date,
    source_file text,
    loaded_at timestamp default current_timestamp
);

create table if not exists variant_summary (
    variant_code varchar(100) primary key,
    item_code varchar(100),
    variant_ref varchar(255),
    item_name text,
    brand_name varchar(255),
    category_path text,
    unit_price numeric(12, 2),
    color_name varchar(100),
    size_label varchar(100),
    stock_status varchar(50),
    variant_rank_in_item integer,
    variants_for_item integer,
    summarized_at timestamp default current_timestamp
);

create table if not exists variant_enrichment (
    variant_code varchar(100) not null,
    enrichment_description text,
    status varchar(50) not null,
    latency_ms integer,
    created_at timestamp default current_timestamp
);

create index if not exists idx_stg_variant_code
    on stg_catalog_extract(variant_code);

create index if not exists idx_enrichment_variant_code
    on variant_enrichment(variant_code);

create index if not exists idx_enrichment_status
    on variant_enrichment(status);