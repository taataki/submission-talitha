import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import streamlit as st
from PIL import Image
import os

sns.set_style("whitegrid")
plt.rcParams["figure.facecolor"] = "#f9f9f9"

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bike Sharing Dashboard",
    page_icon="🚲",
    layout="wide",
)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    df = pd.read_csv("main_data.csv")
    df["dteday"] = pd.to_datetime(df["dteday"])
    df.sort_values("dteday", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

df_full = load_data()

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🚲 Bike Sharing")
    st.markdown("---")
    min_date = df_full["dteday"].min().date()
    max_date = df_full["dteday"].max().date()

    date_range = st.date_input(
        "Rentang Tanggal",
        value=[min_date, max_date],
        min_value=min_date,
        max_value=max_date,
    )

    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        start_date, end_date = min_date, max_date

    st.markdown("---")
    st.caption(f"Data: {min_date} – {max_date}")

# ── Filter ────────────────────────────────────────────────────────────────────
df = df_full[
    (df_full["dteday"] >= pd.Timestamp(start_date))
    & (df_full["dteday"] <= pd.Timestamp(end_date))
].copy()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🚲 Bike Sharing Analysis Dashboard")
st.markdown("**Washington D.C. · 2011–2012**")
st.markdown("---")

# ── KPI metrics ───────────────────────────────────────────────────────────────
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Hari", f"{len(df):,}")
col2.metric("Total Rental", f"{df['cnt'].sum():,}")
col3.metric("Rata-rata Harian", f"{int(df['cnt'].mean()):,}")
col4.metric("Maks. Rental/Hari", f"{df['cnt'].max():,}")

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 1.  TREN HARIAN (line chart)
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("📈 Tren Rental Harian")

fig, ax = plt.subplots(figsize=(16, 4))
ax.plot(df["dteday"], df["cnt"], color="#2196F3", linewidth=1.2, alpha=0.85)
ax.fill_between(df["dteday"], df["cnt"], alpha=0.15, color="#2196F3")
ax.set_xlabel("Tanggal")
ax.set_ylabel("Jumlah Rental")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.set_title("Tren Rental Harian")
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 2.  TREN BULANAN YoY  (2011 vs 2012)
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("📅 Tren Rata-rata Rental Bulanan: 2011 vs 2012")

monthly = df.copy()
monthly["yr_label"] = monthly["yr"].map({0: 2011, 1: 2012})
monthly_avg = monthly.groupby(["yr_label", "mnth"])["cnt"].mean().reset_index()

month_names = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"]
monthly_avg["month_name"] = monthly_avg["mnth"].apply(lambda x: month_names[x - 1])

fig, ax = plt.subplots(figsize=(14, 5))
for yr, color, marker in [(2011, "#1976D2", "o"), (2012, "#E53935", "s")]:
    subset = monthly_avg[monthly_avg["yr_label"] == yr]
    ax.plot(subset["month_name"], subset["cnt"],
            label=str(yr), color=color, marker=marker, linewidth=2.5, markersize=7)
ax.set_xlabel("Bulan")
ax.set_ylabel("Rata-rata Rental Harian")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.set_title("Tren Rata-rata Rental Bulanan: 2011 vs 2012")
ax.legend(title="Tahun")
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

# Tabel statistik YoY
st.markdown("**Statistik Tahunan**")
yearly_stats = (
    df.groupby(df["yr"].map({0: 2011, 1: 2012}))["cnt"]
    .agg(["sum", "mean", "median", "max"])
    .rename(columns={"sum": "Total Rental", "mean": "Rata-rata", "median": "Median", "max": "Maks."})
    .applymap(lambda x: f"{int(x):,}")
)
yearly_stats.index.name = "Tahun"
st.dataframe(yearly_stats, use_container_width=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 3.  POLA PER JAM  (embedded pre-generated images)
# ═══════════════════════════════════════════════════════════════════════════════
VIZ_DIR = os.path.join(os.path.dirname(__file__), "viz_images")

st.subheader("🕐 Pola Rata-rata Rental Per Jam")

img_path1 = os.path.join(VIZ_DIR, "viz1_pola_per_jam.png")
if os.path.exists(img_path1):
    st.image(img_path1, use_container_width=True)

# Tabel top jam
st.markdown("**5 Jam Teratas – Hari Kerja vs Akhir Pekan/Libur**")
data_jam_kerja = pd.DataFrame({
    "Jam": [17, 18, 8, 19, 16],
    "Tipe Hari": ["Hari Kerja"] * 5,
    "Avg Rental": [525.29, 492.23, 477.01, 348.40, 293.12],
})
data_jam_libur = pd.DataFrame({
    "Jam": [13, 12, 14, 15, 16],
    "Tipe Hari": ["Akhir Pekan/Libur"] * 5,
    "Avg Rental": [372.73, 366.26, 364.65, 358.81, 352.73],
})
col_a, col_b = st.columns(2)
with col_a:
    st.dataframe(data_jam_kerja.style.format({"Avg Rental": "{:.1f}"}), use_container_width=True, hide_index=True)
with col_b:
    st.dataframe(data_jam_libur.style.format({"Avg Rental": "{:.1f}"}), use_container_width=True, hide_index=True)

# Tabel kategori waktu
st.markdown("**Rata-rata Rental per Kategori Waktu**")
time_cat = pd.DataFrame({
    "Kategori Waktu": ["Malam/Dini Hari (20-04)", "Pagi (05-09)", "Siang (10-14)", "Sore (15-19)"],
    "Libur/Akhir Pekan": [85.4, 70.2, 335.0, 309.7],
    "Hari Kerja": [83.0, 227.4, 175.3, 372.1],
})
st.dataframe(time_cat.style.format({"Libur/Akhir Pekan": "{:.1f}", "Hari Kerja": "{:.1f}"}),
             use_container_width=True, hide_index=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 4.  HEATMAP JAM × HARI
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("🗓️ Heatmap Rata-rata Rental per Jam dan Hari")

img_path2 = os.path.join(VIZ_DIR, "viz2_heatmap.png")
if os.path.exists(img_path2):
    st.image(img_path2, use_container_width=True)

# Statistik rata-rata per jam (dari images)
st.markdown("**Statistik Rata-rata Rental per Jam (min / mean / max across days)**")
stat_jam = pd.DataFrame({
    "Jam": list(range(24)),
    "Min": [27.6,12.5,6.8,4.2,5.0,8.3,14.5,33.1,83.9,156.5,160.4,175.6,
            168.4,168.4,181.3,273.0,318.8,272.6,225.5,168.0,127.6,94.1,61.9,27.6],
    "Mean": [53.7,33.2,22.7,11.4,6.3,19.8,76.2,212.9,360.2,219.5,195.0,221.3,
             240.5,250.8,311.8,461.8,425.8,311.7,226.2,172.4,131.4,87.9,53.7,33.2],
    "Max": [94.3,77.4,61.6,31.1,9.4,25.9,107.8,304.7,488.6,259.0,247.0,295.2,
            381.3,382.4,366.1,544.3,517.6,358.5,268.9,197.9,147.2,115.9,94.3,77.4],
})
st.dataframe(stat_jam.style.format({"Min": "{:.1f}", "Mean": "{:.1f}", "Max": "{:.1f}"}),
             use_container_width=True, hide_index=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 5.  MUSIM
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("🍂 Pengaruh Musim terhadap Rental Sepeda")

season_stats = (
    df.groupby("season_label")["cnt"]
    .agg(Rata_rata="mean", Median="median", N_Observasi="count")
    .reset_index()
    .rename(columns={"season_label": "Musim", "Rata_rata": "Rata-rata", "N_Observasi": "N Observasi"})
    .sort_values("Rata-rata", ascending=False)
)

season_order = season_stats["Musim"].tolist()
season_colors = {"Fall": "#E53935", "Summer": "#FB8C00", "Winter": "#1E88E5", "Spring": "#43A047"}
colors = [season_colors.get(s, "#90A4AE") for s in season_order]

fig, ax = plt.subplots(figsize=(10, 5))
bars = ax.bar(season_stats["Musim"], season_stats["Rata-rata"], color=colors, edgecolor="white", linewidth=1.5)
for bar, val in zip(bars, season_stats["Rata-rata"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 50,
            f"{int(val):,}", ha="center", va="bottom", fontsize=12, fontweight="bold")
ax.set_xlabel("Musim")
ax.set_ylabel("Rata-rata Rental Harian")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.set_title("Pengaruh Musim terhadap Rata-rata Rental Sepeda Harian")
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.markdown("**Statistik Rental per Musim**")
display_season = season_stats.copy()
display_season["Rata-rata"] = display_season["Rata-rata"].apply(lambda x: f"{x:.1f}")
display_season["Median"] = display_season["Median"].apply(lambda x: f"{x:.1f}")
st.dataframe(display_season, use_container_width=True, hide_index=True)

# Kombinasi musim × cuaca
st.markdown("**Rata-rata Rental: Kombinasi Musim × Cuaca**")
combo = df.pivot_table(values="cnt", index="season_label", columns="weather_label", aggfunc="mean")
combo = combo.reindex(["Spring", "Summer", "Fall", "Winter"])
combo_display = combo.applymap(lambda x: f"{x:.0f}" if pd.notna(x) else "-")
combo_display.index.name = "Musim"
st.dataframe(combo_display, use_container_width=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 6.  CUACA
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("🌤️ Pengaruh Kondisi Cuaca terhadap Rental Sepeda")

weather_stats = (
    df.groupby("weather_label")["cnt"]
    .agg(Rata_rata="mean", Median="median", N_Observasi="count")
    .reset_index()
    .rename(columns={"weather_label": "Cuaca", "Rata_rata": "Rata-rata", "N_Observasi": "N Observasi"})
    .sort_values("Rata-rata", ascending=False)
)
baseline = weather_stats[weather_stats["Cuaca"] == "Clear"]["Rata-rata"].values[0]
weather_stats["Penurunan vs Clear (%)"] = ((weather_stats["Rata-rata"] - baseline) / baseline * 100).round(1)

weather_colors = {"Clear": "#1E88E5", "Mist": "#64B5F6", "Light Rain/Snow": "#FB8C00"}
wcolors = [weather_colors.get(w, "#90A4AE") for w in weather_stats["Cuaca"]]

fig, ax = plt.subplots(figsize=(9, 5))
bars = ax.bar(weather_stats["Cuaca"], weather_stats["Rata-rata"], color=wcolors, edgecolor="white", linewidth=1.5)
for bar, (_, row) in zip(bars, weather_stats.iterrows()):
    pct = row["Penurunan vs Clear (%)"]
    val = row["Rata-rata"]
    label = f"{int(val):,}\n({pct:.1f}%)" if row["Cuaca"] != "Clear" else f"{int(val):,}\n(Baseline)"
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 50,
            label, ha="center", va="bottom", fontsize=11, fontweight="bold")
ax.set_xlabel("Kondisi Cuaca")
ax.set_ylabel("Rata-rata Rental Harian")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.set_title("Pengaruh Kondisi Cuaca terhadap Rata-rata Rental Sepeda Harian")
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.markdown("**Statistik Rental per Kondisi Cuaca**")
display_weather = weather_stats.copy()
display_weather["Rata-rata"] = display_weather["Rata-rata"].apply(lambda x: f"{x:.1f}")
display_weather["Median"] = display_weather["Median"].apply(lambda x: f"{x:.1f}")
display_weather["Penurunan vs Clear (%)"] = display_weather["Penurunan vs Clear (%)"].apply(lambda x: f"{x:.1f}%")
st.dataframe(display_weather, use_container_width=True, hide_index=True)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 7.  HARI KERJA vs LIBUR
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("📆 Hari Kerja vs Akhir Pekan/Libur")

wd_stats = (
    df.groupby("workingday")["cnt"]
    .agg(Rata_rata="mean", Median="median", N_Observasi="count")
    .reset_index()
)
wd_stats["Tipe Hari"] = wd_stats["workingday"].map({0: "Akhir Pekan/Libur", 1: "Hari Kerja"})

fig, ax = plt.subplots(figsize=(7, 4))
bars = ax.bar(wd_stats["Tipe Hari"], wd_stats["Rata_rata"],
              color=["#FB8C00", "#1E88E5"], edgecolor="white", linewidth=1.5, width=0.5)
for bar, val in zip(bars, wd_stats["Rata_rata"]):
    ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 30,
            f"{int(val):,}", ha="center", va="bottom", fontsize=13, fontweight="bold")
ax.set_ylabel("Rata-rata Rental Harian")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.set_title("Rata-rata Rental: Hari Kerja vs Akhir Pekan/Libur")
fig.tight_layout()
col_wd, _ = st.columns([1, 1])
with col_wd:
    st.pyplot(fig)
plt.close(fig)

st.markdown("---")

# ═══════════════════════════════════════════════════════════════════════════════
# 8.  DISTRIBUSI CASUAL vs REGISTERED
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader("👥 Casual vs Registered Users")

user_totals = {"Casual": df["casual"].sum(), "Registered": df["registered"].sum()}
fig, axes = plt.subplots(1, 2, figsize=(13, 5))

# Pie
axes[0].pie(
    user_totals.values(),
    labels=user_totals.keys(),
    autopct="%1.1f%%",
    colors=["#FB8C00", "#1E88E5"],
    startangle=140,
    wedgeprops={"edgecolor": "white", "linewidth": 2},
    textprops={"fontsize": 13},
)
axes[0].set_title("Proporsi Casual vs Registered")

# Bar per bulan
monthly_users = (
    df.groupby(["yr", "mnth"])[["casual", "registered"]]
    .mean()
    .reset_index()
)
monthly_users["yr_label"] = monthly_users["yr"].map({0: 2011, 1: 2012})
monthly_users["label"] = monthly_users.apply(
    lambda r: f"{month_names[int(r['mnth'])-1]} {int(r['yr_label'])}", axis=1
)
x = range(len(monthly_users))
width = 0.4
axes[1].bar([i - width/2 for i in x], monthly_users["casual"], width, label="Casual", color="#FB8C00")
axes[1].bar([i + width/2 for i in x], monthly_users["registered"], width, label="Registered", color="#1E88E5")
axes[1].set_xticks(list(x)[::3])
axes[1].set_xticklabels(monthly_users["label"].tolist()[::3], rotation=30, ha="right", fontsize=8)
axes[1].set_ylabel("Rata-rata Rental per Bulan")
axes[1].yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
axes[1].set_title("Rata-rata Casual vs Registered per Bulan")
axes[1].legend()

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

user_summary = pd.DataFrame({
    "Tipe User": ["Casual", "Registered"],
    "Total Rental": [df["casual"].sum(), df["registered"].sum()],
    "Rata-rata Harian": [df["casual"].mean(), df["registered"].mean()],
})
user_summary["Total Rental"] = user_summary["Total Rental"].apply(lambda x: f"{int(x):,}")
user_summary["Rata-rata Harian"] = user_summary["Rata-rata Harian"].apply(lambda x: f"{x:.1f}")
st.dataframe(user_summary, use_container_width=True, hide_index=True)

st.markdown("---")
st.caption("© Bike Sharing Dataset Analysis · Washington D.C. 2011–2012")
