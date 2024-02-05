import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import Session
import warnings

warnings.filterwarnings("ignore")


st.set_page_config(page_title=":bar_chart: Commence Estimates", page_icon="📈", layout="wide")

st.title(":bar_chart: Commence Estimates")
st.info("The **Commencing Enrolment** process is a critical annual undertaking where the University strategically "
        " determines the target number of commencing students for all courses for the upcoming year and the indicative "
        "estimates for the subsequent four years. As part of this process, the University also determines the updated "
        "estimate of commencing students for the current year, based on actuals year-to-date.\n"
        "The estimate tool created by group 1 implements the following features,\n"
        "- Support role based operations\n"
        "- Allow create and modify versions of estimates\n"
        "- Visualise the actuals and versions of estimates for comparison\n"
        "- Email notification for better collabration", icon="ℹ️")


@st.cache_resource
def create_session():
    if 'snowflake' in st.secrets:
        return Session.builder.configs(st.secrets.snowflake).create()
    else:
        return get_active_session()


if 'session' not in st.session_state:
    session = create_session()
    st.session_state['session'] = session
else:
    session = st.session_state.session

current_role = session.get_current_role().replace('"', '')

st.sidebar.markdown("""
    <style>
    [data-testid='stSidebarNav'] > ul {
        min-height: 40vh;
    } 
    </style>
    """, unsafe_allow_html=True)

st.sidebar.warning(f"Login Role **{current_role}**")

st.session_state['current_role'] = current_role

