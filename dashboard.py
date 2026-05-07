import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import streamlit as st
import plotly.express as px

sns.set_style("whitegrid")
plt.rcParams["figure.facecolor"] = "#f9f9f9"

st.set_page_config(
    page_title="Bike Sharing Dashboard",
    page_icon="🚲",
    layout="wide",
)

@st.cache_data
def load_data():
    df = pd.read_csv("main_data.csv")
    df["dteday"] = pd.to_datetime(df["dteday"])
    df["year"] = df["yr"].map({0: 2011, 1: 2012})
    df["workingday_label"] = df["workingday"].map({
        0: "Akhir Pekan/Libur",
        1: "Hari Kerja"
    })
    df.sort_values("dteday", inplace=True)
    df.reset_index(drop=True, inplace=True)
    return df

df_full = load_data()

# =========================
# Sidebar Filter
# =========================
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

    tipe_hari = st.selectbox(
        "Pilih Tipe Hari",
        ["Semua", "Hari Kerja", "Akhir Pekan/Libur"]
    )

    st.markdown("---")
    st.caption("Gunakan filter untuk eksplorasi data.")

if len(date_range) == 2:
    start_date, end_date = date_range
else:
    start_date, end_date = min_date, max_date

df = df_full[
    (df_full["dteday"] >= pd.Timestamp(start_date)) &
    (df_full["dteday"] <= pd.Timestamp(end_date))
].copy()

if tipe_hari == "Hari Kerja":
    df = df[df["workingday"] == 1]
elif tipe_hari == "Akhir Pekan/Libur":
    df = df[df["workingday"] == 0]

# =========================
# Header
# =========================
st.title("🚲 Bike Sharing Analysis Dashboard")
st.markdown("Washington D.C. · 2011–2012")
st.markdown("---")

# =========================
# KPI
# =========================
col1, col2, col3, col4 = st.columns(4)

col1.metric("Total Hari", f"{len(df):,}")
col2.metric("Total Rental", f"{df['cnt'].sum():,}")
col3.metric("Rata-rata Harian", f"{df['cnt'].mean():,.0f}")
col4.metric("Maks. Rental/Hari", f"{df['cnt'].max():,}")

st.markdown("---")

@st.cache_data
def load_hour_data():
    df2 = pd.read_csv("hour.csv")
    df2["dteday"] = pd.to_datetime(df2["dteday"])

    df2["workingday_label"] = df2["workingday"].map({
        0: "Akhir Pekan/Libur",
        1: "Hari Kerja"
    })

    df2["weekday_label"] = df2["weekday"].map({
        0: "Sun", 1: "Mon", 2: "Tue", 3: "Wed",
        4: "Thu", 5: "Fri", 6: "Sat"
    })

    df2.sort_values("dteday", inplace=True)
    df2.reset_index(drop=True, inplace=True)

    return df2

df_full = load_data()
df2_full = load_hour_data()
df2 = df2_full[
    (df2_full["dteday"] >= pd.Timestamp(start_date)) &
    (df2_full["dteday"] <= pd.Timestamp(end_date))
].copy()

if tipe_hari == "Hari Kerja":
    df2 = df2[df2["workingday"] == 1]
elif tipe_hari == "Akhir Pekan/Libur":
    df2 = df2[df2["workingday"] == 0]
    
# =========================
# Pertanyaan Bisnis 1
# =========================

st.subheader(
    "📌 Pertanyaan Bisnis 1: Bagaimana pola rata-rata jumlah rental sepeda per jam "
    "antara hari kerja dan hari libur/akhir pekan?"
)

hourly = (
    df2.groupby(["hr", "workingday_label"])["cnt"]
    .mean()
    .reset_index()
    .rename(columns={"cnt": "avg_cnt"})
)

wd = hourly[hourly["workingday_label"] == "Hari Kerja"]
wk = hourly[hourly["workingday_label"] == "Akhir Pekan/Libur"]

fig, ax = plt.subplots(figsize=(13, 5))

