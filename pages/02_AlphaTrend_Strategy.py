import streamlit as st
import pandas as pd
import datetime
from src.shared.universe import get_asset_name
import src.shared.universe as universe
from src.shared.market_data import MarketData
from src.shared.universe import get_universe, ASSET_POOLS
from src.alpha.backtester import BacktestEngine
import src.alpha.analytics as analytics
from src.shared.ui import render_header

# --- SESSION STATE INITIALIZATION ---
if 'shared_corr_threshold' not in st.session_state:
    st.session_state.shared_corr_threshold = 0.60
if 'slider_top_key' not in st.session_state:
    st.session_state.slider_top_key = st.session_state.shared_corr_threshold
if 'slider_bottom_key' not in st.session_state:
    st.session_state.slider_bottom_key = st.session_state.shared_corr_threshold

CORR_LOOKBACK_WINDOW = 60

if 'backtest_results' not in st.session_state:
    st.session_state.backtest_results = None
if 'benchmark_data' not in st.session_state:
    st.session_state.benchmark_data = None
if 'params' not in st.session_state:
    st.session_state.params = {}
if 'run_trigger' not in st.session_state:
    st.session_state.run_trigger = False

# --- CALLBACKS ---
def update_corr_from_top():
    new_val = st.session_state.slider_top_key
    st.session_state.shared_corr_threshold = new_val
    st.session_state.slider_bottom_key = new_val 
    st.session_state.run_trigger = True 

def update_corr_from_bottom():
    new_val = st.session_state.slider_bottom_key
    st.session_state.shared_corr_threshold = new_val
    st.session_state.slider_top_key = new_val 
    st.session_state.run_trigger = True

# --- PAGE CONFIGURATION ---
st.set_page_config(page_title="AlphaStream Strategy", page_icon="assets/logo.png", layout="wide", initial_sidebar_state="collapsed")
render_header()

st.title("Pure Alpha Generation & Beta Neutralization")
with st.expander("The motivations behind this project"):
    st.markdown("""
    ### The Natixis Student Challenge & Asset Allocation
    I initially designed the baseline of this project as part of my participation in the **Natixis Student Challenge**. Although my team was not selected for the final rounds, I wanted to push the study further to deeply analyze the performance of our investment strategy.

    My objective was to build a robust systematic engine combining several key concepts—primarily establishing **Risk Parity** across three main asset classes (Equities, Bonds, Commodities), while actively deploying **Momentum Seeking** signals that dynamically limit clustering and highly correlated bets. This approach ultimately creates an all-weather portfolio structurally resistant to massive market whiplashes.
    
    *(Note: The original Natixis strategy also included a strong ESG component with score attribution constraints, which I chose to omit in this specific dashboard focus).*
    """)

st.markdown("""
    <style>
        .block-container {padding-top: 1rem; padding-bottom: 2rem;}
        .stButton button {height: 2.2rem; font-size: 0.8rem;}
        .stNumberInput input {height: 2rem;}
    </style>
""", unsafe_allow_html=True)


