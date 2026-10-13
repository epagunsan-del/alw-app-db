
import os
import streamlit as st
import pandas as pd
import plotly.express as px

# ------------------------------------------------------------------------------
# 1. PAGE CONFIGURATION & HEADER
# ------------------------------------------------------------------------------

st.set_page_config(
    page_title="Anna Leigh Waters Sports Analytics Dashboard",
    page_icon="🏓",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏓 Anna Leigh Waters: Professional Performance & Match Analytics")

st.markdown("""
This interactive data dashboard explores the competitive record, scoring
margins, and statistical dominance of World No. 1 professional pickleball
athlete **Anna Leigh Waters (ALW)**.

Filter match records dynamically in the sidebar to inspect trends across
disciplines, stages, and years.
""")

# ------------------------------------------------------------------------------
# 2. DATA LOADING & CACHING
# ------------------------------------------------------------------------------

@st.cache_data
def load_data():
    if os.path.exists("data/alw_stats.csv"):
        file_path = "data/alw_stats.csv"
    elif os.path.exists("alw_stats.csv"):
        file_path = "alw_stats.csv"
    else:
        st.error("⚠️ Dataset file 'alw_stats.csv' could not be found.")
        return pd.DataFrame()

    try:
        df = pd.read_csv(file_path)

        required_columns = [
            "Date", "Discipline", "Year", "Round",
            "Point_Differential", "Match_Result", "Is_Pickle",
            "Tournament", "Opponent", "Partner", "Games_Won",
            "Games_Lost", "Clean_Winners"
        ]

        missing_columns = [
            column for column in required_columns
            if column not in df.columns
        ]

        if missing_columns:
            st.error(
                f"Dataset is missing required columns: "
                f"{', '.join(missing_columns)}"
            )
            return pd.DataFrame()

        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
        df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
        df["Point_Differential"] = pd.to_numeric(
            df["Point_Differential"], errors="coerce"
        )
        df["Clean_Winners"] = pd.to_numeric(
            df["Clean_Winners"], errors="coerce"
        )
        df["Is_Pickle"] = (
            df["Is_Pickle"]
            .astype(str)
            .str.strip()
            .str.lower()
            .isin(["true", "1", "yes"])
        )

        df = df.dropna(
            subset=["Date", "Year", "Point_Differential"]
        )

        df["Year"] = df["Year"].astype(int)

        return df

    except Exception as error:
        st.error(f"Error loading dataset: {error}")
        return pd.DataFrame()


raw_df = load_data()

if raw_df.empty:
    st.warning("No valid match records are available.")
    st.stop()

# ------------------------------------------------------------------------------
# 3. INTERACTIVE SIDEBAR FILTERS
# ------------------------------------------------------------------------------

st.sidebar.header("🎯 Filter Match Data")

# Filter 1: Discipline
available_disciplines = sorted(
    raw_df["Discipline"].dropna().unique().tolist()
)

selected_disciplines = st.sidebar.multiselect(
    "Select Discipline(s):",
    options=available_disciplines,
    default=available_disciplines
)

# Filter 2: Year
available_years = sorted(
    raw_df["Year"].unique().tolist()
)

selected_years = st.sidebar.multiselect(
    "Select Year(s):",
    options=available_years,
    default=available_years
)

# Filter 3: Tournament Round
available_rounds = [
    "All Rounds"
] + sorted(raw_df["Round"].dropna().unique().tolist())

selected_round = st.sidebar.selectbox(
    "Select Tournament Round:",
    options=available_rounds,
    index=0
)

# Filter 4: Point Differential
min_diff = int(raw_df["Point_Differential"].min())
max_diff = int(raw_df["Point_Differential"].max())

diff_threshold = st.sidebar.slider(
    "Minimum Point Differential:",
    min_value=min_diff,
    max_value=max_diff,
    value=min_diff,
    help="Filter for matches with at least this net scoring margin."
)

# Apply filters
filtered_df = raw_df[
    (raw_df["Discipline"].isin(selected_disciplines))
    & (raw_df["Year"].isin(selected_years))
    & (raw_df["Point_Differential"] >= diff_threshold)
]

if selected_round != "All Rounds":
    filtered_df = filtered_df[
        filtered_df["Round"] == selected_round
    ]

if filtered_df.empty:
    st.warning(
        "No matches found matching the selected filter criteria. "
        "Please adjust your filters."
    )
    st.stop()

# ------------------------------------------------------------------------------
# 4. SUMMARY STATISTICS
# ------------------------------------------------------------------------------

st.subheader("📈 Summary Performance Statistics")

total_matches = len(filtered_df)

wins_count = int(
    (filtered_df["Match_Result"] == "Win").sum()
)

win_rate = (
    wins_count / total_matches * 100
    if total_matches > 0
    else 0.0
)

mean_point_diff = filtered_df["Point_Differential"].mean()
median_point_diff = filtered_df["Point_Differential"].median()
total_pickles = int(filtered_df["Is_Pickle"].sum())

col1, col2, col3, col4, col5 = st.columns(5)

col1.metric("Total Matches (Count)", f"{total_matches}")
col2.metric("Win Rate (%)", f"{win_rate:.1f}%", f"{wins_count} Wins")
col3.metric("Mean Point Diff", f"{mean_point_diff:+.2f}")
col4.metric("Median Point Diff", f"{median_point_diff:+.1f}")
col5.metric("11–0 Pickles Count", f"{total_pickles}")

st.markdown("---")

# ------------------------------------------------------------------------------
# 5. PERFORMANCE VISUALIZATIONS
# ------------------------------------------------------------------------------

st.subheader("📊 Performance Visualizations")

# Chart 1: Bar Chart - Wins/Losses by Discipline
chart_row1_col1, chart_row1_col2 = st.columns(2)

with chart_row1_col1:
    fig_bar = px.histogram(
        filtered_df,
        x="Discipline",
        color="Match_Result",
        barmode="group",
        title="1. Match Outcomes Across Disciplines",
        color_discrete_map={
            "Win": "#2ca02c",
            "Loss": "#d62728"
        },
        text_auto=True
    )

    fig_bar.update_layout(
        xaxis_title="Discipline",
        yaxis_title="Match Count",
        legend_title="Outcome"
    )

    st.plotly_chart(fig_bar, use_container_width=True)

# Chart 2: Histogram - Point Differential
with chart_row1_col2:
    fig_hist = px.histogram(
        filtered_df,
        x="Point_Differential",
        nbins=22,
        marginal="box",
        title="2. Distribution of Net Point Differentials",
        color_discrete_sequence=["#1f77b4"]
    )

    fig_hist.update_layout(
        xaxis_title="Point Differential",
        yaxis_title="Frequency"
    )

    st.plotly_chart(fig_hist, use_container_width=True)

# Chart 3: Scatter Plot - Clean Winners vs. Point Differential
chart_row2_col1, chart_row2_col2 = st.columns(2)

with chart_row2_col1:
    fig_scatter = px.scatter(
        filtered_df,
        x="Clean_Winners",
        y="Point_Differential",
        color="Discipline",
        symbol="Match_Result",
        hover_data=[
            "Tournament",
            "Opponent",
            "Partner",
            "Round"
        ],
        title="3. Clean Winners vs. Point Differential",
        color_discrete_sequence=px.colors.qualitative.Dark24
    )

    fig_scatter.update_layout(
        xaxis_title="Clean Winners",
        yaxis_title="Point Differential"
    )

    st.plotly_chart(fig_scatter, use_container_width=True)

# Chart 4: Box Plot - Point Differential by Tournament Round
with chart_row2_col2:
    round_order = [
        "Round of 16",
        "Quarterfinal",
        "Semifinal",
        "Final"
    ]

    fig_box = px.box(
        filtered_df,
        x="Round",
        y="Point_Differential",
        category_orders={"Round": round_order},
        color="Round",
        points="all",
        title="4. Margin of Victory by Tournament Round"
    )

    fig_box.update_layout(
        xaxis_title="Tournament Round",
        yaxis_title="Point Differential",
        showlegend=False
    )

    st.plotly_chart(fig_box, use_container_width=True)

# Chart 5: Donut Chart - Matches by Discipline
fig_donut = px.pie(
    filtered_df,
    names="Discipline",
    hole=0.45,
    title="5. Event Workload Distribution by Discipline",
    color_discrete_sequence=px.colors.qualitative.Pastel
)

st.plotly_chart(fig_donut, use_container_width=True)

st.markdown("---")

# ------------------------------------------------------------------------------
# 6. INTERACTIVE DATA TABLE
# ------------------------------------------------------------------------------

st.subheader("📋 Match Records Explorer")

st.markdown(
    "Explore and sort individual match records from the filtered subset:"
)

display_cols = [
    "Date",
    "Tournament",
    "Discipline",
    "Round",
    "Partner",
    "Opponent",
    "Match_Result",
    "Games_Won",
    "Games_Lost",
    "Point_Differential",
    "Clean_Winners",
    "Is_Pickle"
]

st.dataframe(
    filtered_df[display_cols].sort_values(
        by="Date",
        ascending=False
    ),
    use_container_width=True,
    hide_index=True
)

st.markdown("---")

# ------------------------------------------------------------------------------
# 7. KEY ANALYTICAL INSIGHTS
# ------------------------------------------------------------------------------

st.subheader("💡 Key Analytical Insights")

# Calculate insights from the filtered dataset
average_margin = filtered_df["Point_Differential"].mean()

clean_winner_matches = filtered_df[
    filtered_df["Clean_Winners"] > 18
]

if not clean_winner_matches.empty:
    clean_winner_win_rate = (
        (clean_winner_matches["Match_Result"] == "Win").mean() * 100
    )
else:
    clean_winner_win_rate = None

discipline_win_rates = (
    filtered_df.assign(
        Is_Win=filtered_df["Match_Result"].eq("Win")
    )
    .groupby("Discipline")["Is_Win"]
    .mean()
    .mul(100)
)

best_discipline = (
    discipline_win_rates.idxmax()
    if not discipline_win_rates.empty
    else "N/A"
)

st.markdown(
    f"""
1. **Winning Margin Consistency:** The average point differential
   in the filtered dataset is **{average_margin:+.2f}**.
   A positive value indicates that ALW scored more points than her
   opponents on average, while a negative value indicates the opposite.

2. **Offensive Production:** There are **{len(clean_winner_matches)}**
   matches with more than 18 recorded clean winners.
   {
       f"The win rate in these matches is {clean_winner_win_rate:.1f}%."
       if clean_winner_win_rate is not None
       else "There are no matches with more than 18 recorded clean winners."
   }
   This describes an observed association and does not prove causation.

3. **Performance Across Disciplines:** Based on the filtered records,
   **{best_discipline}** has the highest observed win rate among
   the available disciplines. This result depends on the records and
   filters currently selected.
"""
)

st.markdown("---")

# ------------------------------------------------------------------------------
# 8. DATASET CITATION
# ------------------------------------------------------------------------------

st.caption("""
**Data Citation & Sources**

- Professional Pickleball Association (Carvana PPA Tour):
  https://www.ppatour.com/athletes/anna-leigh-waters/

- PPA Tour historical information:
  https://www.ppatour.com/about/history/

- Supplementary pickleball statistics and analysis:
  The Dink Pickleball — https://www.thedinkpickleball.com/

Note: Verify match-level statistics against the original sources.
Any modeled or illustrative records must be clearly identified as such.
""")
