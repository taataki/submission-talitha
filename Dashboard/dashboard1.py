# Rewrite the entire dashboard.py with corrected URLs
cat > /home/claude/submission/dashboard/dashboard.py << 'PYEOF'
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import warnings

warnings.filterwarnings("ignore")

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Bike Sharing Dashboard",
    page_icon="🚲",
    layout="wide",
)

# ── Load data ─────────────────────────────────────────────────────────────────
@st.cache_data
def load_data():
    # main_data.csv sudah berisi hasil cleaning lengkap (termasuk season_label & weather_label)
    main_url = "https://raw.githubusercontent.com/taataki/submission-talitha/5ab5f584657db5df3109d25834a4719aa89c723a/Dashboard/main_data.csv"
    df = pd.read_csv(main_url)
    df["dteday"] = pd.to_datetime(df["dteday"])

    # hour.csv dari folder Dataset untuk analisis pola per jam
    hour_url = "https://raw.githubusercontent.com/taataki/submission-talitha/5ab5f584657db5df3109d25834a4719aa89c723a/Dataset/hour.csv"
    df_hour = pd.read_csv(hour_url)
    df_hour["dteday"] = pd.to_datetime(df_hour["dteday"])

    # Tambahkan label pada df_hour (tidak ada di file aslinya)
    season_map  = {1: "Spring", 2: "Summer", 3: "Fall", 4: "Winter"}
    weather_map = {1: "Clear", 2: "Mist", 3: "Light Rain/Snow", 4: "Heavy Rain"}
    df_hour["season_label"]  = df_hour["season"].map(season_map)
    df_hour["weather_label"] = df_hour["weathersit"].map(weather_map)

    def kategorikan_jam(hr):
        if   5  <= hr <= 9:  return "Pagi (05–09)"
        elif 10 <= hr <= 14: return "Siang (10–14)"
        elif 15 <= hr <= 19: return "Sore (15–19)"
        else:                return "Malam/Dini Hari (20–04)"

    df_hour["time_cat"] = df_hour["hr"].apply(kategorikan_jam)

    return df, df_hour

df_day, df_hour = load_data()

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🚲 Bike Sharing Dashboard")
st.markdown("**Analisis Data Bike Sharing Washington D.C. — Periode 2011–2012**")
st.markdown("---")

# ── Sidebar filter (date range) ───────────────────────────────────────────────
st.sidebar.header("🔍 Filter Data")
min_date = df_day["dteday"].min().date()
max_date = df_day["dteday"].max().date()

date_range = st.sidebar.date_input(
    "Rentang Tanggal",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date,
)

if len(date_range) == 2:
    start_date, end_date = date_range
    df_filtered = df_day[
        (df_day["dteday"].dt.date >= start_date) &
        (df_day["dteday"].dt.date <= end_date)
    ]
else:
    df_filtered = df_day.copy()

# ── KPI Metrics ───────────────────────────────────────────────────────────────
st.subheader("📊 Ringkasan Metrik")

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_rentals = df_filtered["cnt"].sum()
    st.metric("Total Rental", f"{total_rentals:,.0f}")

with col2:
    avg_daily = df_filtered["cnt"].mean()
    st.metric("Rata-rata Rental/Hari", f"{avg_daily:,.0f}")

with col3:
    total_casual = df_filtered["casual"].sum()
    st.metric("Total Pengguna Kasual", f"{total_casual:,.0f}")

with col4:
    total_registered = df_filtered["registered"].sum()
    st.metric("Total Pengguna Terdaftar", f"{total_registered:,.0f}")

st.markdown("---")

# ── Section 1: Pertanyaan Bisnis 1 ───────────────────────────────────────────
st.subheader("❓ Pertanyaan Bisnis 1")
st.markdown(
    "**Bagaimana pola rata-rata jumlah rental sepeda per jam antara hari kerja "
    "dan hari libur/akhir pekan, dan pada rentang jam berapakah permintaan "
    "tertinggi terjadi di masing-masing kelompok hari tersebut?**"
)

# Viz 1 — Line chart pola per jam
hourly = (
    df_hour
    .groupby(["hr", "workingday"])["cnt"]
    .mean()
    .reset_index()
    .rename(columns={"cnt": "avg_cnt"})
)
wd = hourly[hourly["workingday"] == 1]
wk = hourly[hourly["workingday"] == 0]

fig1, ax1 = plt.subplots(figsize=(10, 4))
ax1.plot(wd["hr"], wd["avg_cnt"], marker="o", markersize=4, linewidth=2,
         color="#1565C0", label="Hari Kerja")