# --- CONTROL BOX (TOP CONTAINER) ---
with st.container(border=True):
    st.markdown("Backtest Configuration")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.caption("Benchmark to Beat")
        selected_benchmark = st.selectbox("Benchmark", options=["SPY (S&P 500)", "Risk Parity (Multi-Asset)"], index=1, label_visibility="collapsed", key="bench_input")
    with c2:
        st.caption("Start Date")
        start_date = st.date_input("Start", value=datetime.date(2022, 1, 1), label_visibility="collapsed", key="start_date_input")
    with c3:
        freq_map = {"ME": "Monthly", "W-FRI": "Weekly (Fri)", "QE": "Quarterly"}
        st.caption("Rebalance Freq")
        rebal_freq = st.selectbox("Freq", options=list(freq_map.keys()), format_func=lambda x: freq_map.get(x, x), index=0, label_visibility="collapsed")
        
    c4, c5, c6 = st.columns(3)
    with c4:
        st.caption("Signal Method")
        selected_signal = st.selectbox("Signal", options=["z_score", "rsi", "distance_ma"], format_func=lambda x: x.replace("_", " ").upper(), index=0, label_visibility="collapsed", key="signal_input", help="Select the signal method to use for generating trading signals.")
    with c5:
        st.caption("Max Correlation Threshold")
        corr_limit = st.slider("Correlation Threshold", min_value=0.5, max_value=0.99, step=0.05, label_visibility="collapsed",key="slider_top_key", on_change=update_corr_from_top, help="Assets with correlation higher than this will be skipped during selection.")
    with c6:
        st.caption("Top N (per Class)")
        top_n = st.number_input("Top N", min_value=1, max_value=5, value=2, label_visibility="collapsed", key="top_n_input")
            
    # --- SIMPLE PRE-SELECTION ---
    all_classes = list(ASSET_POOLS.keys())
    desired_defaults = ['Equities US', 'Bonds', 'Commodities']
    default_classes = [c for c in desired_defaults if c in all_classes]
    
    st.markdown("### Investment Universe")
    selected_classes = st.multiselect("Select High-Level Asset Classes", options=all_classes, default=default_classes, help="Select which broad categories of assets to include. Pre-selecting Equities, Bonds, and Commodities builds a classic balanced portfolio.")
    
    universe_dict = {}
    
    if selected_classes:
        # Initialize dictionary with all tickers from selected classes up to 10 by default to save processing time
        for c_name in selected_classes:
            universe_dict[c_name] = ASSET_POOLS[c_name][:10]
            
        with st.expander("Advanced Customization (Select Specific Assets)", expanded=False):
            st.caption("Refine individual selections per class. If you leave a category empty here, it will be skipped entirely.")
            
            # Create a dynamic number of columns based on selected classes
            num_cols = len(selected_classes)
            if num_cols > 0:
                cols = st.columns(min(num_cols, 4)) # max 4 cols per row to avoid crowding
                for idx, c_name in enumerate(selected_classes):
                    col = cols[idx % 4]
                    with col:
                        available_tickers = ASSET_POOLS[c_name]
                        selected_tickers = st.multiselect(
                            f"{c_name} Assets",
                            options=available_tickers,
                            default=available_tickers[:10],
                            format_func=get_asset_name,
                            key=f"ms_univ_{c_name}"
                        )
                        # Overwrite with specific selection
                        if selected_tickers:
                            universe_dict[c_name] = selected_tickers
                        else:
                            # If they explicitly clear the box, remove the class from the dictionary
                            if c_name in universe_dict:
                                del universe_dict[c_name]

    st.markdown("---")
    # --- LAUNCH CONTROLS ---
    col_run1, col_run2 = st.columns(2)
    with col_run1:
        use_hedge = st.toggle("Beta Hedge (Short SPY to offset continuous market risk)", value=True)
    with col_run2:
        btn_run = st.button("RUN BACKTEST", use_container_width=True, type="primary")