ax.plot(wd["hr"], wd["avg_cnt"], marker="o", linewidth=2.5, label="Hari Kerja")
ax.plot(wk["hr"], wk["avg_cnt"], marker="s", linewidth=2.5, label="Akhir Pekan/Libur")

ax.set_xlabel("Jam (0–23)")
ax.set_ylabel("Rata-rata Jumlah Rental")
ax.set_title("Pola Rata-rata Rental Sepeda Per Jam: Hari Kerja vs Akhir Pekan/Libur")
ax.set_xticks(range(0, 24))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))
ax.legend()
ax.grid(axis="y", alpha=0.35, linestyle="--")

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.dataframe(hourly, use_container_width=True, hide_index=True)
st.markdown("---")

# =========================
# Visualisasi Tambahan Q1
# =========================
st.subheader("📊 Rata-rata Rental Berdasarkan Hari dalam Seminggu")

weekday_order = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

weekday_stats = (
    df.groupby("weekday_label")["cnt"]
    .mean()
    .reindex(weekday_order)
    .reset_index()
    .rename(columns={
        "weekday_label": "Hari",
        "cnt": "Rata-rata Rental"
    })
)

fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(
    data=weekday_stats,
    x="Hari",
    y="Rata-rata Rental",
    ax=ax
)

ax.set_xlabel("Hari")
ax.set_ylabel("Rata-rata Rental Harian")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.dataframe(weekday_stats, use_container_width=True, hide_index=True)

st.markdown("---")

# =========================
# Pertanyaan Bisnis 2
# =========================
st.subheader(
    "📌 Pertanyaan Bisnis 2: Pengaruh Cuaca dan Musim terhadap Rata-rata Rental Harian?"
)

season_stats = (
    df.groupby("season_label")["cnt"]
    .agg(["mean", "median", "sum", "count"])
    .rename(columns={
        "mean": "Rata-rata Rental",
        "median": "Median Rental",
        "sum": "Total Rental",
        "count": "Jumlah Hari"
    })
    .sort_values("Rata-rata Rental", ascending=False)
    .reset_index()
)

fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(
    data=season_stats,
    x="season_label",
    y="Rata-rata Rental",
    ax=ax
)

ax.set_xlabel("Musim")
ax.set_ylabel("Rata-rata Rental Harian")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.dataframe(season_stats, use_container_width=True, hide_index=True)

st.markdown("---")

# =========================
# Visualisasi Cuaca
# =========================
st.subheader("🌤️ Rata-rata Rental Berdasarkan Kondisi Cuaca")

weather_stats = (
    df.groupby("weather_label")["cnt"]
    .agg(["mean", "median", "sum", "count"])
    .rename(columns={
        "mean": "Rata-rata Rental",
        "median": "Median Rental",
        "sum": "Total Rental",
        "count": "Jumlah Hari"
    })
    .sort_values("Rata-rata Rental", ascending=False)
    .reset_index()
)

fig, ax = plt.subplots(figsize=(10, 5))
sns.barplot(
    data=weather_stats,
    x="weather_label",
    y="Rata-rata Rental",
    ax=ax
)

ax.set_xlabel("Kondisi Cuaca")
ax.set_ylabel("Rata-rata Rental Harian")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.dataframe(weather_stats, use_container_width=True, hide_index=True)

st.markdown("---")



# =========================
# Cuaca dan Musim
# =========================

st.subheader(
    "📌 Kombinasi Cuaca dan Musim Terhadap Rata-Rata Rental Harian"
)

combo_stats = (
    df.groupby(["season_label", "weather_label"])["cnt"]
    .mean()
    .reset_index()
    .rename(columns={"cnt": "Rata-rata Rental Harian"})
)

season_order = ["Spring", "Summer", "Fall", "Winter"]
weather_order = ["Clear", "Mist", "Light Rain/Snow"]

combo_pivot = combo_stats.pivot(
    index="season_label",
    columns="weather_label",
    values="Rata-rata Rental Harian"
).reindex(index=season_order, columns=weather_order)

