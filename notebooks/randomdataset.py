"""
Synthetic dataset generator for the public portfolio version of this project.

Produces fully fabricated data (no real user, spend, or sales figures) that
mirrors the exact file structure, column names, and data types of the
original `data/` folder, so the accompanying notebooks run unchanged:

    ad_channels.csv  -> channel_id (int), channel (str)
    clicks.csv       -> click_datetime (datetime str), channel_id (int), user_id (int)
    locks.csv        -> lock_id (int), user_id (int), lock_datetime (datetime str)
    sales.csv        -> user_id (float, some NaN), lock_id (int), sale_datetime (str),
                        sale_id (int), make (str), model (str), has_trade_in (0/1),
                        is_financed (0/1), apr (float, NaN when not financed),
                        delivery_distance (int)
    spend.csv        -> channel_id (int), date (str), spend (float)
    vehicles.csv     -> make (str), model (str), bodystyle (str), avg_margin (float)

Run from the `notebooks/` folder; files are written to the current directory.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

# ---------------------------------------------------------------------------
# 1. AD CHANNELS  (generic partner names, no real brands)
# ---------------------------------------------------------------------------
channel_defs = [
    "Search Engine-SearchPartnerA_Convertible",
    "Search Engine-SearchPartnerA_Sedan",
    "Search Engine-SearchPartnerA_Truck",
    "Search Engine-SearchPartnerB_Convertible",
    "Search Engine-SearchPartnerB_Sedan",
    "Search Engine-SearchPartnerB_Truck",
    "Online Video-VideoPlatformA_Teen",
    "Online Video-VideoPlatformA_25+",
    "Online Video-VideoPlatformB_Teen",
    "Online Video-VideoPlatformB_25+",
    "Finance Partnership-FinancePartnerA",
    "Finance Partnership-FinancePartnerB",
    "Social Media-SocialPlatformA",
    "Social Media-SocialPlatformB",
    "Third Party Listing-ListingPartnerA",
    "Third Party Listing-ListingPartnerB",
]
df_ad_channels = pd.DataFrame({
    "channel_id": range(1, len(channel_defs) + 1),
    "channel": channel_defs,
})
n_channels = len(df_ad_channels)

# ---------------------------------------------------------------------------
# 2. VEHICLES  (generic industry make/model/bodystyle reference table)
# ---------------------------------------------------------------------------
vehicle_defs = [
    ("Toyota", "Tacoma", "Truck"), ("Nissan", "Sentra", "Sedan"),
    ("Audi", "A4", "Sedan"), ("Toyota", "RAV4", "SUV"),
    ("BMW", "X3", "SUV"), ("Volkswagen", "Beetle", "Hatchback"),
    ("Ford", "F-150", "Truck"), ("Jeep", "Wrangler", "SUV"),
    ("Honda", "HR-V", "SUV"), ("Ford", "Mustang", "Coupe"),
    ("Nissan", "Leaf", "Hatchback"), ("Land Rover", "Range Rover", "SUV"),
    ("Ford", "Escape", "SUV"), ("BMW", "5 Series", "Sedan"),
    ("Chevrolet", "Malibu", "Sedan"), ("Porsche", "Panamera", "Sedan"),
    ("Chevrolet", "Silverado", "Truck"), ("Mercedes-Benz", "S-Class", "Sedan"),
    ("BMW", "3 Series", "Sedan"), ("Mercedes-Benz", "GLE", "SUV"),
    ("Audi", "A6", "Sedan"), ("Audi", "Q3", "SUV"),
    ("Subaru", "WRX", "Sedan"), ("Nissan", "Titan", "Truck"),
    ("Porsche", "911", "Coupe"), ("Hyundai", "Veloster", "Hatchback"),
    ("Hyundai", "Sonata", "Sedan"), ("Ford", "Fusion", "Sedan"),
    ("Subaru", "Forester", "SUV"), ("Honda", "CR-V", "SUV"),
    ("Tesla", "Model S", "Sedan"), ("Volkswagen", "Passat", "Sedan"),
    ("Mercedes-Benz", "GLC", "SUV"), ("Honda", "Civic", "Sedan"),
    ("Toyota", "Corolla", "Sedan"), ("Mercedes-Benz", "E-Class", "Sedan"),
    ("Ram", "1500", "Truck"), ("Tesla", "Model 3", "Sedan"),
    ("Chevrolet", "Equinox", "SUV"), ("Chevrolet", "Camaro", "Coupe"),
]
df_vehicles = pd.DataFrame(vehicle_defs, columns=["make", "model", "bodystyle"])
# Random (fabricated) average margin per vehicle, loosely modeled on a
# right-skewed real-world margin distribution.
df_vehicles["avg_margin"] = np.round(
    np.random.gamma(shape=3.0, scale=170, size=len(df_vehicles)), 2
)

# ---------------------------------------------------------------------------
# 3. SPEND  (per channel, daily spend over a ~7 month window)
# ---------------------------------------------------------------------------
date_range = pd.date_range("2022-06-01", "2022-12-31", freq="D")
spend_rows = []
for channel_id in df_ad_channels["channel_id"]:
    daily_spend = np.round(np.random.gamma(shape=1.1, scale=75, size=len(date_range)), 2)
    daily_spend = np.clip(daily_spend, 0.01, None)
    for d, s in zip(date_range, daily_spend):
        spend_rows.append({"channel_id": channel_id, "date": d.strftime("%Y-%m-%d"), "spend": s})
df_spend = pd.DataFrame(spend_rows)

# ---------------------------------------------------------------------------
# 4. CLICKS  (top of funnel)
# ---------------------------------------------------------------------------
n_users_pool = 8000
user_pool = np.random.randint(10_000_000, 99_999_999, n_users_pool)

n_clicks = 20000
click_start = datetime(2022, 5, 18)
click_end = datetime(2023, 4, 2)
click_span_seconds = int((click_end - click_start).total_seconds())

df_clicks = pd.DataFrame({
    "click_datetime": [
        (click_start + timedelta(seconds=int(np.random.uniform(0, click_span_seconds))))
        .strftime("%Y-%m-%d %H:%M:%S.%f")
        for _ in range(n_clicks)
    ],
    "channel_id": np.random.randint(1, n_channels + 1, n_clicks),
    "user_id": np.random.choice(user_pool, n_clicks),
})

# ---------------------------------------------------------------------------
# 5. LOCKS  (rate-lock funnel step; ~70% of users also appear in clicks,
#    the rest represent direct/untracked traffic, matching the real data's
#    partial click-to-lock overlap)
# ---------------------------------------------------------------------------
n_locks = 1200
clicked_users = df_clicks["user_id"].unique()
n_from_clicks = int(n_locks * 0.7)
n_direct = n_locks - n_from_clicks

lock_users = np.concatenate([
    np.random.choice(clicked_users, n_from_clicks, replace=True),
    np.random.choice(user_pool, n_direct, replace=True),
])
np.random.shuffle(lock_users)

lock_start = datetime(2022, 6, 1)
lock_end = datetime(2023, 1, 31)
lock_span_seconds = int((lock_end - lock_start).total_seconds())

df_locks = pd.DataFrame({
    "lock_id": range(1, n_locks + 1),
    "user_id": lock_users,
    "lock_datetime": [
        (lock_start + timedelta(seconds=int(np.random.uniform(0, lock_span_seconds))))
        .strftime("%Y-%m-%d %H:%M:%S.%f")
        for _ in range(n_locks)
    ],
})

# ---------------------------------------------------------------------------
# 6. SALES  (subset of locks that convert)
# ---------------------------------------------------------------------------
n_sales = 130
sale_locks = df_locks.sample(n=n_sales, replace=False, random_state=42).reset_index(drop=True)

vehicle_choices = df_vehicles.sample(n=n_sales, replace=True, random_state=7).reset_index(drop=True)
is_financed = np.random.choice([0, 1], size=n_sales, p=[0.35, 0.65])
has_trade_in = np.random.choice([0, 1], size=n_sales, p=[0.55, 0.45])

apr = np.where(
    is_financed == 1,
    np.clip(np.random.normal(0.09, 0.05, n_sales), 0.012, 0.34),
    np.nan,
)

delivery_distance = np.clip(np.random.gamma(shape=1.5, scale=420, size=n_sales), 0, 2214).astype(int)

sale_user_ids = sale_locks["user_id"].astype(float).to_numpy()
# A small fraction of sales have a missing user_id, mirroring the real data.
missing_idx = np.random.choice(n_sales, size=max(1, int(n_sales * 0.01)), replace=False)
sale_user_ids[missing_idx] = np.nan

sale_dt_start = datetime(2022, 9, 1)
sale_dt_end = datetime(2023, 1, 5)
sale_span_seconds = int((sale_dt_end - sale_dt_start).total_seconds())

df_sales = pd.DataFrame({
    "user_id": sale_user_ids,
    "lock_id": sale_locks["lock_id"],
    "sale_datetime": [
        "{m}/{d}/{y} {h}:{mi:02d}".format(
            m=dt.month, d=dt.day, y=dt.year, h=dt.hour, mi=dt.minute
        )
        for dt in (
            sale_dt_start + timedelta(seconds=int(np.random.uniform(0, sale_span_seconds)))
            for _ in range(n_sales)
        )
    ],
    "sale_id": range(1, n_sales + 1),
    "make": vehicle_choices["make"],
    "model": vehicle_choices["model"],
    "has_trade_in": has_trade_in,
    "is_financed": is_financed,
    "apr": np.round(apr, 3),
    "delivery_distance": delivery_distance,
})

# ---------------------------------------------------------------------------
# SAVE
# ---------------------------------------------------------------------------
df_ad_channels.to_csv("ad_channels.csv", index=False)
df_clicks.to_csv("clicks.csv", index=False)
df_locks.to_csv("locks.csv", index=False)
df_sales.to_csv("sales.csv", index=False)
df_spend.to_csv("spend.csv", index=False)
df_vehicles.to_csv("vehicles.csv", index=False)

print("Generated 6 synthetic CSV files matching the original data/ schema:")
print(f"  ad_channels.csv : {len(df_ad_channels)} rows")
print(f"  clicks.csv      : {len(df_clicks)} rows")
print(f"  locks.csv       : {len(df_locks)} rows")
print(f"  sales.csv       : {len(df_sales)} rows")
print(f"  spend.csv       : {len(df_spend)} rows")
print(f"  vehicles.csv    : {len(df_vehicles)} rows")
