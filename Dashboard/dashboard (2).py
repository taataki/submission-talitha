import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import streamlit as st

sns.set(style='dark')

# ── Helper functions ──────────────────────────────────────────────────────────

def create_hourly_pattern_df(df_hour):
    """Rata-rata rental per jam dikelompokkan berdasarkan workingday."""
    hourly = (
        df_hour
        .groupby(['hr', 'workingday'])['cnt']
        .mean()
        .reset_index()
        .rename(columns={'cnt': 'avg_cnt'})
    )
    wd = hourly[hourly['workingday'] == 1].copy()
    wk = hourly[hourly['workingday'] == 0].copy()
    return wd, wk


def create_season_df(df):
    """Rata-rata rental harian per musim."""
    season_order = ['Spring', 'Summer', 'Fall', 'Winter']
    avg_season = (
        df.groupby('season_label')['cnt']
        .mean()
        .reindex(season_order)
        .reset_index()
        .rename(columns={'cnt': 'avg_cnt'})
    )
    return avg_season


def create_weather_df(df):
    """Rata-rata rental harian per kondisi cuaca."""
    weather_order = ['Clear', 'Mist', 'Light Rain/Snow']
    avg_weather = (
        df.groupby('weather_label')['cnt']
        .mean()
        .reindex([w for w in weather_order if w in df['weather_label'].unique()])
        .reset_index()
        .rename(columns={'cnt': 'avg_cnt'})
    )
    base = avg_weather.loc[avg_weather['weather_label'] == 'Clear', 'avg_cnt'].values[0]
    avg_weather['pct_drop'] = ((avg_weather['avg_cnt'] - base) / base * 100).round(1)
    return avg_weather


def create_yoy_df(df):
    """Rata-rata rental bulanan per tahun (YoY)."""
    yoy = (
        df.groupby(['yr', 'mnth'])['cnt']
        .mean()
        .reset_index()
    )
    yoy['Tahun'] = yoy['yr'].map({0: '2011', 1: '2012'})
    return yoy


def create_heatmap_df(df_hour):
    """Pivot tabel rata-rata rental per jam dan hari."""
    pivot = (
        df_hour
        .groupby(['weekday', 'hr'])['cnt']
        .mean()
        .unstack()
    )
    pivot.index = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    return pivot


# ── Load data ──────────────────────────────────────────────────────────────────

BASE_URL = 'https://raw.githubusercontent.com/taataki/submission-talitha/main/dashboard/main_data.csv'
HOUR_URL = 'https://raw.githubusercontent.com/taataki/submission-talitha/main/Dataset/hour.csv'

@st.cache_data
def load_data():
    df_day = pd.read_csv(BASE_URL)
    df_day['dteday'] = pd.to_datetime(df_day['dteday'])

    df_hour = pd.read_csv(HOUR_URL)
    df_hour['dteday'] = pd.to_datetime(df_hour['dteday'])

    # Label mapping untuk hour dataset
    season_map  = {1: 'Spring', 2: 'Summer', 3: 'Fall', 4: 'Winter'}
    weather_map = {1: 'Clear', 2: 'Mist', 3: 'Light Rain/Snow', 4: 'Heavy Rain'}
    weekday_map = {0: 'Sun', 1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat'}
    for df in [df_day, df_hour]:
        df['season_label']  = df['season'].map(season_map)
        df['weather_label'] = df['weathersit'].map(weather_map)
        df['weekday_label'] = df['weekday'].map(weekday_map)

    return df_day, df_hour

df_day_clean, df_hour = load_data()

# ── Sidebar filter ─────────────────────────────────────────────────────────────

min_date = df_day_clean['dteday'].min()
max_date = df_day_clean['dteday'].max()

with st.sidebar:
    st.title("🚲 Bike Sharing")
    st.markdown("**Dashboard Analisis Data**")
    st.markdown("---")

    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )
    st.markdown("---")
    st.caption("Data: Capital Bikeshare, Washington D.C. (2011–2012)")

main_df = df_day_clean[
    (df_day_clean['dteday'] >= str(start_date)) &
    (df_day_clean['dteday'] <= str(end_date))
]