# --- EXECUTION LOGIC ---
if btn_run or st.session_state.run_trigger:
    st.session_state.run_trigger = False
    current_threshold = st.session_state.shared_corr_threshold
    
    with st.spinner(f"Fetching Market Data & Running Simulation"):
        try:
            # Universe Construction is now already handled in the expander UI
            # We just use universe_dict which was built locally in this function
            if not universe_dict:
                st.error("Please select at least one asset in the Custom Universe Selection.")
                st.stop()
                
            # Flatten the dictionary values into a unique set of tickers to minimize API calls.
            # We explicitly add 'SPY' as it is required for Beta hedging and potential benchmark comparisons.
            all_tickers = list(set([t for sublist in universe_dict.values() for t in sublist] + ['SPY']))
            
            # Fetch 2 extra years of historical data to allow for 
            # signal lookback periods (e.g. 200-day moving average computation)
            data_start = start_date - datetime.timedelta(days=365*2) 
            data_end = datetime.date.today()
            
            if 'market_data' in st.session_state and st.session_state.market_data is not None:
                market_df = st.session_state.market_data
            else:
                market_df, meta = MarketData.get_clean_multiticker_data(all_tickers, data_start, data_end)
            
            if market_df is None or market_df.empty:
                st.error("No data fetched. Please check tickers or internet connection.")
            else:
                # Initialization of the Vectorized Backtesting Engine
                # The engine requires the pre-fetched DataFrame (market_df) and the structured universe.
                engine = BacktestEngine(market_df, universe_dict, initial_capital=100000)
                sim_start = pd.Timestamp(start_date)
                
                # Core Simulation Execution
                # The engine iterates through rebalancing dates (e.g., end of month).
                # At each step, it:
                #   a. Computes momentum signals (using Lookback window)
                #   b. Validates correlation (using Corr_Lookback window)
                #   c. Selects Top N assets per class
                #   d. Allocates capital (Risk Parity or Equal Weight)
                #   e. Calculates dynamic Beta and applies Hedge (if active)
                results = engine.run(
                    start_date=sim_start,
                    freq=rebal_freq,
                    signal_method=selected_signal,
                    top_n=top_n, 
                    hedge_on=use_hedge,
                    lookback=126, 
                    corr_threshold=current_threshold,
                    corr_lookback=CORR_LOOKBACK_WINDOW
                )
                
                bench_series = None
                bench_name = ""
            
                if selected_benchmark == "SPY (S&P 500)":
                    # Cap-weighted standard benchmark
                    bench_name = "SPY"
                    if isinstance(market_df.columns, pd.MultiIndex):
                        if 'Adj Close' in market_df.columns and 'SPY' in market_df['Adj Close'].columns:
                            bench_series = market_df['Adj Close']['SPY']
                        elif 'SPY' in market_df.columns:
                             bench_series = market_df['SPY']
                    else:
                        bench_series = market_df['SPY'] if 'SPY' in market_df.columns else market_df.iloc[:, 0]
            
                elif selected_benchmark == "Risk Parity (Multi-Asset)":
                    # Smart-beta benchmark that weights assets inversely to their volatility
                    # Ensures a fairer comparison for a multi-asset strategy
                    bench_name = "Risk Parity Index"
                    with st.spinner("Calculating Risk Parity Benchmark..."):
                        bench_series = engine.run_risk_parity_benchmark(start_date=sim_start)
                        
            with st.expander("About the Benchmarks"):
                st.markdown("""
                **SPY (S&P 500):** The standard US market index. Very aggressive (100% Equities).
                
                **Risk Parity (Multi-Asset):** A custom benchmark constructed from your selected universe. Instead of weighting assets by Market Cap (like SPY), it weights them by **Inverse Volatility**. 
                - Safe assets (Bonds) get higher weights. 
                - Risky assets (Tech Stocks) get lower weights.
                - *Goal:* Equal risk contribution from every asset class.
                """)
            
                st.session_state.backtest_results = results
                st.session_state.benchmark_data = bench_series
                st.session_state.benchmark_name = bench_name
                st.session_state.market_data = market_df 

                st.session_state.params = {
                    "univ": "Custom",
                    "universe_dict": universe_dict,
                    "signal": selected_signal,
                    "hedge": use_hedge,
                    "top_n": top_n,
                    "corr_threshold": current_threshold
                }
                
        except Exception as e:
            st.error(f"Critical Error during execution: {e}")

# --- TABS DISPLAY ---
selected_tab = st.radio("Navigation", [
    " Overview & Performance", 
    " Asset Allocation", 
    " Signals & Selection", 
    " Risk & Hedge"
], horizontal=True, label_visibility="collapsed")

