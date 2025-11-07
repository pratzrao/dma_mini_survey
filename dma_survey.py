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
    page_title="DMA Survey - Data Maturity Assessment",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# Database connection
@st.cache_resource
def get_connection():
    db_url = st.secrets["DB_URL"]
    auth_token = st.secrets["AUTH_TOKEN"]
    return libsql.connect(database=db_url, auth_token=auth_token)


# Database functions
def create_dma_survey_table():
    """Create the DMA survey results table."""
    conn = get_connection()
    try:
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS dma_survey_results (
            survey_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            organisation TEXT NOT NULL,
            address TEXT,
            email TEXT,
            contact_number TEXT,
            question_1_score INTEGER NOT NULL CHECK(question_1_score BETWEEN 1 AND 5),
            question_2_score INTEGER NOT NULL CHECK(question_2_score BETWEEN 1 AND 5),
            question_3_score INTEGER NOT NULL CHECK(question_3_score BETWEEN 1 AND 5),
            question_4_score INTEGER NOT NULL CHECK(question_4_score BETWEEN 1 AND 5),
            question_5_score INTEGER NOT NULL CHECK(question_5_score BETWEEN 1 AND 5),
            total_score INTEGER NOT NULL,
            maturity_level TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        conn.execute(create_table_sql)
        conn.commit()
        return True
    except Exception as e:
        st.error(f"Error creating DMA survey table: {e}")
        return False


def submit_dma_survey(name, organisation, address, email, contact_number, scores):
    """Submit a completed DMA survey."""
    conn = get_connection()
    try:
        # Calculate total score
        total_score = sum(scores.values())

        # Determine maturity level based on total score
        if total_score <= 5:
            maturity_level = "Beginner Level"
        elif total_score <= 10:
            maturity_level = "Emerging Level"
        elif total_score <= 15:
            maturity_level = "Progressing Level"
        elif total_score <= 20:
            maturity_level = "Advanced Level"
        else:
            maturity_level = "Expert Level"

        # Insert survey response
        insert_sql = """
        INSERT INTO dma_survey_results 
        (name, organisation, address, email, contact_number, 
         question_1_score, question_2_score, question_3_score, 
         question_4_score, question_5_score, total_score, maturity_level)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """

        # Handle empty/None values for optional fields
        address = address if address else ""
        email = email if email else ""
        contact_number = contact_number if contact_number else ""

        cursor = conn.execute(
            insert_sql,
            (
                name,
                organisation,
                address,
                email,
                contact_number,
                scores["q1"],
                scores["q2"],
                scores["q3"],
                scores["q4"],
                scores["q5"],
                total_score,
                maturity_level,
            ),
        )

        conn.commit()
        return cursor.lastrowid, total_score, maturity_level
    except Exception as e:
        st.error(f"Error submitting DMA survey: {e}")
        conn.rollback()
        return None, None, None




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
    .sub-header {
        text-align: center;
        color: #6c757d;
        font-size: 1.3rem;
        margin-bottom: 3rem;
        font-weight: 300;
    }
    .score-display {
        text-align: center;
        font-size: 4rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 2rem 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    .maturity-level {
        text-align: center;
        font-size: 2rem;
        font-weight: bold;
        color: #495057;
        margin: 1rem 0;
        padding: 1rem;
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    .participant-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 20px;
        margin: 1rem 0;
        text-align: center;
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
        border: 1px solid rgba(255, 255, 255, 0.1);
        backdrop-filter: blur(10px);
    }
    .participant-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 12px 35px rgba(102, 126, 234, 0.4);
    }
    .participant-org {
        font-size: 1.2rem;
        font-weight: bold;
        margin-bottom: 0.8rem;
        color: #ffffff;
        text-align: center;
        letter-spacing: 0.5px;
    }
    .participant-name {
        font-size: 1rem;
        margin-bottom: 0.8rem;
        color: #f8f9fa;
        text-align: center;
    }
    .participant-score {
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0.5rem 0;
        color: #ffffff;
        text-align: center;
    }
    .participant-level {
        font-size: 0.9rem;
        margin-top: 0.5rem;
        color: #e3f2fd;
        text-align: center;
        font-style: italic;
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

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 1rem;
        font-weight: 600;
        font-size: 0.95rem;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
        transition: all 0.3s ease;
        min-height: 60px;
        white-space: pre-line;
        text-align: center;
    }
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.5);
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4c93 100%);
    }
    div[data-testid="column"] .stButton > button {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        color: #495057;
        border: 2px solid #dee2e6;
        border-radius: 12px;
        padding: 1rem 0.5rem;
        font-weight: 500;
        font-size: 0.9rem;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        transition: all 0.3s ease;
        min-height: 70px;
    }
    div[data-testid="column"] .stButton > button:hover {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-color: #667eea;
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.3);
    }
    .real-time-indicator {
        position: fixed;
        top: 10px;
        right: 10px;
        background: #28a745;
        color: white;
        padding: 8px 12px;
        border-radius: 25px;
        font-size: 12px;
        z-index: 1000;
        animation: pulse 2s infinite;
        box-shadow: 0 2px 10px rgba(40, 167, 69, 0.3);
    }
    @keyframes pulse {
        0% { transform: scale(1); opacity: 0.9; }
        50% { transform: scale(1.05); opacity: 1; }
        100% { transform: scale(1); opacity: 0.9; }
    }
    .refresh-indicator {
        color: #667eea;
        font-style: italic;
        text-align: center;
        animation: fadeInOut 0.5s ease-in-out;
    }
    @keyframes fadeInOut {
        0% { opacity: 0; }
        50% { opacity: 1; }
        100% { opacity: 0.7; }
    }
