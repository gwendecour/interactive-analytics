import streamlit as st
import os

def set_theme_css():
    """Injects static Dark Mode CSS."""
    st.session_state.theme = 'dark' # Enforce dark theme across all other modules
    
    css = """
    <style>
        [data-testid="stAppViewContainer"] {
            background-color: #0e1117;
            color: #fafafa;
        }
        [data-testid="stHeader"] {
            background-color: rgba(14, 17, 23, 0.0);
        }
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)


def render_header():
    """
    Renders a horizontal navigation bar, hides the native sidebar, and manages the theme.
    """
    set_theme_css()
    
    # CSS TO HIDE THE SIDEBAR AND STYLE THE HEADER
    st.markdown("""
        <style>
            /* Completely hide the sidebar and its toggle button */
            [data-testid="stSidebar"] {display: none;}
            [data-testid="collapsedControl"] {display: none;}
            
            /* Enlarge radio buttons used for navigation tabs and style them as buttons */
            /* --- RADIO BUTTONS STYLING --- */
            
            /* 1. Default Pill Shape (applies to ALL radios) */
            div[role="radiogroup"] label[data-baseweb="radio"] {
                background-color: rgba(150, 150, 150, 0.1) !important;
                border: 1px solid rgba(150, 150, 150, 0.2) !important;
                border-radius: 8px !important;
                margin-right: 10px !important;
                cursor: pointer !important;
                transition: all 0.2s ease;
            }
            div[role="radiogroup"] label[data-baseweb="radio"]:hover {
                background-color: rgba(150, 150, 150, 0.25) !important;
                transform: scale(1.02);
            }
            
            /* Active Tab Style */
            div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) {
                background-color: #475569 !important; /* Soft Slate */
                border: 1px solid #334155 !important;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            div[role="radiogroup"] label[data-baseweb="radio"]:has(input:checked) p {
                color: white !important;
            }
            
            /* 2. MAIN NAVIGATION RADIOS (Large, Bold, Wide by default) */
            div[role="radiogroup"] label[data-baseweb="radio"] {
                padding: 8px 24px !important;
            }
            div[role="radiogroup"] label p {
                font-size: 1.15rem !important;
                font-weight: bold !important;
                margin-bottom: 0px !important;
            }

            /* 3. CHART CONTROL RADIOS (Small, Normal, Compact via st-key mapping) */
            .st-key-acf_radio div[role="radiogroup"] label[data-baseweb="radio"],
            .st-key-dist_radio div[role="radiogroup"] label[data-baseweb="radio"] {
                padding: 4px 12px !important;
            }
            .st-key-acf_radio div[role="radiogroup"] label p,
            .st-key-dist_radio div[role="radiogroup"] label p {
                font-size: 0.9rem !important;
                font-weight: normal !important;
                margin-bottom: 0px !important;
            }
            
            /* Hide the radio circle dot completely */
            div[role="radiogroup"] label[data-baseweb="radio"] > div:first-child {
                display: none !important;
            }
            
            /* Remove left spacing from the text container since circle is gone */
            div[role="radiogroup"] label[data-baseweb="radio"] > div:last-child {
                margin-left: 0 !important;
            }
            
            /* Navigation bar styling */
            .nav-container {
                display: flex;
                justify_content: space-between;
                align_items: center;
                padding: 10px 20px;
                background-color: #0e1117; /* Dark Mode */
                border-bottom: 1px solid #333333;
                margin-bottom: 20px;
            }
            .nav-logo {
                font-family: 'Lora', serif;
                font-size: 1.2rem;
                font-weight: bold;
                color: #ffffff; /* Dark Mode */
                text-decoration: none;
            }
            
            /* Align the height of page links with the Theme button */
            a[data-testid="stPageLink-NavLink"] {
                min-height: 40px !important;
                display: flex !important;
                align-items: center !important;
                justify-content: center !important;
            }
            
            div[data-testid="stButton"] button {
                min-height: 40px !important;
                padding-top: 0.25rem !important;
                padding-bottom: 0.25rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

    # HORIZONTAL NAVIGATION BAR
    # Using columns to align left (Logo/Home) and right (Resume/Story)
    col1, col2 = st.columns([5, 1], vertical_alignment="center")
    
    with col1:
        # Logo and Home Page link
        c_logo, c_text = st.columns([1, 15], vertical_alignment="center")
        with c_logo:
            if os.path.exists("assets/logo.png"):
                st.image("assets/logo.png", width=40)
        with c_text:
            st.page_link("Home.py", label="Home Page")
            
    with col2:
        # Resume link
        st.page_link("pages/04_Resume_&_Story.py", label="My Resume & Story")

    st.divider()