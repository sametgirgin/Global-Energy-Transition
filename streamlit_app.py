import altair as alt
import pandas as pd
import streamlit as st
from pathlib import Path
from typing import Dict, List


st.set_page_config(
    page_title="Global Energy Transition Explorer",
    layout="wide",
)

# Workbook location
DATA_FILE = Path(__file__).parent / "2025 Country Transition Tracker Data.xlsx"
LOGO_FILE = Path(__file__).parent / "logo.png"

# Mapping of user-facing labels to sheet names in the workbook
SHEETS: Dict[str, str] = {
    "Energy Related Greenhouse Gas Emissions (Mt CO2e)": "Greenhouse Gas Emissions",
    "Fossil Fuel Consumption (EJ)": "Fossil Fuel Consumption (EJ)",
    "Renewable Energy Consumption (EJ)": "Renewable Energy Consumption",
    "Power Sector Decarbonisation (generation mix share)": "Power Sector Decarbonisation",
    "Carbon Intensity (tCO2-eq per MJ)": "Carbon Int (tCO2-eq per MJ)",
    "Energy Consumption per Capita (GJ per person)": "Energy Consumption per Capita",
    "Economy-wide Carbon Intensity (CO2e per $ GDP)": "Economic Energy Intensity",
    "Carbon Intensity (CO2e per $ GDP)": "Carbon Intensity (per GDP)",
}

DESCRIPTIONS: Dict[str, str] = {
    "Energy Related Greenhouse Gas Emissions (Mt CO2e)": (
        "Energy-sector greenhouse gas emissions (million tonnes of CO2e)."
    ),
    "Fossil Fuel Consumption (EJ)": "Total fossil fuel consumption in exajoules.",
    "Renewable Energy Consumption (EJ)": "Total renewable energy consumption in exajoules.",
    "Power Sector Decarbonisation (generation mix share)": (
        "Share of electricity generation by source. Values represent fractions of total generation."
    ),
    "Carbon Intensity (tCO2-eq per MJ)": "Carbon intensity of energy supply (tonnes CO2e per megajoule).",
    "Energy Consumption per Capita (GJ per person)": "Per-capita energy use in gigajoules.",
    "Economy-wide Carbon Intensity (CO2e per $ GDP)": (
        "Energy intensity of the economy: energy used per unit of GDP."
    ),
    "Carbon Intensity (CO2e per $ GDP)": "Carbon intensity per unit of GDP.",
}


@st.cache_data(show_spinner=False)
def load_markdown(md_path: Path) -> str:
    if not md_path.exists():
        return ""
    return md_path.read_text(encoding="utf-8")