# Filter df_hour berdasarkan tanggal yang sama
main_hour = df_hour[
    (df_hour['dteday'] >= str(start_date)) &
    (df_hour['dteday'] <= str(end_date))
]

# ── Siapkan dataframes ─────────────────────────────────────────────────────────

wd_df, wk_df     = create_hourly_pattern_df(main_hour)
season_df        = create_season_df(main_df)
weather_df       = create_weather_df(main_df)
yoy_df           = create_yoy_df(main_df)
heatmap_pivot    = create_heatmap_df(main_hour)

# ── Header ─────────────────────────────────────────────────────────────────────

st.header('🚲 Bike Sharing Dashboard')
st.markdown("Analisis pola rental sepeda di Washington D.C., periode **2011–2012**.")

# ── Metric ringkasan ───────────────────────────────────────────────────────────

st.subheader('Ringkasan Statistik')

col1, col2, col3, col4 = st.columns(4)

with col1:
    total_rental = int(main_df['cnt'].sum())
    st.metric("Total Rental", value=f"{total_rental:,}")

with col2:
    avg_daily = int(main_df['cnt'].mean())
    st.metric("Rata-rata Harian", value=f"{avg_daily:,}")

with col3:
    total_registered = int(main_df['registered'].sum())
    st.metric("Total Registered", value=f"{total_registered:,}")

with col4:
    total_casual = int(main_df['casual'].sum())
    st.metric("Total Casual", value=f"{total_casual:,}")

st.markdown("---")

# ── Visualisasi 1: Pola rental per jam ────────────────────────────────────────

st.subheader('Pola Rata-rata Rental Per Jam: Hari Kerja vs Akhir Pekan/Libur')
st.markdown("Menjawab **Pertanyaan Bisnis 1** — Pada jam berapa permintaan tertinggi terjadi?")

fig, ax = plt.subplots(figsize=(13, 5))

ax.plot(wd_df['hr'], wd_df['avg_cnt'],
        color='steelblue', linewidth=2.5, marker='o', markersize=5, label='Hari Kerja')
ax.plot(wk_df['hr'], wk_df['avg_cnt'],
        color='coral', linewidth=2.5, marker='s', markersize=5, label='Akhir Pekan / Hari Libur')

ax.axvspan(7, 9,   alpha=0.10, color='steelblue')
ax.axvspan(16, 19, alpha=0.10, color='orange')

if len(wd_df[wd_df['hr'] == 8]) > 0:
    ax.annotate(
        'Peak Pagi\n(±08:00)',
        xy=(8, wd_df.loc[wd_df['hr'] == 8, 'avg_cnt'].values[0]),
        xytext=(8.5, wd_df['avg_cnt'].max() * 0.82),
        arrowprops=dict(arrowstyle='->', color='steelblue'),
        fontsize=9, color='steelblue'
    )
if len(wd_df[wd_df['hr'] == 17]) > 0:
    ax.annotate(
        'Peak Sore\n(±17:00)',
        xy=(17, wd_df.loc[wd_df['hr'] == 17, 'avg_cnt'].values[0]),
        xytext=(17.5, wd_df['avg_cnt'].max() * 0.95),
        arrowprops=dict(arrowstyle='->', color='darkorange'),
        fontsize=9, color='darkorange'
    )

ax.set_xlabel('Jam (0–23)', fontsize=12)
ax.set_ylabel('Rata-rata Jumlah Rental', fontsize=12)
ax.set_title(
    'Pola Rata-rata Rental Sepeda Per Jam:\nHari Kerja vs Akhir Pekan/Libur',
    fontsize=13, fontweight='bold'
)
ax.legend(fontsize=11)
ax.set_xticks(range(0, 24))
ax.grid(axis='y', alpha=0.35, linestyle='--')
ax.set_facecolor('#f8f9fa')
fig.patch.set_facecolor('white')
plt.tight_layout()
st.pyplot(fig)

st.caption(
    "💡 **Insight:** Hari kerja menunjukkan pola *bimodal* (puncak jam 08:00 & 17:00), "
    "mencerminkan aktivitas *commuting*. Hari libur menunjukkan pola *unimodal* dengan puncak siang hari (12:00–14:00), "
    "mencerminkan aktivitas rekreasi."
)

