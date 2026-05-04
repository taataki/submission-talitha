import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
import streamlit as st

sns.set(style='dark')

# Helper functions

def create_hourly_pattern_df(df):
    hourly = (
        df.groupby(['hr', 'workingday'])['cnt']
        .mean()
        .reset_index()
        .rename(columns={'cnt': 'avg_cnt'})
    )
    wd = hourly[hourly['workingday'] == 1].copy()
    wk = hourly[hourly['workingday'] == 0].copy()
    return wd, wk

def create_season_df(df):
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
    yoy = (
        df.groupby(['yr', 'mnth'])['cnt']
        .mean()
        .reset_index()
    )
    yoy['Tahun'] = yoy['yr'].map({0: '2011', 1: '2012'})
    return yoy

def create_heatmap_df(df):
    pivot = (
        df.groupby(['weekday', 'hr'])['cnt']
        .mean()
        .unstack()
    )
    pivot.index = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    return pivot

# Load cleaned data
day_df  = pd.read_csv("main_data.csv")
hour_df = pd.read_csv("hour_data.csv")

day_df.sort_values(by="dteday", inplace=True)
day_df.reset_index(drop=True, inplace=True)
hour_df.sort_values(by="dteday", inplace=True)
hour_df.reset_index(drop=True, inplace=True)

for df in [day_df, hour_df]:
    df["dteday"] = pd.to_datetime(df["dteday"])

season_map  = {1: 'Spring', 2: 'Summer', 3: 'Fall', 4: 'Winter'}
weather_map = {1: 'Clear',  2: 'Mist',   3: 'Light Rain/Snow', 4: 'Heavy Rain'}
weekday_map = {0: 'Sun', 1: 'Mon', 2: 'Tue', 3: 'Wed', 4: 'Thu', 5: 'Fri', 6: 'Sat'}

for df in [day_df, hour_df]:
    if 'season_label'  not in df.columns:
        df['season_label']  = df['season'].map(season_map)
    if 'weather_label' not in df.columns:
        df['weather_label'] = df['weathersit'].map(weather_map)
    if 'weekday_label' not in df.columns:
        df['weekday_label'] = df['weekday'].map(weekday_map)

# Filter data
min_date = day_df["dteday"].min()
max_date = day_df["dteday"].max()

with st.sidebar:
    start_date, end_date = st.date_input(
        label='Rentang Waktu',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_day_df = day_df[
    (day_df["dteday"] >= str(start_date)) &
    (day_df["dteday"] <= str(end_date))
]
main_hour_df = hour_df[
    (hour_df["dteday"] >= str(start_date)) &
    (hour_df["dteday"] <= str(end_date))
]

# Menyiapkan berbagai dataframe
wd_df, wk_df  = create_hourly_pattern_df(main_hour_df)
season_df     = create_season_df(main_day_df)
weather_df    = create_weather_df(main_day_df)
yoy_df        = create_yoy_df(main_day_df)
heatmap_pivot = create_heatmap_df(main_hour_df)


# ── Dashboard ─────────────────────────────────────────────────────────────────

st.header('Bike Sharing Dashboard :bike:')

# Total rental metrics
st.subheader('Total Rentals')

col1, col2 = st.columns(2)

with col1:
    total_rental = int(main_day_df['cnt'].sum())
    st.metric("Total Rentals", value=f"{total_rental:,}")

with col2:
    avg_daily = int(main_day_df['cnt'].mean())
    st.metric("Average Daily Rentals", value=f"{avg_daily:,}")

# Tren rental harian
fig, ax = plt.subplots(figsize=(16, 8))
daily = main_day_df.resample('D', on='dteday')['cnt'].sum().reset_index()
ax.plot(
    daily["dteday"],
    daily["cnt"],
    marker='o',
    linewidth=2,
    color="#90CAF9"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)


# Pola rental per jam
st.subheader("Hourly Rental Pattern")

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(wd_df['hr'], wd_df['avg_cnt'],
        color='steelblue', linewidth=2.5, marker='o', markersize=5, label='Working Day')
ax.plot(wk_df['hr'], wk_df['avg_cnt'],
        color='coral', linewidth=2.5, marker='s', markersize=5, label='Weekend / Holiday')
ax.legend(fontsize=20)
ax.set_xlabel('Hour', fontsize=20)
ax.set_ylabel('Average Rentals', fontsize=20)
ax.set_xticks(range(0, 24))
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)


# Heatmap
st.subheader("Rental Heatmap by Hour & Day")

fig, ax = plt.subplots(figsize=(20, 6))
sns.heatmap(
    heatmap_pivot,
    cmap='YlOrRd',
    ax=ax,
    linewidths=0.3,
    linecolor='white',
    cbar_kws={'label': 'Avg Rentals'},
    annot=True,
    fmt='.0f',
    annot_kws={'size': 7}
)
ax.set_xlabel('Hour', fontsize=15)
ax.set_ylabel('Day', fontsize=15)
ax.tick_params(axis='y', labelsize=15)
ax.tick_params(axis='x', labelsize=12)
st.pyplot(fig)


# Pengaruh musim & cuaca
st.subheader("Effect of Season & Weather")

col1, col2 = st.columns(2)

colors_season = ["#90CAF9", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

with col1:
    fig, ax = plt.subplots(figsize=(20, 10))
    sns.barplot(
        x="season_label",
        y="avg_cnt",
        data=season_df.sort_values(by="avg_cnt", ascending=False),
        palette=colors_season,
        ax=ax
    )
    ax.set_title("Average Rentals by Season", loc="center", fontsize=50)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax.tick_params(axis='x', labelsize=35)
    ax.tick_params(axis='y', labelsize=30)
    st.pyplot(fig)

with col2:
    colors_weather = ["#90CAF9", "#D3D3D3", "#D3D3D3"]
    fig, ax = plt.subplots(figsize=(20, 10))
    sns.barplot(
        x="weather_label",
        y="avg_cnt",
        data=weather_df.sort_values(by="avg_cnt", ascending=False),
        palette=colors_weather,
        ax=ax
    )
    ax.set_title("Average Rentals by Weather", loc="center", fontsize=50)
    ax.set_ylabel(None)
    ax.set_xlabel(None)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
    ax.tick_params(axis='x', labelsize=30)
    ax.tick_params(axis='y', labelsize=30)
    st.pyplot(fig)


# Tren YoY
st.subheader("Monthly Rental Trend: 2011 vs 2012")

bulan_label = ['Jan','Feb','Mar','Apr','Mei','Jun','Jul','Agu','Sep','Okt','Nov','Des']

fig, ax = plt.subplots(figsize=(16, 8))
for yr_val, label, clr, mrkr in [(0, '2011', '#1565C0', 'o'), (1, '2012', '#E53935', 's')]:
    subset = yoy_df[yoy_df['yr'] == yr_val]
    if not subset.empty:
        ax.plot(subset['mnth'], subset['cnt'],
                marker=mrkr, linewidth=2.5, markersize=8, color=clr, label=label)
ax.set_xticks(range(1, 13))
ax.set_xticklabels(bulan_label)
ax.legend(title='Year', fontsize=20, title_fontsize=15)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:,.0f}'))
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)
st.pyplot(fig)


st.caption('Copyright © Talitha Widyadhana 2024')