</style>
""",
    unsafe_allow_html=True,
)

# Create the DMA survey table if it doesn't exist
create_dma_survey_table()

# Initialize session state
if "page" not in st.session_state:
    st.session_state.page = "survey"
if "survey_submitted" not in st.session_state:
    st.session_state.survey_submitted = False
if "user_score" not in st.session_state:
    st.session_state.user_score = None
if "user_level" not in st.session_state:
    st.session_state.user_level = None


def show_survey_form():
    """Display the main survey form."""
    st.markdown('<div class="main-header">DMA Survey</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Data Maturity Assessment</div>', unsafe_allow_html=True
    )

    # Personal Information Section
    st.markdown("### Personal Information")

    organisation = st.text_input(
        "Organisation *", key="org", placeholder="Your organization name"
    )

    st.markdown("---")

    # Survey Questions
    st.markdown("### Assessment Questions")
    st.markdown(
        '<p style="text-align: center; color: #666; font-style: italic; margin-bottom: 2rem;">Rate each question on a scale of 1 to 5</p>',
        unsafe_allow_html=True,
    )

    questions = [
        {
            "text": "To what extent is data considered an organisational priority and importance, currently?",
        },
        {
            "text": "To what extent does your organisation currently employ or engage individuals with data analysis or data science expertise?"
        },
        {
            "text": "To what extent is data used for internal learning, evaluation, and to identify needs and problems?",
        },
        {
            "text": "To what extent do employees in your organisation discuss topics related to data (both project and administrative data) with their peers and senior management?",
        },
        {
            "text": "To what extent are leaders willing to invest resources (time, money, effort) into data-driven practices and solutions?",
        },
    ]

    scores = {}
    for i, question in enumerate(questions, 1):
        st.markdown(
            f"""
        <div style="
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 2rem;
            border-radius: 15px;
            margin: 1.5rem 0;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            border: 1px solid #e1e8ed;
        ">
            <h4 style="
                color: #2c3e50;
                margin-bottom: 1rem;
                font-size: 1.1rem;
            ">
                Question {i}
            </h4>
            <p style="
                color: #34495e;
                font-size: 1rem;
                line-height: 1.6;
                margin-bottom: 1.5rem;
            ">
                {question['text']}
            </p>
        """,
            unsafe_allow_html=True,
        )

        # No special handling needed for question 2 anymore

        # Rating scale with custom styling
        st.markdown('<div style="margin-top: 1rem;">', unsafe_allow_html=True)

        # Create custom rating buttons
        cols = st.columns(5)
        score_labels = [
            "",
            "",
            "",
            "",
            "",
        ]

        for col, score, label in zip(cols, [1, 2, 3, 4, 5], score_labels):
            with col:
                if st.button(
                    f"{score}\n{label}",
                    key=f"q{i}_btn_{score}",
                    use_container_width=True,
                    help=f"Rate {score} out of 5 - {label}",
                ):
                    st.session_state[f"q{i}_selected"] = score

        # Get the selected score or default to 1
        scores[f"q{i}"] = st.session_state.get(f"q{i}_selected", 1)

        # Show selected score
        if f"q{i}_selected" in st.session_state:
            selected = st.session_state[f"q{i}_selected"]
            st.markdown(
                f'<p style="text-align: center; margin-top: 1rem; font-weight: bold; color: #667eea;">Selected: {selected}/5 - {score_labels[selected-1]}</p>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<p style="text-align: center; margin-top: 1rem; color: #6c757d; font-style: italic;">Please select a rating</p>',
                unsafe_allow_html=True,
            )

        st.markdown("</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # Submit button with styling
    st.markdown("<br>", unsafe_allow_html=True)

    # Center the submit button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("Submit Survey", type="primary", use_container_width=True):
            # Validation
            if not organisation:
                st.error("Please fill in all required fields (Organisation)")
                return

            # Check if all questions are answered and build scores dict
            unanswered_questions = []
            final_scores = {}

            for i in range(1, 6):
                if f"q{i}_selected" not in st.session_state:
                    unanswered_questions.append(f"Question {i}")
                else:
                    final_scores[f"q{i}"] = st.session_state[f"q{i}_selected"]

            if unanswered_questions:
                st.error(
                    f"Please answer all questions. Missing: {', '.join(unanswered_questions)}"
                )
                return

            # Submit to database
            survey_id, total_score, maturity_level = submit_dma_survey(
                "", organisation, "", "", "", final_scores
            )

            if survey_id is not None:
                st.session_state.survey_submitted = True
                st.session_state.user_score = total_score
                st.session_state.user_level = maturity_level

                st.session_state.user_org = organisation
                st.session_state.page = "results"
                st.rerun()
            else:
                st.error("Error submitting survey. Please try again.")


def show_results_page():
    """Display individual results and analytics."""

    # Add auto-refresh to results page too
    st_autorefresh(interval=3000, key="results_refresh")

    # Removed anchor - using native scroll component instead

    # Real-time indicator
    st.markdown(
        '<div class="real-time-indicator">🟢 LIVE</div>', unsafe_allow_html=True
    )

    st.markdown('<div class="main-header">Your Results</div>', unsafe_allow_html=True)

    # User's score
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown(
            f'<div class="score-display">{st.session_state.user_score}/25</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            f'<div class="maturity-level">{st.session_state.user_level}</div>',
            unsafe_allow_html=True,
        )

    st.markdown("### Your Assessment Breakdown")

    st.markdown("**Scoring Rubric:**")
    scoring_rubric = {
        "Beginner Level (5 points)": "Minimal prioritisation of data. Data is rarely seen as an organisational priority, hardly discussed in teams, and leadership shows little willingness to invest. Data-related skills are absent, and analytical work is handled manually or intuitively.",
        "Emerging Level (6-10 points)": "Data is acknowledged but inconsistently valued. Data may be rated as important but discussions are occasional and adoption is partial. Leaders begin to recognise data's role but investments remain tentative. Data exposure is low, existing through ad hoc engagements lacks strategy or structure for sustained skill development.",
        "Progressing Level (11-15 points)": "Growing acceptance of data. Data is discussed more frequently, and used for learning and evaluation. Leadership commitment starts translating into structured practices. Some internal capacity exists, supported by periodic external inputs.",
        "Advanced Level (16-20 points)": "Strong data-driven mindset. The data culture supports systematic use across teams. Dedicated data staff and structured collaborations reflect a maturing system. Employees regularly discuss data, leaders actively invest resources, and data is embedded in decision-making and problem identification.",
        "Expert Level (21-25 points)": "Data is considered a core organisational value. Data science is institutionalised. Skilled professionals drive insights across functions, supported by leadership that champions ethical, evidence-driven, and transparent data practices. Employees consistently engage in discussions, and knowledge-sharing systems are in place.",
    }

    for level, description in scoring_rubric.items():
        if st.session_state.user_level in level:
            st.success(f"**{level}**\n\n{description}")
        else:
            st.markdown(f"**{level}**\n\n{description}")

    st.markdown("---")


    # Analytics section
    st.markdown("---")

    st.markdown("### Community Analytics")
    st.caption("🟢 Live updates every 3 seconds")

    # Get analytics data (cached for performance)
    analytics = get_dma_survey_analytics()

    if analytics["stats"]["total_responses"] > 0:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Total Responses</div>
                <div class="metric-value">{analytics["stats"]["total_responses"]}</div>
            </div>
            ''', unsafe_allow_html=True)

        with col2:
            st.markdown(f'''
            <div class="metric-card">
                <div class="metric-label">Average Score</div>
                <div class="metric-value">{analytics["stats"]["avg_score"]}/25</div>
            </div>
            ''', unsafe_allow_html=True)

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
            st.plotly_chart(fig_pie, use_container_width=True)




    else:
        st.info(
            "You are the first participant! More analytics will be available as others complete the survey."
        )






# Main app logic
if st.session_state.page == "survey" and not st.session_state.survey_submitted:
    show_survey_form()
elif st.session_state.page == "results" or st.session_state.survey_submitted:
    show_results_page()

# Footer
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #666; font-size: 0.9rem;'>"
    "DMA Survey - Data Maturity Assessment | Powered by ISDM"
    "</div>",
    unsafe_allow_html=True,
)
