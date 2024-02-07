import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import Session
import warnings

warnings.filterwarnings("ignore")

st.set_page_config(page_title=":bar_chart: Commence Estimates", page_icon="📈", layout="wide")

st.title(":bar_chart: Commence Estimates")

st.info(
    "This is a critical annual undertaking process where University determines the target number of commencing students,\n"
    "- All courses.\n"
    "- For subsequent 4 years.\n"
    "- Re-estimate for current year, based on actuals YTD.\n\n"
    "More FAQ's -- Link to FAQ document to be created by Angela Liu\n\n"
    "**Assumptions**:\n"
    "- New Courses for the current year will not have estimates until the Admin / Faculty manually enters the enrolment count.\n"
    "- By default, the Global Blanket percentage applies, unless the Rule is created which takes precedence.\n"
    "- In case of Overlap of Rules, calculation happens based on the priority of rules selected during the scenario generation.\n"
    "- Faculty own the final enrolment estimates , upon approval (s)would generate the final version of scenario.",
    icon="ℹ️"
)

def create_session():
    # Snowflake session
    try:
        return get_active_session()
    except Exception as e:
        None
    # Use local session
    if 'snowflake' in st.secrets:
        return Session.builder.configs(st.secrets.snowflake).create()
    # Current connection method
    elif 'connection' in dir(st):
        return st.connection("snowflake").session()
    # 1.22
    elif 'experimental_connection' in dir(st):
        return st.experimental_connection("snowpark").session()
    else:
        raise 'Session not detected'


if 'session' not in st.session_state:
    session = create_session()
    st.session_state['session'] = session
else:
    session = st.session_state.session

current_role = session.get_current_role().replace('"', '')

st.sidebar.warning(f"Login Role **{current_role}**")

st.session_state['current_role'] = current_role