# ==============================================================================
# TAB 1: OVERVIEW & PERFORMANCE
# ==============================================================================
if selected_tab == " Overview & Performance":
    if st.session_state.backtest_results is not None:
        results_dict = st.session_state.backtest_results
        nav_series = results_dict['NAV'] # Historical Net Asset Value vector
        bench_data = st.session_state.benchmark_data
        bench_label = st.session_state.get('benchmark_name', 'Benchmark') 
        
        # KPI Generation
        # Compares the Strategy NAV vector against the Benchmark price/return vector
        # Returns a formatted DataFrame with CAGR, Volatility, Sharpe, Drawdown, etc.
        kpi_df = analytics.calculate_kpis(nav_series, bench_data, benchmark_label=bench_label)
        
        def get_val(metric): return kpi_df.loc[kpi_df['Metric'] == metric, 'Strategy'].values[0]
        def get_delta(metric): return kpi_df.loc[kpi_df['Metric'] == metric, 'Alpha (Diff)'].values[0]

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric("Total Return", get_val("Total Return"), get_delta("Total Return"))
        m2.metric("Annual Average", get_val("CAGR"), get_delta("CAGR"))
        m3.metric("Sharpe Ratio", get_val("Sharpe Ratio"), get_delta("Sharpe Ratio"))
        m4.metric("Volatility", get_val("Annual Volatility"), get_delta("Annual Volatility"), delta_color="inverse")
        m5.metric("Max Drawdown", get_val("Max Drawdown"), get_delta("Max Drawdown"), help="The maximum observed loss between two peaks (indicator of downside risk)")
        m6.metric("Calmar Ratio", get_val("Calmar Ratio"), get_delta("Calmar Ratio"), help="(Annual Average Return / Max Drawdown). Higher is better.")

        st.markdown("---")
        
        col_g1, col_g2 = st.columns([3, 2])
        
        with col_g1:
            st.subheader(f"Equity Curve vs {bench_label}") 
            fig_equity = analytics.plot_equity_curve(nav_series, bench_data, benchmark_ticker=bench_label)
            st.plotly_chart(fig_equity, use_container_width=True)
            
            st.subheader("Rolling 6-Month Sharpe Ratio")
            fig_sharpe = analytics.plot_rolling_sharpe(nav_series, bench_data, benchmark_label=bench_label)
            st.plotly_chart(fig_sharpe, use_container_width=True)

        with col_g2:
            st.subheader("Risk Profile Comparison")
            fig_dist = analytics.plot_returns_distribution(nav_series, bench_data, benchmark_label=bench_label)
            st.plotly_chart(fig_dist, use_container_width=True)
            
            with st.expander("How to interpret the Risk Profile (Distribution)?"):
                st.markdown("""
                This chart visualizes the "personality" of the returns compared to the Benchmark.
        
                * **The Peak (Mean/Avg):** We want the Green curve's peak to be **shifted to the right** of the Red curve. This indicates higher average returns.
                * **The Width (Volatility):** We want a **narrower, taller** Green curve. A wide, flat curve means erratic performance and uncertainty.
                * **Skewness (Crash Risk):** The market often has a "long left tail" (negative skew), meaning it crashes fast. We want your Strategy to have a **higher Skewness**, indicating fewer sudden catastrophic losses.
                * **Kurtosis (Fat Tails):** Lower is generally better. High kurtosis means extreme events (Black Swans) happen more frequently.
                """)
            
            st.subheader("Drawdown Comparison")
            fig_dd = analytics.plot_drawdown_underwater(nav_series, bench_data, benchmark_label=bench_label)
            st.plotly_chart(fig_dd, use_container_width=True)

        st.markdown("---")
        st.subheader("Alpha Proof: Can you beat the market?")
    
        if bench_data is not None and not bench_data.empty:
            col_alpha1, col_alpha2 = st.columns(2)
        
            with col_alpha1:
                fig_full = analytics.plot_alpha_beta_scatter(nav_series, bench_data, view_mode='full')
                if fig_full: st.plotly_chart(fig_full, use_container_width=True)
                else: st.info("Insufficient data.")
                
            with col_alpha2:
                fig_zoom = analytics.plot_alpha_beta_scatter(nav_series, bench_data, view_mode='zoomed')
                if fig_zoom: st.plotly_chart(fig_zoom, use_container_width=True)
        else:
            st.warning("Please verify that a Benchmark is selected.")

        with st.expander("Understanding CAPM & Alpha Generation"):
            st.markdown("""
            We use the **Capital Asset Pricing Model (CAPM)** to isolate your "True Skill" (Alpha) from "Market Luck" (Beta).
        
            $$R_{Strategy} = \\alpha + \\beta \\times R_{Benchmark} + \\epsilon$$
        
            * **The Intercept ($\\alpha$):** Look at where the red line crosses the vertical axis.
                * **Above 0: Positive Alpha.** You generate excess returns that cannot be explained by market movements. You are adding value.
                * **Below 0: Negative Alpha.** You are underperforming the risk you are taking.
            * **The Slope ($\\beta$):** 
                * **< 1.0:** Defensive profile (less volatile than the market).
                * **> 1.0:** Aggressive profile (amplifies market moves).
            """)

        with st.expander("View Detailed Performance Table"):
            st.dataframe(kpi_df, use_container_width=True)

    else:
        st.info("Please configure the strategy in the top panel and click 'RUN BACKTEST'.")