ax1.plot(wk["hr"], wk["avg_cnt"], marker="s", markersize=4, linewidth=2,
         color="#E53935", label="Libur / Akhir Pekan", linestyle="--")

ax1.set_xticks(range(0, 24))
ax1.set_xlabel("Jam (0–23)", fontsize=11)
ax1.set_ylabel("Rata-rata Jumlah Rental", fontsize=11)
ax1.set_title("Pola Rata-rata Rental Sepeda per Jam:\nHari Kerja vs Libur/Akhir Pekan (2011–2012)",
              fontsize=13, fontweight="bold")
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax1.legend(fontsize=10)
ax1.grid(axis="y", alpha=0.35, linestyle="--")
ax1.set_facecolor("#f8f9fa")
fig1.patch.set_facecolor("white")
plt.tight_layout()
st.pyplot(fig1)
plt.close(fig1)

st.info(
    "📌 **Insight:** Hari kerja menunjukkan pola **bimodal** dengan puncak pada jam 08:00 "
    "(commute pagi) dan jam 17:00–18:00 (commute sore). Hari libur/akhir pekan "
    "menunjukkan pola **unimodal** dengan puncak di siang hari (jam 12:00–14:00), "
    "mencerminkan aktivitas rekreasi."
)

# Viz 2 — Heatmap per jam & hari
st.markdown("#### Heatmap Rental per Jam dan Hari dalam Seminggu")

pivot_heatmap = (
    df_hour
    .groupby(["weekday", "hr"])["cnt"]
    .mean()
    .unstack()
)
pivot_heatmap.index = ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]

fig2, ax2 = plt.subplots(figsize=(14, 4))
sns.heatmap(
    pivot_heatmap,
    ax=ax2,
    cmap="YlOrRd",
    linewidths=0.3,
    linecolor="white",
    fmt=".0f",
    annot=True,
    annot_kws={"size": 6},
)
ax2.set_title(
    "Heatmap Rata-rata Rental Sepeda per Jam dan Hari dalam Seminggu (2011–2012)",
    fontsize=13, fontweight="bold", pad=10,
)
ax2.set_xlabel("Jam (0–23)", fontsize=11)
ax2.set_ylabel("Hari", fontsize=11)
plt.tight_layout()
st.pyplot(fig2)
plt.close(fig2)

st.info(
    "📌 **Insight:** Sel paling gelap konsisten pada hari Senin–Jumat jam 08:00 dan "
    "17:00–18:00. Sabtu–Minggu memiliki pola warna lebih merata di siang hari, "
    "tanpa pola bimodal yang terlihat pada hari kerja."
)

st.markdown("---")

# ── Section 2: Pertanyaan Bisnis 2 ───────────────────────────────────────────
st.subheader("❓ Pertanyaan Bisnis 2")
st.markdown(
    "**Seberapa besar pengaruh kondisi cuaca dan musim terhadap rata-rata total "
    "rental harian, serta kombinasi cuaca–musim manakah yang menghasilkan "
    "penurunan permintaan terbesar?**"
)

col_a, col_b = st.columns(2)

# Viz 3 — Bar chart musim
with col_a:
    st.markdown("#### Pengaruh Musim terhadap Rental Harian")
    season_order = ["Spring", "Summer", "Fall", "Winter"]
    avg_season = df_filtered.groupby("season_label")["cnt"].mean().reindex(season_order).dropna()

    colors_season = ["#4CAF50", "#FF9800", "#F44336", "#2196F3"]
    fig3, ax3 = plt.subplots(figsize=(6, 4))
    bars3 = ax3.bar(avg_season.index, avg_season.values,
                    color=colors_season[:len(avg_season)],
                    edgecolor="white", linewidth=1.2, width=0.6)
    for bar, val in zip(bars3, avg_season.values):
        ax3.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 30,
                 f"{val:,.0f}", ha="center", va="bottom", fontsize=10, fontweight="bold")
    ax3.set_xlabel("Musim", fontsize=11)
    ax3.set_ylabel("Rata-rata Rental Harian", fontsize=11)
    ax3.set_title("Pengaruh Musim terhadap\nRata-rata Rental Harian", fontsize=12, fontweight="bold")
    ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax3.set_facecolor("#f8f9fa")
    fig3.patch.set_facecolor("white")
    ax3.grid(axis="y", alpha=0.35, linestyle="--")
    plt.tight_layout()
    st.pyplot(fig3)
    plt.close(fig3)

