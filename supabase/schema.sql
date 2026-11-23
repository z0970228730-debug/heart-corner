-- 芯彤的小角落｜正式版資料庫
-- 使用方式：Supabase 後台 → SQL Editor → 貼上整份 → Run
-- 所有資料只能由 Netlify 上的伺服器程式（service role）讀寫，瀏覽器無法直接存取。

create extension if not exists pgcrypto;

-- 會員
create table if not exists members (
  id uuid primary key default gen_random_uuid(),
  line_user_id text unique not null,
  display_name text not null default '',
  picture_url text,
  phone text,
  birthday date,
  baby_birthday date,
  member_code text unique not null,          -- 給店家掃的會員碼，例如 HSM-7K2M
  referral_code text unique not null,        -- 邀請碼，例如 HS4821
  referred_by uuid references members(id),
  referral_rewarded boolean not null default false,
  first_visit_at timestamptz,
  fish int not null default 0 check (fish >= 0),
  streak_n int not null default 0,
  streak_last date,
  created_at timestamptz not null default now()
);

-- 芯幣（以 0.1 為單位記錄，tenths=10 代表 1 芯幣），每一筆都有自己的到期日，先到期的先用
create table if not exists coin_lots (
  id bigserial primary key,
  member_id uuid not null references members(id) on delete cascade,
  tenths int not null check (tenths > 0),
  remaining int not null check (remaining >= 0),
  source text not null,
  merge_key text,
  earned_at timestamptz not null default now(),
  expires_at timestamptz not null
);
create unique index if not exists coin_lots_merge on coin_lots(member_id, merge_key) where merge_key is not null;
create index if not exists coin_lots_member on coin_lots(member_id, earned_at);

-- 芯幣明細（給客人看的紀錄）
create table if not exists coin_history (
  id bigserial primary key,
  member_id uuid not null references members(id) on delete cascade,
  delta int not null,
  label text not null,
  merge_key text,
  created_at timestamptz not null default now()
);
create unique index if not exists coin_history_merge on coin_history(member_id, merge_key) where merge_key is not null;

-- 每日任務、每日免費轉盤（同一天同一項只能領一次）
create table if not exists task_claims (
  member_id uuid not null references members(id) on delete cascade,
  day date not null,
  task text not null,
  fish int not null default 0,
  created_at timestamptz not null default now(),
  primary key (member_id, day, task)
);

-- 月度徽章
create table if not exists badge_claims (
  member_id uuid not null references members(id) on delete cascade,
  month text not null,
  badge text not null,
  created_at timestamptz not null default now(),
  primary key (member_id, month, badge)
);

-- 票券／折扣碼
create table if not exists coupons (
  id bigserial primary key,
  member_id uuid not null references members(id) on delete cascade,
  code text unique not null,
  kind text not null,                 -- redeem 芯幣兌換、wheel 轉盤、welcome 新朋友體驗券
  title text not null,
  value int not null default 0,
  needs_min_spend boolean not null default true,
  issued_at timestamptz not null default now(),
  expires_at timestamptz not null,
  used_at timestamptz,
  used_spend int,
  used_note text
);
create index if not exists coupons_member on coupons(member_id);

-- 店家操作紀錄（核銷、首次到店）
create table if not exists staff_log (
  id bigserial primary key,
  action text not null,
  member_id uuid references members(id),
  coupon_code text,
  amount int,
  note text,
  created_at timestamptz not null default now()
);

-- 全部鎖起來：瀏覽器端完全無法讀寫，只有伺服器程式可以
alter table members enable row level security;
alter table coin_lots enable row level security;
alter table coin_history enable row level security;
alter table task_claims enable row level security;
alter table badge_claims enable row level security;
alter table coupons enable row level security;
alter table staff_log enable row level security;

-- 加芯幣：merge_key 相同的會合併在同一筆（例如同一天餵貓）
create or replace function add_coins(p_member uuid, p_tenths int, p_label text, p_merge text, p_days int default 365)
returns void language plpgsql as $$
begin
  if p_tenths <= 0 then return; end if;
  if p_merge is null then
    insert into coin_lots(member_id, tenths, remaining, source, expires_at)
      values (p_member, p_tenths, p_tenths, p_label, now() + make_interval(days => p_days));
    insert into coin_history(member_id, delta, label) values (p_member, p_tenths, p_label);
  else
    insert into coin_lots(member_id, tenths, remaining, source, merge_key, expires_at)
      values (p_member, p_tenths, p_tenths, p_label, p_merge, now() + make_interval(days => p_days))
      on conflict (member_id, merge_key) where merge_key is not null
      do update set tenths = coin_lots.tenths + excluded.tenths, remaining = coin_lots.remaining + excluded.remaining;
    insert into coin_history(member_id, delta, label, merge_key) values (p_member, p_tenths, p_label, p_merge)
      on conflict (member_id, merge_key) where merge_key is not null
      do update set delta = coin_history.delta + excluded.delta;
  end if;
end $$;

-- 扣芯幣：先到期的先扣，不夠就回傳 false、什麼都不扣
create or replace function spend_coins(p_member uuid, p_tenths int, p_label text)
returns boolean language plpgsql as $$
declare
  bal int; need int := p_tenths; lot record; take int;
begin
  perform 1 from members where id = p_member for update;
  select coalesce(sum(remaining),0) into bal from coin_lots
    where member_id = p_member and remaining > 0 and expires_at > now();
  if bal < p_tenths then return false; end if;
  for lot in select id, remaining from coin_lots
      where member_id = p_member and remaining > 0 and expires_at > now()
      order by expires_at, id for update loop
    take := least(lot.remaining, need);
    update coin_lots set remaining = remaining - take where id = lot.id;
    need := need - take;
    exit when need = 0;
  end loop;
  insert into coin_history(member_id, delta, label) values (p_member, -p_tenths, p_label);
  return true;
end $$;

-- 餵貓：扣小魚乾、加芯幣（每條 0.1 芯幣，同一天合併成一筆）
create or replace function feed_cat(p_member uuid, p_n int, p_day text)
returns boolean language plpgsql as $$
begin
  update members set fish = fish - p_n where id = p_member and fish >= p_n and p_n > 0;
  if not found then return false; end if;
  perform add_coins(p_member, p_n, '餵貓咪累積', 'feed-' || p_day, 365);
  return true;
end $$;