fig = px.imshow(
    combo_pivot,
    text_auto=".0f",
    aspect="auto",
    color_continuous_scale="YlOrRd",
    labels=dict(
        x="Kondisi Cuaca",
        y="Musim",
        color="Rata-rata Rental"
    ),
    title="Rata-rata Total Rental Harian Berdasarkan Kombinasi Musim dan Cuaca"
)

fig.update_layout(
    xaxis_title="Kondisi Cuaca",
    yaxis_title="Musim"
)

st.plotly_chart(fig, use_container_width=True)

combo_table = combo_stats.copy()
baseline = combo_table["Rata-rata Rental Harian"].max()

combo_table["Penurunan vs Tertinggi (%)"] = (
    (combo_table["Rata-rata Rental Harian"] - baseline) / baseline * 100
).round(1)

combo_table = combo_table.sort_values("Penurunan vs Tertinggi (%)")

st.markdown("**Kombinasi Cuaca–Musim dengan Penurunan Permintaan Terbesar**")

st.dataframe(
    combo_table.rename(columns={
        "season_label": "Musim",
        "weather_label": "Cuaca"
    }),
    use_container_width=True,
    hide_index=True
)

# =========================
# Tren Harian
# =========================
st.subheader("📈 Tren Rental Harian")

fig, ax = plt.subplots(figsize=(16, 4))
ax.plot(df["dteday"], df["cnt"], linewidth=1.5)

ax.set_xlabel("Tanggal")
ax.set_ylabel("Jumlah Rental")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.markdown("---")

# =========================
# Tren Bulanan
# =========================
st.subheader("📅 Rata-rata Rental Bulanan per Tahun")

monthly_avg = (
    df.groupby(["year", "mnth"])["cnt"]
    .mean()
    .reset_index()
)

month_names = [
    "Jan", "Feb", "Mar", "Apr", "Mei", "Jun",
    "Jul", "Agu", "Sep", "Okt", "Nov", "Des"
]

monthly_avg["Bulan"] = monthly_avg["mnth"].apply(lambda x: month_names[x - 1])

fig, ax = plt.subplots(figsize=(14, 5))
sns.lineplot(
    data=monthly_avg,
    x="Bulan",
    y="cnt",
    hue="year",
    marker="o",
    ax=ax
)

ax.set_xlabel("Bulan")
ax.set_ylabel("Rata-rata Rental Harian")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

yearly_stats = (
    df.groupby("year")["cnt"]
    .agg(["sum", "mean", "median", "max"])
    .rename(columns={
        "sum": "Total Rental",
        "mean": "Rata-rata Rental",
        "median": "Median Rental",
        "max": "Maksimum Rental"
    })
    .reset_index()
)

st.dataframe(yearly_stats, use_container_width=True, hide_index=True)

st.markdown("---")

# =========================
# Casual vs Registered
# =========================
st.subheader("👥 Total Rental Berdasarkan Tipe Pengguna")

user_total = pd.DataFrame({
    "Tipe User": ["Casual", "Registered"],
    "Total Rental": [df["casual"].sum(), df["registered"].sum()],
    "Rata-rata Harian": [df["casual"].mean(), df["registered"].mean()]
})

fig, ax = plt.subplots(figsize=(8, 5))
sns.barplot(
    data=user_total,
    x="Tipe User",
    y="Total Rental",
    ax=ax
)

ax.set_xlabel("Tipe User")
ax.set_ylabel("Total Rental")
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{int(x):,}"))

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.dataframe(user_total, use_container_width=True, hide_index=True)

st.markdown("---")

# =========================
# Korelasi
# =========================
st.subheader("🌡️ Korelasi Variabel Numerik")

corr_cols = [
    "temp",
    "atemp",
    "hum",
    "windspeed",
    "casual",
    "registered",
    "cnt"
]

corr = df[corr_cols].corr()

fig, ax = plt.subplots(figsize=(10, 6))
sns.heatmap(
    corr,
    annot=True,
    fmt=".2f",
    cmap="coolwarm",
    ax=ax
)

fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

st.caption("© Bike Sharing Dataset Analysis")
