rows.append({
    "asin": asin,
    "locale": LOCALE,
    "category": CATEGORY,
    "source": SOURCE,
    "first_seen_at": now,
    "last_seen_at": now,
    "is_active": True,
})

supabase.table("tracked_asins").upsert(
    rows,
    on_conflict="asin,locale",
    returning="minimal"
).execute()