# ── Visualisasi 2: Heatmap per jam dan hari ───────────────────────────────────

st.subheader('Heatmap Rata-rata Rental Per Jam dan Hari dalam Seminggu')

fig2, ax2 = plt.subplots(figsize=(16, 5))
sns.heatmap(
    heatmap_pivot,
    cmap='YlOrRd',
    ax=ax2,
    linewidths=0.2,
    linecolor='white',
    cbar_kws={'label': 'Rata-rata Rental'},
    fmt='.0f',
    annot=True,
    annot_kws={'size': 7}
)
ax2.set_title(
    'Heatmap Rata-rata Rental Sepeda per Jam dan Hari dalam Seminggu',
    fontsize=13, fontweight='bold', pad=12
)
ax2.set_xlabel('Jam (0–23)', fontsize=12)
ax2.set_ylabel('Hari', fontsize=12)
plt.tight_layout()
st.pyplot(fig2)

st.caption(
    "💡 **Insight:** Sel paling gelap berada di perpotongan Senin–Jumat dengan jam 08:00 dan 17:00–18:00. "
    "Sabtu–Minggu menunjukkan distribusi permintaan yang lebih merata di siang hari."
)

st.markdown("---")

# ── Visualisasi 3 & 4: Pengaruh musim dan cuaca ───────────────────────────────

st.subheader('Pengaruh Musim & Kondisi Cuaca terhadap Rental Harian')
st.markdown("Menjawab **Pertanyaan Bisnis 2** — Faktor apa yang paling memengaruhi jumlah rental?")

col_left, col_right = st.columns(2)

with col_left:
    colors_season = ['#4CAF50', '#FF9800', '#F44336', '#2196F3']
    fig3, ax3 = plt.subplots(figsize=(7, 5))
    bars3 = ax3.bar(
        season_df['season_label'], season_df['avg_cnt'],
        color=colors_season, edgecolor='white', linewidth=1.2, width=0.6
    )
    for bar, val in zip(bars3, season_df['avg_cnt']):
        ax3.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 30,
            f'{val:,.0f}',
            ha='center', va='bottom', fontsize=11, fontweight='bold'
        )
    ax3.set_xlabel('Musim', fontsize=11)
    ax3.set_ylabel('Rata-rata Rental Harian', fontsize=11)
    ax3.set_title('Pengaruh Musim\nterhadap Rata-rata Rental', fontsize=12, fontweight='bold')
    ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax3.set_facecolor('#f8f9fa')
    fig3.patch.set_facecolor('white')
    ax3.grid(axis='y', alpha=0.35, linestyle='--')
    plt.tight_layout()
    st.pyplot(fig3)

with col_right:
    palette_weather = {'Clear': '#2196F3', 'Mist': '#90CAF9', 'Light Rain/Snow': '#FF9800'}
    clrs_w = [palette_weather.get(w, 'gray') for w in weather_df['weather_label']]
    fig4, ax4 = plt.subplots(figsize=(7, 5))
    bars4 = ax4.bar(
        weather_df['weather_label'], weather_df['avg_cnt'],
        color=clrs_w, edgecolor='white', linewidth=1.2, width=0.5
    )
    for bar, val, pct in zip(bars4, weather_df['avg_cnt'], weather_df['pct_drop']):
        pct_str = f'{pct:.1f}%' if pct != 0 else 'Baseline'
        ax4.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 30,
            f'{val:,.0f}\n({pct_str})',
            ha='center', va='bottom', fontsize=10, fontweight='bold'
        )
    ax4.set_xlabel('Kondisi Cuaca', fontsize=11)
    ax4.set_ylabel('Rata-rata Rental Harian', fontsize=11)
    ax4.set_title('Pengaruh Kondisi Cuaca\nterhadap Rata-rata Rental', fontsize=12, fontweight='bold')
    ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax4.set_facecolor('#f8f9fa')
    fig4.patch.set_facecolor('white')
    ax4.grid(axis='y', alpha=0.35, linestyle='--')
    plt.tight_layout()
    st.pyplot(fig4)

st.caption(
    "💡 **Insight Musim:** Fall (Gugur) menghasilkan rata-rata rental tertinggi; Spring (Semi) terendah. "
    "**Insight Cuaca:** Light Rain/Snow menyebabkan penurunan >60% dibanding kondisi Clear — "
    "cuaca buruk adalah hambatan paling kritis bagi permintaan rental."
)

