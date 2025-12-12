# Global Energy Transition Explorer

An interactive Streamlit dashboard to explore key energy and emissions indicators from `2025 Country Transition Tracker Data.xlsx`. The app loads the workbook locally, visualizes time-series trends, and shows supplementary methodology notes for select indicators.

## Features
- Indicator selector with sidebar filters.
- Multi-country line charts and latest-year leader tables for time-series sheets.
- Power mix visualization for the decarbonisation sheet.
- Embedded methodology markdown for greenhouse gas emissions and carbon intensity.
- Caching for faster sheet reloads.

## Requirements
- Python 3.9+ (tested with 3.13)
- Packages: `streamlit`, `pandas`, `openpyxl` (install via `pip install -r requirements.txt`)

## Running the App
1) Ensure the following files are in the project directory:
   - `2025 Country Transition Tracker Data.xlsx`
   - `greenhousegas.md` (optional, shows under the GHG tab)
   - `carbonintensity.md` (optional, shows under the Carbon Intensity (tCO2-eq per MJ) tab)
   - `logo.png` (optional, renders beside the title)
2) Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3) Launch Streamlit:
   ```bash
   streamlit run streamlit_app.py
   ```
4) Use the sidebar to choose an indicator and filter countries; expand data tables for full details.

## Notes
- The app uses `st.cache_data` to avoid re-reading the workbook on every interaction.
- If optional markdown files are missing, a warning appears but the app continues to function.
