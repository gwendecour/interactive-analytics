import streamlit as st
from src.shared.ui import render_header

# --- PAGE CONFIGURATION ---
st.set_page_config(
    page_title="Home",
    page_icon="assets/logo.png",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- HEADER IMPORT ---
render_header()

# --- DYNAMIC THEME CSS ---
theme = st.session_state.get('theme', 'dark')

# Define theme colors
if theme == 'dark':
    bg_color = "#0e1117"
    text_color = "#e0e0e0"
    header_color = "#ffffff"
    card_bg = "#161a22"
    card_border = "#333333"
    btn_sec_bg = "#262730"
    btn_sec_text = "#fafafa"
    btn_sec_border = "#4a4a4a"
    btn_sec_hover_bg = "#3b3d4a"
    btn_sec_hover_border = "#707070"
    btn_sec_hover_text = "#ffffff"
else:
    bg_color = "#ffffff"
    text_color = "#4a4a4a"
    header_color = "#1a1a1a"
    card_bg = "#ffffff"
    card_border = "#f0f0f0"
    btn_sec_bg = "#f0f2f6"
    btn_sec_text = "#31333F"
    btn_sec_border = "#d0d0d0"
    btn_sec_hover_bg = "#e0e2e6"
    btn_sec_hover_border = "#b0b0b0"
    btn_sec_hover_text = "#000000"

st.markdown(f"""
<style>
    /* Import 'Lora' font (Academic/Finance style) */
    @import url('https://fonts.googleapis.com/css2?family=Lora:ital,wght@0,400;0,600;1,400&family=Inter:wght@400;600&display=swap');

    /* Apply font to headers */
    h1, h2, h3, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {{
        font-family: 'Lora', serif !important;
        color: {header_color};
    }}
    
    /* Apply clean font to text */
    p, .stMarkdown, .stText {{
        font-family: 'Inter', sans-serif !important;
        color: {text_color};
        line-height: 1.6;
    }}

    /* --- BUTTON STYLES --- */
    
    /* 1. "EXPLORE" Buttons (Primary Type) -> FINANCE GREEN + WHITE TEXT */
    div.stButton > button[kind="primary"],
    div.stButton > button[kind="primary"] * {{
        background-color: #2e7d32 !important; 
        color: #ffffff !important;            /* FORCE WHITE GLOBALLY */
        fill: #ffffff !important;             /* FORCE WHITE FOR ICONS IF PRESENT */
        border: none !important;
    }}

    /* Hover State Management */
    div.stButton > button[kind="primary"]:hover,
    div.stButton > button[kind="primary"]:hover * {{
        background-color: #1b5e20 !important;
        color: #ffffff !important;
    }}
    
    /* Force white color even if button is active/clicked */
    div.stButton > button[kind="primary"]:active, 
    div.stButton > button[kind="primary"]:focus {{
        color: #ffffff !important;
        background-color: #1b5e20 !important;
    }}

    /* 2. "METHODOLOGY" Buttons (Secondary/Default Type) */
    div.stButton > button[kind="secondary"] {{
        background-color: {btn_sec_bg} !important;
        color: {btn_sec_text} !important;
        border: 1px solid {btn_sec_border} !important;
        font-weight: 500 !important;
        border-radius: 6px;
        transition: all 0.2s ease;
    }}
    div.stButton > button[kind="secondary"]:hover {{
        background-color: {btn_sec_hover_bg} !important;
        border-color: {btn_sec_hover_border} !important;
        color: {btn_sec_hover_text} !important;
    }}
    
    /* Card Styles (Containers) */
    [data-testid="stVerticalBlock"] > [style*="flex-direction: column;"] > [data-testid="stVerticalBlock"] {{
        background-color: {card_bg};
        padding-bottom: 10px;
        border-radius: 8px;
        border: 1px solid {card_border};
    }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# MODAL CONTENT (METHODOLOGY)
# ==============================================================================

story_p1 = r"""
### Strategic Objective
The objective of the **Derivatives Pricing & Hedging** engine is to bridge the gap between theoretical valuation models and industrial trading reality. It provides a robust framework to price, risk-manage, and backtest hedging strategies for both **Vanilla Options** (European Calls/Puts) and **Path-Dependent Structured Products** (Phoenix Autocalls), simulating the daily workflow of an Equity Derivatives desk.

### Pricing Models & Architecture
The engine selects the appropriate valuation method based on the product's complexity:
* **Vanilla Options (Closed-Form):** For European options where the payoff depends solely on $S_T$, we utilize the analytical **Black-Scholes-Merton** formula for instant precision.
$$
C(S,t) = S e^{-qT} N(d_1) - K e^{-rT} N(d_2)
$$
* **Exotic Products (Monte Carlo):** For Phoenix Autocalls, where the payoff is **path-dependent** (barriers are monitored daily/quarterly), we employ a **Monte Carlo Simulation** engine.
    * **Diffusion Process:** We simulate $N$ paths (default $2,000 - 10,000$) using Geometric Brownian Motion (GBM):
    $$ dS_t = (r - q) S_t dt + \sigma S_t dW_t $$
    * **Pricing:** The price is the discounted expectation of the payoff under the risk-neutral measure $\mathbb{Q}$:
    $$ P_0 = e^{-rT} \times \frac{1}{N} \sum_{i=1}^{N} \text{Payoff}(Path_i) $$



### Structured Product Logic (Phoenix Autocall)
The Phoenix is a yield enhancement product defined by three barriers observed at discrete frequencies:
* **Coupon Barrier ($B_{cpn}$):** If $S_t \ge B_{cpn}$, a coupon is paid (Memory effect applies if missed previously).
* **Autocall Barrier ($B_{auto}$):** If $S_t \ge B_{auto}$, the product is redeemed early at Nominal + Coupon.
* **Protection Barrier ($B_{prot}$):** At maturity, if $S_T < B_{prot}$ (and never autocalled), the investor is short a Put option and suffers a capital loss:
$$ \text{Loss} = \text{Nominal} \times \frac{S_T - S_0}{S_0} $$



### Sensitivity Analysis (Numerical Greeks)
Since Exotic products possess discontinuous payoffs with no closed-form derivatives, we calculate sensitivities (Greeks) using **Finite Differences** ("Bump & Revalue"):
* **Delta ($\Delta$):** Sensitivity to Spot. Calculated via **Central Difference** for stability:
$$ \Delta \approx \frac{P(S+\epsilon) - P(S-\epsilon)}{2\epsilon} $$
* **Gamma ($\Gamma$):** Sensitivity to Delta (Convexity). Crucial for hedging frequency:
$$ \Gamma \approx \frac{P(S+\epsilon) - 2P(S) + P(S-\epsilon)}{\epsilon^2} $$
* **Vega ($\nu$):** Sensitivity to Volatility. Calculated via Forward Difference:
$$ \nu \approx P(\sigma + 1\%) - P(\sigma) $$

### Dynamic Hedging Backtest
The module simulates a **Short Volatility** position (Bank selling the option) and manages the Delta-Hedge daily until maturity:
* **Hedge Rebalancing:** At each step $t$, the engine calculates the new $\Delta_t$ and adjusts the inventory of the underlying asset to remain Delta Neutral.
* **Gamma Scalping:** The trading P&L is generated by the mechanical process of "Buying Low / Selling High" (Short Gamma) or vice-versa.
* **P&L Attribution:** The final performance is decomposed into:
    * **Cost of Carry:** Hedge Cost vs Theta (Time Decay).
    * **Vol Spread:** The difference between **Implied Volatility** (priced at inception) and **Realized Volatility** (market reality).
$$ P\&L_{Net} = \text{Premium} - \text{Payout} + \sum (\text{Trading P\&L}) - \text{Costs} $$
"""
story_p2 = r"""
### Strategic Objective
The goal of the **AlphaTrend** strategy is to generate **Absolute Returns (Alpha)** that are uncorrelated with the broader equity market (S&P 500). It simulates a "Quantitative Macro" desk approach by capturing strong trends across diverse asset classes (Equities, Bonds, Commodities) while dynamically hedging systematic market risk.

### Investment Universe
The strategy operates on a liquid, multi-asset universe composed of ETFs representing distinct economic factors:
* **Equities:** `SPY` (Large Cap), `QQQ` (Tech), `IWM` (Small Cap), `XLE` (Energy), `XLF` (Financials)...
* **Fixed Income:** `TLT` (20y+ Treasuries), `IEF` (7-10y Treasuries), `LQD` (Corp Bonds), `TIP` (Inflation-Protected)...
* **Commodities:** `GLD` (Gold), `USO` (Oil), `DBA` (Agriculture)...

### Signal Generation (Alpha Engine)
The strategy evaluates assets using one of three user-selectable momentum methodologies calculated on a rolling lookback window (default $L=126$ days):
* **Risk-Adjusted Momentum (Z-Score) [Default]:** Normalizes returns by their volatility to favor smooth trends.
$$
Score_t = \frac{R_{t, t-L}}{\sigma_{t} \times \sqrt{252}}
$$
* **Distance to Moving Average:** Measures price extension relative to its long-term trend.
$$
Score_t = \frac{P_t}{MA_L(P)} - 1
$$
* **Relative Strength Index (RSI):** Measures the velocity and magnitude of directional price movements.

### Portfolio Construction & Selection Logic
AlphaTrend employs a **Greedy Decorrelation Algorithm** to prevent concentration risk:
* **Regime Filter:** Assets with a **Negative Score** are strictly rejected. If no assets qualify, the strategy allocates to **CASH** (Capital Preservation).
* **Greedy Selection:** Assets are ranked by Score. The best asset is selected first. Subsequent assets are added **only if** their correlation with existing selections is below the `Corr_Threshold` (e.g., 0.6).
* **Weighting Scheme:** Weights are assigned based on **Inverse Volatility** (Risk Parity) between asset classes to balance risk contribution.

### Risk Management & Hedging
To isolate Alpha, the strategy neutralizes its exposure to the market factor (Beta):
* **Beta Calculation:** The portfolio's weighted Beta ($\beta_{port}$) relative to the S&P 500 is calculated dynamically.
* **Dynamic Hedging:** A short position in `SPY` is taken to offset systematic risk:
$$
Hedge_{Size} = - (\beta_{port} \times Portfolio_{NAV})
$$
* **Net Exposure:** The goal is to maintain a **Net Beta $\approx 0$**, ensuring performance is driven by asset selection rather than market direction.

### Key Performance Metrics
* **Alpha ($\alpha$):** The intercept of the regression vs. SPY. Must be positive.
* **Sharpe & Calmar Ratios:** Measures of risk-adjusted return and drawdown resilience.
* **Skewness:** Targeting positive skewness (limiting tail risk).
"""

story_p3 = r"""
### Strategic Objective
In quantitative asset management, optimizing a portfolio relies heavily on the **Covariance Matrix** ($\Sigma$) of asset returns. However, financial datasets are rarely perfect. Illiquid assets (like Corporate Bonds or Small Cap Equities) frequently suffer from **missing data** (stale prices or non-trading days). 
The objective of this research module is to demonstrate how naive imputation methods mathematically destroy the covariance structure and lead to suboptimal, risky allocations, and to compare advanced algorithmic methods that recover the true hidden market dynamics.

### The Dangers of Naive Imputation (Forward Fill)
The industry standard often defaults to **Forward Fill** (carrying the last known price forward). While simple, it severely distorts the statistical properties of the asset:
*   **Volatility Collapse:** Since the price doesn't change on missing days, $R_t = \ln(P_t/P_{t-1}) \approx 0$. This artificially deflates the asset's standard deviation ($\sigma$).
*   **Covariance Destruction:** Returns of the illiquid asset become $0$ exactly when the broader market is moving, destroying the cross-asset correlation:
    $$ Cov(R_{illiquid}, R_{market}) \to 0 $$
*   **Portfolio Illusion:** Mean-Variance optimizers love low-volatility, uncorrelated assets. The optimizer will massively overweight the illiquid asset, mistakenly believing it to be a perfect "safe haven," exposing the fund to massive hidden risk (Volatility Illusion).

### Advanced Imputation Methodologies
To properly recover the covariance matrix, we explore and compare four algorithmic approaches:

#### 1. K-Nearest Neighbors (KNN)
KNN relies on cross-sectional similarity. For a missing return on day $t$ for asset $i$, it identifies the $K$ "closest" assets (based on historical correlation) that *do* have data on day $t$.
$$ \hat{R}_{i,t} = \sum_{j \in K} w_j R_{j,t} \quad \text{where } w_j \propto \text{Similarity}(i, j) $$
*   **Pros:** Preserves cross-asset correlations well.
*   **Cons:** Struggles if the entire market segment is illiquid simultaneously.

#### 2. Singular Value Decomposition (SVD)
Financial markets are governed by a few dominant latent factors (e.g., Market, Sector, Duration). SVD exploits this low-rank structure via **Matrix Completion**.
The returns matrix $M$ is decomposed into $M \approx U \Sigma V^T$. The missing entries are iteratively updated using a truncated SVD (keeping only the top $k$ principal components).
*   **Pros:** Extremely powerful in capturing the macro "Market Beta" effect to fill the gaps.

#### 3. Multivariate Imputation by Chained Equations (MICE)
Originally from medical statistics, MICE is an iterative regression technique. It models each asset as a linear combination of all other assets.
$$ \hat{R}_{i,t} = \beta_0 + \beta_1 R_{1,t} + \beta_2 R_{2,t} + \dots + \beta_n R_{n,t} $$
It loops through all incomplete assets, updating their missing values conditionally based on the current best guesses of the other assets, until convergence.

#### 4. Expectation-Maximization (EM) Algorithm
The EM algorithm explicitly models the returns as drawn from a Multivariate Normal Distribution $N(\mu, \Sigma)$. It alternates between two steps until maximum likelihood is achieved:
*   **E-Step (Expectation):** Estimates the missing data given the observed data and current estimates of $\mu$ and $\Sigma$.
*   **M-Step (Maximization):** Recalculates $\mu$ and $\Sigma$ using the complete dataset (observed + expected).
*   **Pros:** Mathematically rigorous for estimating the Covariance Matrix directly.

### Performance Evaluation
The robustness of each method is evaluated both statistically and financially:
*   **Statistical Error (Frobenius Norm):** Measures the absolute distance between the recovered covariance matrix $\hat{\Sigma}$ and the Ground Truth $\Sigma_{true}$:
    $$ ||\Sigma_{true} - \hat{\Sigma}||_F = \sqrt{\sum_i \sum_j (\Sigma_{true, i,j} - \hat{\Sigma}_{i,j})^2} $$
*   **Financial Impact:** We simulate an Inverse Volatility (Risk Parity) portfolio using the distorted data and compare its **Tracking Error** and **Turnover Friction** against the theoretical optimal portfolio.
"""

# ==============================================================================
# DIALOG FUNCTION (POP-UP)
# ==============================================================================
@st.dialog("Methodology & Backstory")
def show_methodology(title, content):
    st.markdown(f"## {title}")
    st.markdown(content)
    st.markdown("---")
    st.caption("Decourchelle Quant Lab Research")

# ==============================================================================
# PAGE LAYOUT
# ==============================================================================

# --- MAIN TITLE ---
st.markdown("<h1 style='text-align: center; margin-bottom: 10px;'>Choose Your Project</h1>", unsafe_allow_html=True)

# --- DYNAMIC SUBTITLE ---
st.markdown(
    "<p style='text-align: center; margin-bottom: 50px; color: gray; font-size: 1.1rem;'>"
    "Every project is designed as an interactive educational experience: complex analytics are thoroughly explained in plain English, while intelligent caching and background pre-computation ensure a comfortable exploration."
    "</p>", 
    unsafe_allow_html=True
)

# --- PROJECT GRID ---
col1, col2, col3 = st.columns(3, gap="medium")

# --- CARD 1 : PRICING ---
with col1:
    with st.container(border=True):
        # CENTERED TITLE VIA HTML
        st.markdown("<h3 style='text-align: center;'>Derivatives Pricing</h3>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style="height: 130px; text-align: justify;">
        Advanced pricing engine for Vanilla and Structured Products (Phoenix Autocall). 
        Includes Monte Carlo simulations, full Greeks analysis, and Delta-Hedging backtesting simulations.
        </div>
        """, unsafe_allow_html=True)
        
        # SIDE-BY-SIDE BUTTONS
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            if st.button("Explore", key="btn_pricing", type="primary", use_container_width=True):
                st.switch_page("pages/01_Pricing&Hedging_Derivatives.py")
        with b_col2:
            if st.button("Methodology", key="story_p1", use_container_width=True):
                show_methodology("Pricing & Hedging Derivatives", story_p1)

# --- CARD 2 : ALPHATREND ---
with col2:
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center;'>AlphaTrend Strategy</h3>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style="height: 130px; text-align: justify;">
        Multi-Asset Trend Following strategy acting as a "Beta Neutral" desk.
        Features dynamic volatility targeting and automatic market beta neutralization (Long/Short).
        </div>
        """, unsafe_allow_html=True)
        
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            # Visually "Primary" Button (Green)
            if st.button("Explore", key="btn_invest", type="primary", use_container_width=True):
                st.switch_page("pages/02_AlphaTrend_Strategy.py")
        with b_col2:
            if st.button("Methodology", key="story_p2", use_container_width=True):
                show_methodology("AlphaTrend: Beta Neutral", story_p2)

# --- CARD 3 : ROBUST COVARIANCE ---
with col3:
    with st.container(border=True):
        st.markdown("<h3 style='text-align: center;'>Robust Covariance</h3>", unsafe_allow_html=True)
        
        st.markdown("""
        <div style="height: 130px; text-align: justify;">
        Quantitative research on Missing Data Imputation.
        Compare covariance matrix estimation techniques (KNN, SVD, MICE) on illiquid assets vs Ground Truth.
        </div>
        """, unsafe_allow_html=True)
        
        b_col1, b_col2 = st.columns(2)
        with b_col1:
            # Visually "Primary" Button (Green)
            if st.button("Explore", key="btn_vol", type="primary", use_container_width=True):
                st.switch_page("pages/03_Robust_Covariance.py")
        with b_col2:
            if st.button("Methodology", key="story_p3", use_container_width=True):
                show_methodology("Robust Covariance Estimation (In Dev)", story_p3)

# --- DISCLAIMER ---
st.divider()
st.markdown(
    "<div style='text-align: center; color: #888888; font-size: 0.9em; padding: 20px;'>"
    "<i><b>Disclaimer:</b> This platform is an independent, non-professional research environment developed for educational and experimental purposes. "
    "While every effort is made to ensure the mathematical accuracy of the pricing engines and analytics, bugs or logic errors may occasionally occur. "
    "If you spot any anomalies or have suggestions for improvement, please feel free to reach out. Constructive feedback is always welcome.</i><br>"
    "<b>Contact:</b> <a href='mailto:gwendal.decourchelle@edhec.com' style='color:#a0a0a0;'>gwendal.decourchelle@edhec.com</a>"
    "</div>",
    unsafe_allow_html=True
)