@st.cache_data(show_spinner=False)
def load_sheet(sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(DATA_FILE, sheet_name=sheet_name)
    # Drop unnamed helper columns that sometimes appear in Excel exports.
    df = df.loc[:, ~df.columns.astype(str).str.contains("^Unnamed")]

    # Normalize numeric year columns to integers for consistent sorting.
    new_columns = {}
    for col in df.columns:
        if col == "Country":
            continue
        try:
            new_columns[col] = int(col)
        except (ValueError, TypeError):
            new_columns[col] = col
    df = df.rename(columns=new_columns)
    return df


def melt_time_series(df: pd.DataFrame) -> pd.DataFrame:
    year_cols: List = [col for col in df.columns if col != "Country"]
    long_df = (
        df.melt(id_vars="Country", value_vars=year_cols, var_name="Year", value_name="Value")
        .dropna(subset=["Value"])
    )
    long_df["Year"] = long_df["Year"].astype(str)
    long_df["Value"] = pd.to_numeric(long_df["Value"], errors="coerce")
    return long_df.dropna(subset=["Value"])


def time_series_layout(label: str, df: pd.DataFrame) -> None:
    countries = sorted(df["Country"].dropna().unique())
    default_selection = countries[:8] if len(countries) > 8 else countries
    selected = st.sidebar.multiselect("Countries", countries, default=default_selection)

    long_df = melt_time_series(df)
    if selected:
        long_df = long_df[long_df["Country"].isin(selected)]
    year_order = sorted(long_df["Year"].unique())

    st.subheader(label)
    col_chart, col_table = st.columns((2, 1))

    if not long_df.empty:
        chart = (
            alt.Chart(long_df)
            .mark_line(point=True)
            .encode(
                x=alt.X("Year:O", sort=year_order, title="Year"),
                y=alt.Y("Value:Q", title="Value"),
                color="Country:N",
                tooltip=["Country", "Year", alt.Tooltip("Value:Q", format=",.3f")],
            )
            .properties(height=420)
        )
        col_chart.altair_chart(chart, use_container_width=True)
    else:
        col_chart.info("Select at least one country to see the trend.")

    # Latest year snapshot table
    value_cols = [c for c in df.columns if c != "Country"]
    if value_cols:
        latest_year = max(value_cols)
        snapshot = (
            df[["Country", latest_year]]
            .rename(columns={latest_year: f"{latest_year} value"})
            .sort_values(f"{latest_year} value", ascending=False)
        )
        col_table.caption(f"Latest year snapshot ({latest_year})")
        col_table.dataframe(snapshot, hide_index=True, use_container_width=True)

    with st.expander("Data table"):
        if selected:
            st.dataframe(df[df["Country"].isin(selected)].reset_index(drop=True))
        else:
            st.dataframe(df.reset_index(drop=True))


def power_mix_layout(df: pd.DataFrame) -> None:
    st.subheader("Power Sector Decarbonisation (generation mix share)")
    countries = sorted(df["Country"].dropna().unique())
    selected = st.sidebar.selectbox("Country", countries, index=0)

    row = df[df["Country"] == selected].iloc[0]
    source_cols = [c for c in df.columns if c != "Country"]
    mix_df = pd.DataFrame({"Source": source_cols, "Share": [row[c] for c in source_cols]})

    chart = (
        alt.Chart(mix_df)
        .mark_bar()
        .encode(
            x=alt.X("Source:N", sort=source_cols, title="Generation Source"),
            y=alt.Y("Share:Q", title="Share of generation"),
            color="Source:N",
            tooltip=["Source", alt.Tooltip("Share:Q", format=".2%")],
        )
        .properties(height=420)
    )
    st.altair_chart(chart, use_container_width=True)

    mix_df_display = mix_df.copy()
    mix_df_display["Share (%)"] = (mix_df_display["Share"] * 100).round(2)
    st.dataframe(
        mix_df_display[["Source", "Share (%)"]],
        hide_index=True,
        use_container_width=True,
    )


def main() -> None:
    title_col, logo_col = st.columns([4, 1])
    with title_col:
        st.title("Global Energy Transition Explorer")
        st.caption(
            "Interactive visuals for key energy and emissions indicators. Data sourced from the "
            "2025 Country Transition Tracker workbook."
        )
    with logo_col:
        if LOGO_FILE.exists():
            st.image(str(LOGO_FILE), use_column_width=True)

    indicator = st.sidebar.selectbox("Indicator", list(SHEETS.keys()))
    st.sidebar.markdown("Use filters below to focus on specific countries.")

    sheet_name = SHEETS[indicator]
    description = DESCRIPTIONS.get(indicator)
    if description:
        st.write(description)

    if not DATA_FILE.exists():
        st.error(f"Data file not found at {DATA_FILE}")
        return

    df = load_sheet(sheet_name)

    if sheet_name == "Power Sector Decarbonisation":
        power_mix_layout(df)
    else:
        time_series_layout(indicator, df)

    # Supplementary methodology content for GHG emissions
    if indicator == "Energy Related Greenhouse Gas Emissions (Mt CO2e)":
        md_path = Path(__file__).parent / "greenhousegas.md"
        markdown_content = load_markdown(md_path)
        if markdown_content:
            st.divider()
            st.markdown(markdown_content)
        else:
            st.warning(f"Supplementary markdown not found at {md_path}")
    if indicator == "Carbon Intensity (tCO2-eq per MJ)":
        md_path = Path(__file__).parent / "carbonintensity.md"
        markdown_content = load_markdown(md_path)
        if markdown_content:
            st.divider()
            st.markdown(markdown_content)
        else:
            st.warning(f"Supplementary markdown not found at {md_path}")


if __name__ == "__main__":
    main()