# ==============================================================================
# TAB 2: ASSET ALLOCATION
# ==============================================================================
if selected_tab == " Asset Allocation":
    if st.session_state.backtest_results is not None:
        results_dict = st.session_state.backtest_results
        weights_df = results_dict['Weights']
        nav_series = results_dict['NAV']
        market_df = st.session_state.get('market_data', None)
        
        univ_preset = st.session_state.params.get("univ", "Custom")
        # To avoid failure if the user is looking at historical run:
        if st.session_state.run_trigger or btn_run:
            pass # We should be using the currently fetched one or storing it.
        # Wait, if we use universe_dict later in tab 2... we need to save the universe_dict used in the run into session_state!
        # Let's fix that below. For now, since Tab2 relies on the dictionary, we should pull it from session_state where we will save it.
        universe_dict = st.session_state.params.get("universe_dict", ASSET_POOLS)
        
        # Historical Allocation Evolution (Area Chart)
        # Displays the continuous weight of each asset class over time.
        # This confirms that the Risk Parity logic correctly redistributes weights during volatile periods.
        st.markdown("### Historical Allocation Evolution")
        fig_alloc = analytics.plot_dynamic_allocation(weights_df, universe_dict)
        st.plotly_chart(fig_alloc, use_container_width=True)
        
        with st.expander("Understanding the Allocation Evolution"):
            st.markdown("""
            This area chart displays the continuous weight of each asset class over time. 
            It highlights how the **Risk Parity** weighting correctly redistributes allocations during volatile periods, dynamically shifting exposure between Equities, Bonds, and Commodities based on inverse volatility and momentum stability.
            """)
        
        # Asset Rotation Heatmap
        # A chronological matrix showing the Top N largest individual positions.
        # Useful for visualizing how the algorithm rotates out of underperforming assets (e.g. pivoting from Tech to Bonds).
        st.markdown("### Asset Rotation & Attribution")
        fig_heatmap = analytics.plot_asset_rotation_heatmap(weights_df, top_n_display=12)
        st.plotly_chart(fig_heatmap, use_container_width=True)
        
        with st.expander("Understanding Asset Rotation"):
            st.markdown("""
            The **Heatmap** acts as a chronological matrix highlighting the historically largest individual positions. It visually confirms how the algorithm aggressively rotates out of underperforming assets (e.g., pivoting seamlessly from Tech to Safe-Haven Bonds just before a major Equity drawdown).
            """)

        st.caption("What drove the monthly returns? (Weighted Contribution by Asset Class)")
        if market_df is not None:
            fig_contrib = analytics.plot_monthly_contribution(weights_df, market_df, universe_dict)
            st.plotly_chart(fig_contrib, use_container_width=True)
            
            with st.expander("Understanding Monthly Contribution"):
                st.markdown("""
                This bar chart breaks down the total historical monthly performance, isolating the exact **P&L contribution** of each asset class. It allows us to verify if a positive month was driven by Equity momentum or by the protective mechanism of Bond hedging.
                """)
        else:
            st.warning("Market data missing for attribution analysis. Please re-run the backtest.")

        st.markdown("---")
        st.markdown("### Historical Portfolio Inspector")
        
        min_date = weights_df.index[0].date()
        max_date = weights_df.index[-1].date()
        
        col_input, col_void = st.columns([1, 3])
        with col_input:
            target_date = st.date_input("Select a specific date to inspect:", value=max_date, min_value=min_date, max_value=max_date)

        try:
            target_ts = pd.Timestamp(target_date)
            idx_pos = weights_df.index.get_indexer([target_ts], method='pad')[0]
            
            if idx_pos == -1: st.warning("Date selected is before the start of the simulation.")
            else:
                # Create a snapshot for the chosen date
                snapshot_weights = weights_df.iloc[idx_pos]
                snapshot_nav = nav_series.iloc[idx_pos]

                # Combine the asset weights and the total NAV to display monetary values ($)
                snapshot_combined = snapshot_weights.copy()
                snapshot_combined['NAV'] = snapshot_nav
                display_date = weights_df.index[idx_pos]

            col_b1, col_b2 = st.columns([1, 2])
            
            with col_b1:
                fig_pie = analytics.plot_allocation_donut(snapshot_combined)
                st.plotly_chart(fig_pie, use_container_width=True)
                
            with col_b2:
                st.subheader(f"Holdings on {display_date.strftime('%Y-%m-%d')}")
                holdings_df = analytics.get_holdings_table(snapshot_combined, universe_dict)
                
                st.dataframe(
                    holdings_df,
                    column_config={
                        "Asset": st.column_config.TextColumn("Asset"),
                        "Class": st.column_config.TextColumn("Class"),
                        "Weight": st.column_config.ProgressColumn("Weight", format="%.2f%%", min_value=0, max_value=1),
                        "Value ($)": st.column_config.NumberColumn("Value ($)", format="$%d")
                    },
                    use_container_width=True, hide_index=True, height=300
                )

        except Exception as e:
            st.error(f"Could not retrieve data for this date: {e}")
    else:
        st.info("Please configure the strategy in the top panel and click 'RUN BACKTEST'.")

