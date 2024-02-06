import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import Session
import time
import warnings


warnings.filterwarnings("ignore")


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

st.title(":books: Reference Data Management")

current_role = session.get_current_role().replace('"', '')

with st.sidebar:
    ref_option = st.radio('## Choose Reference Data', options=[
        'Course',
        'Owning Faculty',
        'Period Name',
        'Course Level Name',
        'Fee Liability Group'
    ])
    st.session_state['ref_option'] = ref_option
    st.info('The Reference Data is readonly. Only Admin can edit it.', icon='ℹ️')
    st.warning(f"Login Role **{current_role}**")

if 'ref_option' in st.session_state:
    st.subheader(ref_option)
    if st.session_state.ref_option == 'Course':
        st.session_state['table'] = 'ref_course'
    if st.session_state.ref_option == 'Owning Faculty':
        st.session_state['table'] = 'ref_owning_faculty'
    if st.session_state.ref_option == 'Period Name':
        st.session_state['table'] = 'ref_period'
    if st.session_state.ref_option == 'Course Level Name':
        st.session_state['table'] = 'ref_course_level'
    if st.session_state.ref_option == 'Fee Liability Group':
        st.session_state['table'] = 'ref_fee_liability_group'

    if 'table' in st.session_state:
        df = session.table(st.session_state.table)
        if current_role in ['ACCOUNTADMIN', 'G1_ADMIN']:
            with st.form("data_editor_form"):
                st.caption("Edit the dataframe below")

                edited = st.experimental_data_editor(df, use_container_width=True, num_rows="dynamic")
                submit_button = st.form_submit_button("Submit")

            if submit_button:
                try:
                    # Note the quote_identifiers argument for case insensitivity
                    session.write_pandas(
                        edited,
                        table_name=f'tmp_{st.session_state.table}',
                        overwrite=True,
                        quote_identifiers=False,
                        table_type='temp'
                    )
                    msg = st.success("Table updated")
                    time.sleep(3)
                    msg.empty()
                except:
                    st.warning("Error updating table")
                st.experimental_rerun()
        else:
            st.dataframe(df)