# Viz 4 — Bar chart cuaca
with col_b:
    st.markdown("#### Pengaruh Kondisi Cuaca terhadap Rental Harian")
    weather_order = ["Clear", "Mist", "Light Rain/Snow"]
    avg_weather = df_filtered.groupby("weather_label")["cnt"].mean()
    avg_weather_ord = avg_weather.reindex([w for w in weather_order if w in avg_weather.index])

    palette = {"Clear": "#2196F3", "Mist": "#90CAF9", "Light Rain/Snow": "#FF9800", "Heavy Rain": "#F44336"}
    clrs4 = [palette.get(w, "gray") for w in avg_weather_ord.index]
    base = avg_weather_ord.get("Clear", 1)
    pct_drop = [(v - base) / base * 100 for v in avg_weather_ord.values]

    fig4, ax4 = plt.subplots(figsize=(6, 4))
    bars4 = ax4.bar(avg_weather_ord.index, avg_weather_ord.values,
                    color=clrs4, edgecolor="white", linewidth=1.2, width=0.5)
    for bar, val, pct in zip(bars4, avg_weather_ord.values, pct_drop):
        pct_str = f"{pct:.1f}%" if pct != 0 else "Baseline"
        ax4.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 30,
                 f"{val:,.0f}\n({pct_str})", ha="center", va="bottom", fontsize=9, fontweight="bold")
    ax4.set_xlabel("Kondisi Cuaca", fontsize=11)
    ax4.set_ylabel("Rata-rata Rental Harian", fontsize=11)
    ax4.set_title("Pengaruh Kondisi Cuaca terhadap\nRata-rata Rental Harian", fontsize=12, fontweight="bold")
    ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
    ax4.set_facecolor("#f8f9fa")
    fig4.patch.set_facecolor("white")
    ax4.grid(axis="y", alpha=0.35, linestyle="--")
    plt.tight_layout()
    st.pyplot(fig4)
    plt.close(fig4)

st.info(
    "📌 **Insight:** Musim **Fall** menghasilkan rata-rata rental tertinggi; musim **Spring** terendah. "
    "Kondisi **Light Rain/Snow** menyebabkan penurunan >60% dibanding cuaca **Clear**. "
    "Kombinasi terburuk: **Spring + Light Rain/Snow**; terbaik: **Fall + Clear**."
)

st.markdown("---")

# ── Section 3: Tren YoY ──────────────────────────────────────────────────────
st.subheader("📈 Tren Rental Bulanan: 2011 vs 2012")

yoy = (
    df_day
    .groupby(["yr", "mnth"])["cnt"]
    .mean()
    .reset_index()
)
bulan_label = ["Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
               "Jul", "Agu", "Sep", "Okt", "Nov", "Des"]

fig5, ax5 = plt.subplots(figsize=(12, 4))
for yr_val, label, clr, mrkr in [(0, "2011", "#1565C0", "o"), (1, "2012", "#E53935", "s")]:
    subset = yoy[yoy["yr"] == yr_val]
    ax5.plot(subset["mnth"], subset["cnt"],
             marker=mrkr, linewidth=2.5, markersize=6, color=clr, label=label)

ax5.set_xticks(range(1, 13))
ax5.set_xticklabels(bulan_label)
ax5.set_xlabel("Bulan", fontsize=11)
ax5.set_ylabel("Rata-rata Rental Harian", fontsize=11)
ax5.set_title("Tren Rata-rata Rental Bulanan: 2011 vs 2012", fontsize=13, fontweight="bold")
ax5.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:,.0f}"))
ax5.legend(title="Tahun", fontsize=11)
ax5.grid(axis="y", alpha=0.35, linestyle="--")
ax5.set_facecolor("#f8f9fa")
fig5.patch.set_facecolor("white")
plt.tight_layout()
st.pyplot(fig5)
plt.close(fig5)

st.info(
    "📌 **Insight:** Kurva 2012 secara konsisten berada di atas 2011 pada hampir seluruh bulan, "
    "menunjukkan pertumbuhan basis pengguna yang signifikan. Kedua tahun mengikuti pola musiman "
    "yang serupa: meningkat menuju musim panas dan menurun di akhir tahun."
)

st.markdown("---")

# ── Footer ────────────────────────────────────────────────────────────────────
st.caption("Dashboard dibuat oleh Talitha Widyadhana | Dicoding — Analisis Data dengan Python")
PYEOF
echo "Done"