# ==============================================================================
# TAB 3: SIGNALS & SELECTION
# ==============================================================================
if selected_tab == " Signals & Selection":
    market_df = st.session_state.get('market_data', None)
    results_dict = st.session_state.get('backtest_results', {})
    
    if market_df is not None:
        params = st.session_state.get('params', {})
        used_signal = params.get("signal", "z_score")
        lookback_period = 126 
                
        # Compute Momentum Signals
        # Calculates metrics (Z-Score, RSI, Distance to MA) for all assets over the historical market_df
        with st.spinner(f"Computing historical {used_signal} values..."):
            signals_df = analytics.calculate_all_signals(market_df, used_signal, lookback=lookback_period)
        
        # Signal Evolution (The Race)
        # Visualizes the continuous trajectory of momentum scores over time
        st.markdown("### Signal Evolution (The Race)")
        st.caption("Spotlight View: Select assets to compare. Others remain gray for context.")
        
        all_tickers = list(signals_df.columns)
        default_selection = all_tickers[:5] if len(all_tickers) > 5 else all_tickers
        
        selected_tickers = st.multiselect(
            "Select Assets to Highlight:", options=all_tickers, default=default_selection,
            format_func=get_asset_name, key="signal_race_multiselect"
        )
        
        fig_race = analytics.plot_signal_race(signals_df, highlight_assets=selected_tickers, signal_method=used_signal)
        st.plotly_chart(fig_race, use_container_width=True)
        
        with st.expander("About Signal Evolution & Momentum"):
            st.markdown("""
            This chart visualizes the underlying momentum metrics powering the allocation engine.
            
            * **Z-Score:** Measures how far an asset's price is from its recent historical average, normalized by its volatility. High Z-Scores indicate strong recent outperformance.
            * **Distance to MA:** A classic trend-following metric. The percentage difference between the current price and a long-term moving average (e.g., 200-day).
            * **RSI (Relative Strength Index):** A momentum oscillator measuring the speed and change of price movements on a scale of 0 to 100.
            
            **The Race:** Watch for regime changes—for example, when Energy (Commodities) lines cross above Tech (Equities) lines, the algorithm rotate capital away from Tech.
            """)
        st.markdown("---")
        
        st.markdown("### Ranking Snapshot")
        min_date = signals_df.index[0].date()
        max_date = signals_df.index[-1].date()
        
        col_date, col_void = st.columns([1, 3])
        with col_date:
            target_date_sig = st.date_input(
                "Select date to inspect ranking:", value=max_date, min_value=min_date, max_value=max_date, key="signal_snapshot_date_picker"
            )

        ts = pd.Timestamp(target_date_sig)
        chosen_tickers_for_date = []
        selections_history = results_dict.get('Selections', {})
        if selections_history:
            rebalance_dates = pd.DatetimeIndex(selections_history.keys()).sort_values()
            past_dates = rebalance_dates[rebalance_dates <= ts]
            if not past_dates.empty: chosen_tickers_for_date = selections_history[past_dates[-1]]

        try:
            # Isolate the specific date's signal vector
            # We use loc[:ts].iloc[-1] to get the most recently available signals on or before the target date
            current_signals = signals_df.loc[:ts].iloc[-1].dropna()
            # Rank from strongest positive momentum to weakest
            full_ranking = current_signals.sort_values(ascending=False)
        except Exception:
            full_ranking = pd.Series()

        if not full_ranking.empty:
            st.markdown("---")
            st.subheader("Asset Class Analysis")
            
            thresh = st.slider("Correlation Alert Threshold", min_value=0.5, max_value=0.99, step=0.05, key="slider_bottom_key", on_change=update_corr_from_bottom)
            current_thresh = st.session_state.shared_corr_threshold

            # Dynamically create tabs according to classes actually selected
            all_classes_in_run = list(st.session_state.params.get("universe_dict", ASSET_POOLS).keys())
            tabs_classes = st.tabs(["All"] + all_classes_in_run)
            
            # Use dynamic filters based on the explicit TICKER_TO_CATEGORY mapping
            for idx, tab in enumerate(tabs_classes):
                with tab:
                    if idx == 0:
                        cat_name = "All"
                        filter_func = lambda t: True
                    else:
                        cat_name = all_classes_in_run[idx - 1]
                        # Use default argument binding to prevent late-binding closure bugs
                        def make_filter(c): 
                            return lambda t: universe.get_asset_class(t) == c
                        filter_func = make_filter(cat_name)
                        
                    filtered_tickers = [t for t in full_ranking.index if filter_func(t)]
                    
                    if not filtered_tickers:
                        st.info(f"No assets found for class: {cat_name} in current selection.")
                        continue
                        
                    subset_ranking = full_ranking[filtered_tickers]
                    subset_ranking_df = subset_ranking.to_frame(name='Score')

                    col_rank, col_matrix = st.columns([2, 1])
                    
                    with col_rank:
                        st.markdown(f"**{cat_name} Signals**")
                        subset_selected = [t for t in chosen_tickers_for_date if t in filtered_tickers]
                        temp_signals_df = pd.DataFrame(index=[ts], data=[subset_ranking.to_dict()])
                        
                        fig_rank = analytics.plot_signal_ranking_bar(temp_signals_df, target_date=ts, actual_selections=subset_selected)
                        st.plotly_chart(fig_rank, use_container_width=True, key=f"rank_{cat_name}")
                        
                        with st.expander("Selection Logic (Top N)"):
                            st.markdown(f"""
                            For this Asset Class, the algorithm evaluates the highest momentum scores:
                            
                            * **Top N Parameter:** The strategy attempts to buy the top `{top_n}` assets shown in this bar chart.
                            * **Momentum Filter:** If all scores are negative, the algorithm buys nothing and goes to Cash (Capital Preservation).
                            * **Correlation Override:** If the #2 asset is highly correlated to the #1 asset, the algorithm skips #2 and buys #3 instead to ensure diversification. 
                            """)

                    with col_matrix:
                        st.markdown(f"**{cat_name} Correlation**")
                        if len(filtered_tickers) < 2:
                            st.caption("Need at least 2 assets to calculate correlation.")
                        else:
                            if market_df is not None:
                                fig_corr = analytics.plot_correlation_matrix(market_df, subset_ranking_df, threshold=current_thresh, window=CORR_LOOKBACK_WINDOW)
                                if fig_corr: st.plotly_chart(fig_corr, use_container_width=True, key=f"corr_{cat_name}")
                                
                        with st.expander("Diversification & Correlation Filter"):
                            st.markdown(f"""
                            This matrix visualizes the correlation over the last {CORR_LOOKBACK_WINDOW} days. It prevents buying duplicates (e.g., buying 3 highly correlated Tech ETFs).
                            
                            * **Current Threshold: {current_thresh}**
                            * **Red Cells:** High correlation (> Threshold). The algorithm will pick the strongest momentum asset and discard the others.
                            * **White Cells:** Low correlation. These assets provide true diversification benefit.
                            """)

        st.markdown("---")
        st.markdown("### Signal vs Price Deep Dive")
        st.caption("Validate the signal effectiveness. Does the price react when the signal spikes?")
        
        deep_dive_default = selected_tickers[0] if selected_tickers else all_tickers[0]

        target_asset = st.selectbox(
            "Select Single Asset to Inspect:", options=all_tickers, index=all_tickers.index(deep_dive_default) if deep_dive_default in all_tickers else 0,
            format_func=get_asset_name, key="deep_dive_asset_selector"
        )
        
        if target_asset:
            fig_deep = analytics.plot_signal_vs_price(market_df, signals_df, target_asset)
            st.plotly_chart(fig_deep, use_container_width=True)
            
            with st.expander("Analysis: Signal vs Price Action"):
                st.markdown("""
                This chart allows you to verify the algorithm's reactivity:
                * **Blue Line (Score):** Represents the calculated momentum.
                * **Black Line (Price):** The asset price.
                
                **What to look for:**
                * **Leading Indicator:** Does the score turn positive *before* a major rally?
                * **Lag:** Does the score take too long to turn red during a crash?
                * **Noise:** If the score flickers around 0 frequently, it generates false signals (whipsaws).
                """)

    else:
        st.warning("No data found. Please go to the Overview tab and click 'RUN BACKTEST' first.")

