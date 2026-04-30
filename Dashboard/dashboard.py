import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import os
import warnings
warnings.filterwarnings('ignore')

# ─── Page Config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title='Bike Sharing Dashboard',
    page_icon='🚲',
    layout='wide'
)

# ─── CSS Kustom ────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    [data-testid="metric-container"] {
        background-color: #f0f4f8;
        border: 1px solid #dce3ec;
        border-radius: 10px;
        padding: 16px 20px;
    }
    .block-container { padding-top: 1.5rem; }
</style>
""", unsafe_allow_html=True)

# ─── Load Data ─────────────────────────────────────────────────────────────────
# Tentukan path relatif agar berjalan baik dari folder manapun
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DAY_PATH   = os.path.join(BASE_DIR, 'main_data.csv')
HOUR_PATH  = os.path.join(BASE_DIR, '..', 'data', 'hour.csv')

@st.cache_data(show_spinner='Memuat data...')
def load_data():
    # Load main_data (df_day yang sudah di-clean + label)
    df_day = pd.read_csv(DAY_PATH)
    df_day['dteday'] = pd.to_datetime(df_day['dteday'])

    # Pastikan kolom label tersedia (antisipasi jika main_data belum punya label)
    if 'season_label' not in df_day.columns:
        df_day['season_label']  = df_day['season'].map({1:'Spring',2:'Summer',3:'Fall',4:'Winter'})
    if 'weather_label' not in df_day.columns:
        df_day['weather_label'] = df_day['weathersit'].map({1:'Clear',2:'Mist',3:'Light Rain/Snow',4:'Heavy Rain'})
    if 'weekday_label' not in df_day.columns:
        df_day['weekday_label'] = df_day['weekday'].map({0:'Sun',1:'Mon',2:'Tue',3:'Wed',4:'Thu',5:'Fri',6:'Sat'})

    # Load hour.csv untuk analisis per jam
    df_hour = pd.read_csv(HOUR_PATH)
    df_hour['dteday']        = pd.to_datetime(df_hour['dteday'])
    df_hour['season_label']  = df_hour['season'].map({1:'Spring',2:'Summer',3:'Fall',4:'Winter'})
    df_hour['weather_label'] = df_hour['weathersit'].map({1:'Clear',2:'Mist',3:'Light Rain/Snow',4:'Heavy Rain'})
    df_hour['weekday_label'] = df_hour['weekday'].map({0:'Sun',1:'Mon',2:'Tue',3:'Wed',4:'Thu',5:'Fri',6:'Sat'})

    def kat_jam(hr):
        if   5  <= hr <= 9:  return 'Pagi (05-09)'
        elif 10 <= hr <= 14: return 'Siang (10-14)'
        elif 15 <= hr <= 19: return 'Sore (15-19)'
        else:                return 'Malam (20-04)'
    df_hour['time_cat'] = df_hour['hr'].apply(kat_jam)

    return df_day, df_hour

df_day, df_hour = load_data()

# ─── Sidebar Filter ────────────────────────────────────────────────────────────
st.sidebar.title('🔍 Filter Data')
st.sidebar.markdown('---')

year_opt = st.sidebar.multiselect(
    'Pilih Tahun',
    options=[2011, 2012],
    default=[2011, 2012]
)

season_opt = st.sidebar.multiselect(
    'Pilih Musim',
    options=['Spring', 'Summer', 'Fall', 'Winter'],
    default=['Spring', 'Summer', 'Fall', 'Winter']
)

weather_opt = st.sidebar.multiselect(
    'Pilih Kondisi Cuaca',
    options=['Clear', 'Mist', 'Light Rain/Snow', 'Heavy Rain'],
    default=['Clear', 'Mist', 'Light Rain/Snow']
)

# Terapkan filter ke df_day
df_filt = df_day[
    df_day['yr'].isin([y - 2011 for y in year_opt]) &
    df_day['season_label'].isin(season_opt) &
    df_day['weather_label'].isin(weather_opt)
].copy()

# Terapkan filter tahun ke df_hour
df_hour_filt = df_hour[
    df_hour['yr'].isin([y - 2011 for y in year_opt])
].copy()

st.sidebar.markdown('---')
st.sidebar.info(
    f'📅 Data harian terfilter : **{len(df_filt):,}** baris\n\n'
    f'⏱️ Data per jam terfilter: **{len(df_hour_filt):,}** baris'
)

# ─── Header ────────────────────────────────────────────────────────────────────
st.title('🚲 Bike Sharing Analysis Dashboard')
st.markdown('**Capital Bikeshare Washington D.C. | Periode 2011–2012**')
st.markdown('---')

# ─── Metric Cards ──────────────────────────────────────────────────────────────
c1, c2, c3, c4 = st.columns(4)

total     = int(df_filt['cnt'].sum())
rata_rata = int(df_filt['cnt'].mean()) if len(df_filt) > 0 else 0
max_val   = int(df_filt['cnt'].max())  if len(df_filt) > 0 else 0
hari_max  = (
    df_filt.loc[df_filt['cnt'].idxmax(), 'dteday'].strftime('%d %b %Y')
    if len(df_filt) > 0 else '-'
)

c1.metric('📦 Total Rental',      f'{total:,}')
c2.metric('📊 Rata-rata Harian',  f'{rata_rata:,}')
c3.metric('🏆 Hari Terbaik',      hari_max)
c4.metric('🔝 Maks. Rental/Hari', f'{max_val:,}')

st.markdown('---')

# ═══════════════════════════════════════════════════════════════════════════════
# BAGIAN 1 — Pertanyaan Bisnis 1
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader('📌 Pertanyaan Bisnis 1')
st.markdown(
    '> *Bagaimana pola rata-rata jumlah rental sepeda per jam antara hari kerja dan '
    'hari libur/akhir pekan selama periode 2011–2012, dan pada rentang jam berapakah '
    'permintaan tertinggi terjadi?*'
)

tab1, tab2 = st.tabs(['📈 Line Chart Per Jam', '🗓️ Heatmap Per Jam × Hari'])

# ── Tab 1a: Line Chart ────────────────────────────────────────────────────────
with tab1:
    hourly = (
        df_hour_filt
        .groupby(['hr', 'workingday'])['cnt']
        .mean()
        .reset_index()
        .rename(columns={'cnt': 'avg_cnt'})
    )
    wd = hourly[hourly['workingday'] == 1]
    wk = hourly[hourly['workingday'] == 0]

    fig1, ax1 = plt.subplots(figsize=(13, 4.5))

    ax1.plot(wd['hr'], wd['avg_cnt'], color='#1565C0', linewidth=2.5,
             marker='o', markersize=5, label='Hari Kerja')
    ax1.plot(wk['hr'], wk['avg_cnt'], color='#E53935', linewidth=2.5,
             marker='s', markersize=5, label='Akhir Pekan / Hari Libur')

    # Highlight jam puncak
    ax1.axvspan(7, 9,   alpha=0.10, color='#1565C0')
    ax1.axvspan(16, 19, alpha=0.10, color='#FF6F00')

    # Anotasi
    if len(wd) > 0:
        peak_wd = wd.loc[wd['avg_cnt'].idxmax()]
        ax1.annotate(
            f'Peak Sore\n(±{int(peak_wd["hr"])}:00)',
            xy=(peak_wd['hr'], peak_wd['avg_cnt']),
            xytext=(peak_wd['hr'] + 1.5, peak_wd['avg_cnt'] * 0.92),
            arrowprops=dict(arrowstyle='->', color='#FF6F00'),
            fontsize=9, color='#FF6F00'
        )

    ax1.set_xlabel('Jam (0–23)', fontsize=11)
    ax1.set_ylabel('Rata-rata Jumlah Rental', fontsize=11)
    ax1.set_title(
        'Pola Rata-rata Rental Sepeda Per Jam:\n'
        'Hari Kerja vs Akhir Pekan/Libur (Washington D.C.)',
        fontsize=13, fontweight='bold'
    )
    ax1.legend(fontsize=10)
    ax1.set_xticks(range(0, 24))
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax1.grid(axis='y', alpha=0.35, linestyle='--')
    ax1.set_facecolor('#f8f9fa')
    fig1.patch.set_facecolor('white')
    plt.tight_layout()
    st.pyplot(fig1)

    st.info(
        '**Interpretasi:** Pada hari kerja, pola bimodal teridentifikasi dengan puncak pada '
        'jam **08:00** (commute pagi) dan **17:00–18:00** (commute sore). Pada hari libur/'
        'akhir pekan, pola unimodal teridentifikasi dengan puncak di siang hari (**12:00–14:00**), '
        'yang mencerminkan dominasi aktivitas rekreasi.'
    )

# ── Tab 1b: Heatmap ───────────────────────────────────────────────────────────
with tab2:
    pivot_hm = (
        df_hour_filt
        .groupby(['weekday', 'hr'])['cnt']
        .mean()
        .unstack()
    )
    pivot_hm.index = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']

    fig2, ax2 = plt.subplots(figsize=(15, 4.5))
    sns.heatmap(
        pivot_hm, cmap='YlOrRd', ax=ax2,
        linewidths=0.15, linecolor='white',
        cbar_kws={'label': 'Rata-rata Rental'}
    )
    ax2.set_title(
        'Heatmap Rata-rata Rental per Jam dan Hari dalam Seminggu',
        fontsize=13, fontweight='bold', pad=12
    )
    ax2.set_xlabel('Jam (0–23)', fontsize=11)
    ax2.set_ylabel('Hari', fontsize=11)
    fig2.patch.set_facecolor('white')
    plt.tight_layout()
    st.pyplot(fig2)

    st.info(
        '**Interpretasi:** Sel paling gelap secara konsisten terkonsentrasi pada perpotongan '
        'hari **Senin–Jumat** dengan jam **08:00** dan **17:00–18:00**, mengonfirmasi pola '
        'commuting pada hari kerja. Hari Sabtu–Minggu menunjukkan intensitas yang lebih merata '
        'pada jam siang hari.'
    )

st.markdown('---')

# ═══════════════════════════════════════════════════════════════════════════════
# BAGIAN 2 — Pertanyaan Bisnis 2
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader('📌 Pertanyaan Bisnis 2')
st.markdown(
    '> *Seberapa besar pengaruh kondisi cuaca dan musim terhadap rata-rata total rental '
    'harian selama 2011–2012, serta kombinasi cuaca–musim manakah yang menghasilkan '
    'penurunan permintaan terbesar?*'
)

col_a, col_b = st.columns(2)

# ── Kolom A: Bar Chart Musim ──────────────────────────────────────────────────
with col_a:
    st.markdown('**🍂 Pengaruh Musim terhadap Rata-rata Rental Harian**')

    season_order = ['Spring', 'Summer', 'Fall', 'Winter']
    avg_season   = (
        df_filt.groupby('season_label')['cnt']
        .mean()
        .reindex([s for s in season_order if s in df_filt['season_label'].unique()])
    )

    fig3, ax3 = plt.subplots(figsize=(6, 4.5))
    clrs_s = ['#4CAF50', '#FF9800', '#F44336', '#2196F3'][:len(avg_season)]
    bars3  = ax3.bar(avg_season.index, avg_season.values,
                     color=clrs_s, edgecolor='white', linewidth=1.1, width=0.55)

    for bar, val in zip(bars3, avg_season.values):
        ax3.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 40,
            f'{val:,.0f}',
            ha='center', fontsize=10, fontweight='bold'
        )

    ax3.set_xlabel('Musim', fontsize=10)
    ax3.set_ylabel('Rata-rata Rental Harian', fontsize=10)
    ax3.set_title('Musim vs Rata-rata Rental Harian', fontsize=12, fontweight='bold')
    ax3.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax3.set_facecolor('#f8f9fa')
    fig3.patch.set_facecolor('white')
    ax3.grid(axis='y', alpha=0.35, linestyle='--')
    plt.tight_layout()
    st.pyplot(fig3)

# ── Kolom B: Bar Chart Cuaca ──────────────────────────────────────────────────
with col_b:
    st.markdown('**🌤️ Pengaruh Kondisi Cuaca terhadap Rata-rata Rental Harian**')

    weather_order = ['Clear', 'Mist', 'Light Rain/Snow', 'Heavy Rain']
    avg_weather   = df_filt.groupby('weather_label')['cnt'].mean()
    avg_weather_o = avg_weather.reindex(
        [w for w in weather_order if w in avg_weather.index]
    )
    palette_w = {
        'Clear': '#2196F3', 'Mist': '#90CAF9',
        'Light Rain/Snow': '#FF9800', 'Heavy Rain': '#F44336'
    }
    clrs_w = [palette_w.get(w, 'gray') for w in avg_weather_o.index]
    base   = avg_weather_o.get('Clear', avg_weather_o.iloc[0] if len(avg_weather_o) > 0 else 1)
    pct    = [(v - base) / base * 100 for v in avg_weather_o.values]

    fig4, ax4 = plt.subplots(figsize=(6, 4.5))
    bars4 = ax4.bar(avg_weather_o.index, avg_weather_o.values,
                    color=clrs_w, edgecolor='white', linewidth=1.1, width=0.5)

    for bar, val, p in zip(bars4, avg_weather_o.values, pct):
        p_str = f'{p:.1f}%' if abs(p) > 0.05 else 'Baseline'
        ax4.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 30,
            f'{val:,.0f}\n({p_str})',
            ha='center', fontsize=9, fontweight='bold'
        )

    ax4.set_xlabel('Kondisi Cuaca', fontsize=10)
    ax4.set_ylabel('Rata-rata Rental Harian', fontsize=10)
    ax4.set_title('Cuaca vs Rata-rata Rental Harian', fontsize=12, fontweight='bold')
    ax4.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax4.tick_params(axis='x', labelrotation=15)
    ax4.set_facecolor('#f8f9fa')
    fig4.patch.set_facecolor('white')
    ax4.grid(axis='y', alpha=0.35, linestyle='--')
    plt.tight_layout()
    st.pyplot(fig4)

st.info(
    '**Interpretasi:** Musim **Fall** menghasilkan rata-rata rental tertinggi. '
    'Kondisi **Light Rain/Snow** menyebabkan penurunan lebih dari **60%** dibandingkan '
    'kondisi **Clear**. Kombinasi **Fall + Clear** adalah kondisi optimal, sementara '
    '**Spring + Light Rain/Snow** adalah kondisi dengan permintaan terendah.'
)

st.markdown('---')

# ═══════════════════════════════════════════════════════════════════════════════
# BAGIAN 3 — Tren Bulanan YoY
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader('📈 Tren Rata-rata Rental Bulanan: 2011 vs 2012')

yoy = (
    df_filt
    .groupby(['yr', 'mnth'])['cnt']
    .mean()
    .reset_index()
)

bulan_label = ['Jan','Feb','Mar','Apr','Mei','Jun',
               'Jul','Agu','Sep','Okt','Nov','Des']

fig5, ax5 = plt.subplots(figsize=(13, 4.5))
for yr_val, label, clr, mrkr in [(0, '2011', '#1565C0', 'o'), (1, '2012', '#E53935', 's')]:
    subset = yoy[yoy['yr'] == yr_val]
    if len(subset) > 0:
        ax5.plot(subset['mnth'], subset['cnt'],
                 marker=mrkr, linewidth=2.5, markersize=6,
                 color=clr, label=label)

ax5.set_xticks(range(1, 13))
ax5.set_xticklabels(bulan_label)
ax5.set_xlabel('Bulan', fontsize=11)
ax5.set_ylabel('Rata-rata Rental Harian', fontsize=11)
ax5.set_title(
    'Tren Rata-rata Rental Bulanan per Tahun (2011 vs 2012)',
    fontsize=13, fontweight='bold'
)
ax5.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
ax5.legend(title='Tahun', fontsize=10)
ax5.grid(axis='y', alpha=0.35, linestyle='--')
ax5.set_facecolor('#f8f9fa')
fig5.patch.set_facecolor('white')
plt.tight_layout()
st.pyplot(fig5)

st.info(
    '**Interpretasi:** Kurva tahun **2012** secara konsisten berada di atas kurva **2011** '
    'pada hampir seluruh bulan, mengindikasikan pertumbuhan basis pengguna layanan bike '
    'sharing yang berkelanjutan antara dua periode tersebut.'
)

st.markdown('---')

# ═══════════════════════════════════════════════════════════════════════════════
# BAGIAN 4 — Kesimpulan & Rekomendasi
# ═══════════════════════════════════════════════════════════════════════════════
st.subheader('📝 Kesimpulan & Rekomendasi')

with st.expander('📌 Kesimpulan 1 — Pola Rental Per Jam (Pertanyaan Bisnis 1)'):
    st.markdown("""
    - Pada **hari kerja**, permintaan rental memperlihatkan **pola bimodal** dengan dua puncak
      utama: jam **08:00** (*morning commute*) dan jam **17:00–18:00** (*evening commute*).
    - Pada **akhir pekan/libur**, permintaan mengikuti **pola unimodal** dengan puncak tunggal
      di siang hari (jam **12:00–14:00**), mencerminkan aktivitas rekreasi.
    - Perbedaan pola ini mengindikasikan dua segmen pengguna dominan: pengguna *registered*
      (commuter) dan pengguna *casual* (rekreasi).
    """)

with st.expander('📌 Kesimpulan 2 — Pengaruh Cuaca dan Musim (Pertanyaan Bisnis 2)'):
    st.markdown("""
    - **Musim Fall** menghasilkan rata-rata rental harian tertinggi; **Musim Spring** terendah.
    - Kondisi **Light Rain/Snow** menyebabkan penurunan rata-rata rental **>60%**
      dibandingkan kondisi **Clear**.
    - Kombinasi **Fall + Clear** merupakan kondisi optimal; **Spring + Light Rain/Snow**
      merupakan kondisi dengan permintaan terendah.
    """)

with st.expander('💡 Rekomendasi Action Items'):
    st.markdown("""
    | No. | Action Item | Dasar Analisis |
    |-----|-------------|----------------|
    | 1 | **Fleet Rebalancing:** Tambah armada 30–40% di jam 06:30–09:30 & 15:30–19:30 pada hari kerja | Pola bimodal commuting |
    | 2 | **Dynamic Pricing:** Harga premium saat Fall + Clear; diskon saat Spring/cuaca berkabut | Variasi musim & cuaca |
    | 3 | **Maintenance Window:** Jadwalkan perawatan saat Heavy Rain atau Spring cuaca buruk | Demand mendekati nol |
    | 4 | **Targeted Marketing:** Kampanye promosi di musim Spring dan akhir pekan pagi hari | Demand rendah, potensi konversi |
    """)

st.markdown('---')
st.caption('📊 Dashboard dibuat dengan Streamlit · Data: Capital Bikeshare Washington D.C. (2011–2012)')