import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import libsql_experimental as libsql
import time
from streamlit_autorefresh import st_autorefresh

# Page configuration
st.set_page_config(
    page_title="DMA Survey - Community Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Force light mode and fix input styling
st.markdown("""
<style>
    .stApp {
        color: #262730;
        background-color: #FFFFFF;
    }
    .stApp > header {
        background-color: transparent;
    }
    .stApp > .main {
        background-color: #FFFFFF;
    }
    [data-testid="stHeader"] {
        background-color: #FFFFFF;
    }
    [data-testid="stToolbar"] {
        background-color: #FFFFFF;
    }
    [data-testid="stSidebar"] {
        background-color: #F0F2F6;
    }
    
    /* Fix input fields */
    .stTextInput > div > div > input {
        background-color: #FFFFFF;
        color: #262730;
        border: 1px solid #d1d5db;
    }
    
    /* Fix text areas and other inputs */
    .stTextArea > div > div > textarea,
    .stSelectbox > div > div > div,
    .stNumberInput > div > div > input {
        background-color: #FFFFFF;
        color: #262730;
        border: 1px solid #d1d5db;
    }
    
    /* Fix plotly chart container background only */
    [data-testid="stPlotlyChart"] {
        background-color: #FFFFFF;
    }
</style>
""", unsafe_allow_html=True)


# Database connection
@st.cache_resource
def get_connection():
    db_url = st.secrets["DB_URL"]
    auth_token = st.secrets["AUTH_TOKEN"]
    return libsql.connect(database=db_url, auth_token=auth_token)


# Remove any caching to ensure real-time data
def get_dma_survey_analytics():
    """Get analytics data for DMA survey results."""
    conn = get_connection()
    try:
        # Get basic statistics
        stats_query = """
        SELECT 
            COUNT(*) as total_responses,
            AVG(total_score) as avg_score,
            MIN(total_score) as min_score,
            MAX(total_score) as max_score,
            AVG(question_1_score) as avg_q1,
            AVG(question_2_score) as avg_q2,
            AVG(question_3_score) as avg_q3,
            AVG(question_4_score) as avg_q4,
            AVG(question_5_score) as avg_q5
        FROM dma_survey_results
        """
        stats = conn.execute(stats_query).fetchone()

        # Get maturity level distribution
        maturity_query = """
        SELECT maturity_level, COUNT(*) as count
        FROM dma_survey_results
        GROUP BY maturity_level
        ORDER BY COUNT(*) DESC
        """
        maturity_dist = conn.execute(maturity_query).fetchall()

        # Get all responses
        all_query = """
        SELECT name, organisation, total_score, maturity_level, created_at
        FROM dma_survey_results
        ORDER BY created_at DESC
        """
        all_responses = conn.execute(all_query).fetchall()

        return {
            "stats": {
                "total_responses": stats[0],
                "avg_score": round(stats[1], 2) if stats[1] else 0,
                "min_score": stats[2],
                "max_score": stats[3],
                "question_averages": {
                    "q1": round(stats[4], 2) if stats[4] else 0,
                    "q2": round(stats[5], 2) if stats[5] else 0,
                    "q3": round(stats[6], 2) if stats[6] else 0,
                    "q4": round(stats[7], 2) if stats[7] else 0,
                    "q5": round(stats[8], 2) if stats[8] else 0,
                },
            },
            "maturity_distribution": [
                {"level": row[0], "count": row[1]} for row in maturity_dist
            ],
            "recent_responses": [
                {
                    "name": row[0],
                    "organisation": row[1],
                    "total_score": row[2],
                    "maturity_level": row[3],
                    "created_at": row[4],
                }
                for row in all_responses
            ],
        }
    except Exception as e:
        st.error(f"Error getting DMA analytics: {e}")
        return {
            "stats": {
                "total_responses": 0,
                "avg_score": 0,
                "min_score": 0,
                "max_score": 0,
                "question_averages": {},
            },
            "maturity_distribution": [],
            "recent_responses": [],
        }


# Custom CSS for styling
st.markdown(
    """
<style>
    .main-header {
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 3rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        padding: 2rem;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        border: 1px solid #e1e8ed;
        text-align: center;
    }
    .metric-card .metric-value {
        font-size: 3rem;
        font-weight: bold;
        color: #2c3e50;
    }
    .metric-card .metric-label {
        font-size: 1.2rem;
        color: #6c757d;
    }
</style>
""",
    unsafe_allow_html=True,
)


def show_analytics_page():
    """Display the community analytics page."""
    st.markdown(
        '<div class="main-header">Community Analytics</div>', unsafe_allow_html=True
    )
    st.caption("🟢 Live updates every 3 seconds")

    # Real-time auto-refresh using streamlit-autorefresh component
    st_autorefresh(interval=3000, key="dashboard_refresh")

    # Get analytics data (cached for performance)
    analytics = get_dma_survey_analytics()

    if analytics["stats"]["total_responses"] > 0:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                f"""
            <div class="metric-card">
                <div class="metric-label">Total Responses</div>
                <div class="metric-value">{analytics["stats"]["total_responses"]}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        with col2:
            st.markdown(
                f"""
            <div class="metric-card">
                <div class="metric-label">Average Score</div>
                <div class="metric-value">{analytics["stats"]["avg_score"]}/25</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

        # Charts
        if analytics["maturity_distribution"]:
            df_maturity = pd.DataFrame(analytics["maturity_distribution"])
            fig_pie = px.pie(
                df_maturity,
                values="count",
                names="level",
                title="Maturity Level Distribution",
                color_discrete_sequence=px.colors.qualitative.Set3,
            )
            fig_pie.update_layout(
                paper_bgcolor='rgba(0,0,0,0)',  # Transparent background
                plot_bgcolor='rgba(0,0,0,0)',   # Transparent plot background
                font=dict(color='black'),        # Black text
                title_font_color='black'         # Black title
            )
            st.plotly_chart(fig_pie, use_container_width=True)
    else:
        st.info(
            "No survey responses yet. More analytics will be available as users complete the survey."
        )


show_analytics_page()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.9rem;'>"
    "DMA Survey - Data Maturity Assessment | Powered by ISDM"
    "</div>",
    unsafe_allow_html=True,
)