st.markdown("---")

# ── Visualisasi 5: Tren YoY ────────────────────────────────────────────────────

st.subheader('Tren Rata-rata Rental Bulanan: 2011 vs 2012')

bulan_label = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']

fig5, ax5 = plt.subplots(figsize=(12, 5))
styles = [(0, '2011', '#1565C0', 'o'), (1, '2012', '#E53935', 's')]
for yr_val, label, clr, mrkr in styles:
    subset = yoy_df[yoy_df['yr'] == yr_val]
    if not subset.empty:
        ax5.plot(
            subset['mnth'], subset['cnt'],
            marker=mrkr, linewidth=2.5, markersize=6,
            color=clr, label=label
        )
ax5.set_xticks(range(1, 13))
ax5.set_xticklabels(bulan_label)
ax5.set_xlabel('Bulan', fontsize=12)
ax5.set_ylabel('Rata-rata Rental Harian', fontsize=12)
ax5.set_title('Tren Rata-rata Rental Bulanan: 2011 vs 2012', fontsize=13, fontweight='bold')
ax5.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
ax5.legend(title='Tahun', fontsize=11)
ax5.grid(axis='y', alpha=0.35, linestyle='--')
ax5.set_facecolor('#f8f9fa')
fig5.patch.set_facecolor('white')
plt.tight_layout()
st.pyplot(fig5)

st.caption(
    "💡 **Insight:** Kurva 2012 secara konsisten berada di atas 2011 sepanjang tahun, "
    "mengindikasikan pertumbuhan basis pengguna yang berkelanjutan. "
    "Kedua tahun mengikuti pola musiman yang serupa."
)

st.markdown("---")

# ── Kesimpulan ─────────────────────────────────────────────────────────────────

st.subheader('Kesimpulan & Rekomendasi')

with st.expander("📌 Kesimpulan 1 — Pola Rental Per Jam (Pertanyaan Bisnis 1)", expanded=True):
    st.markdown("""
    - **Hari Kerja** memperlihatkan pola **bimodal**: puncak pagi (**07:00–09:00**) dan puncak sore (**16:00–19:00**) → perilaku *commuting*.
    - **Hari Libur/Akhir Pekan** memperlihatkan pola **unimodal**: puncak tunggal siang hari (**12:00–14:00**) → aktivitas rekreasi.
    - Dua segmen pengguna dominan: **registered** (hari kerja, commuting) dan **casual** (akhir pekan, rekreasi).
    """)

with st.expander("📌 Kesimpulan 2 — Pengaruh Cuaca & Musim (Pertanyaan Bisnis 2)", expanded=True):
    st.markdown("""
    - **Musim Fall (Gugur)** menghasilkan rata-rata rental harian tertinggi; **Spring (Semi)** terendah.
    - Kondisi **Light Rain/Snow** menyebabkan penurunan **>60%** dibanding kondisi Clear — hambatan paling kritis.
    - Kombinasi terburuk: **Spring + Light Rain/Snow** | Kombinasi terbaik: **Fall + Clear**.
    """)

with st.expander("💡 Rekomendasi Strategis untuk Operator"):
    st.markdown("""
    | No. | Action Item | Dasar Analisis |
    |-----|------------|----------------|
    | 1 | **Fleet Rebalancing** — Tambah armada 30–40% di area perkantoran pada jam 06:30–09:30 & 15:30–19:30 hari kerja | Pola bimodal hari kerja |
    | 2 | **Dynamic Pricing** — Harga premium saat Fall + Clear; diskon saat Mist/Spring | Variasi musim & cuaca |
    | 3 | **Scheduled Maintenance** — Jadwalkan perawatan saat Heavy Rain atau Spring cuaca buruk | Permintaan mendekati nol |
    | 4 | **Targeted Marketing** — Promosi di musim Spring & Sabtu–Minggu pagi untuk konversi casual → registered | Segmentasi pengguna |
    """)

st.markdown("---")
st.caption("© 2024 Talitha Widyadhana — Proyek Analisis Data Dicoding")