# ==============================================================================
# TAB 4: RISK & HEDGE
# ==============================================================================
if selected_tab == " Risk & Hedge":
    results_dict = st.session_state.get('backtest_results', None)
    market_df = st.session_state.get('market_data', None)

    if results_dict is not None and market_df is not None:
        weights_df = results_dict.get('Weights')
        hedge_series = results_dict.get('Hedge Ratio')

        st.markdown("### Portfolio Protection Analysis")
        
        if hedge_series is not None and not hedge_series.empty and hedge_series.abs().sum() != 0:
            # Hedge Activation Plot (Ratio)
            # Area chart showing the required short position (0% to 100% of portfolio value)
            st.markdown("#### Hedge Activation")
            st.caption("This chart shows when the algorithm decided to protect the portfolio and with what intensity.")
            
            fig_ratio = analytics.plot_hedge_ratio(hedge_series)
            st.plotly_chart(fig_ratio, use_container_width=True, key="chart_hedge_activation")
            
            col_h1, col_h2 = st.columns([4,1])
            
            with col_h1:
                # Financial Impact Plot (Hedge PnL)
                # Calculates the cash generated or lost by the short SPY position.
                st.markdown("#### Hedge Financial Impact")
                st.caption("Cumulative profit or loss from the short position.")
                
                fig_impact = analytics.plot_hedge_impact(hedge_series, market_df)
                st.plotly_chart(fig_impact, use_container_width=True, key="chart_hedge_impact")
                
            with col_h2:
                # Hedge KPI summary
                avg_hedge = hedge_series.abs().mean()
                max_hedge = hedge_series.abs().max()
                
                st.markdown("#### Protection Statistics")
                st.metric("Average Hedge Level", f"{avg_hedge:.1%}")
                st.metric("Peak Protection", f"{max_hedge:.1%}")
                
            with st.expander("Beta Hedge Logic"):
                st.markdown(f"""
                The hedging engine dynamically calculates the aggregate Beta (correlation $\\times$ volatility) of your selected assets relative to the Benchmark (SPY).
                
                * **If Portfolio Beta = 0.8:** The app automatically shorts an equivalent 80% worth of SPY.
                * **Result:** The directional market risk is offset. If the market drops, the short position generates profit (Hedge PnL) to cushion the losses in the long portfolio.
                """)

        else:
            st.warning("Hedging was disabled or inactive for this backtest run.")
            
    else:
        st.info("Please run a backtest with 'Beta Hedge' enabled to see this analysis.")