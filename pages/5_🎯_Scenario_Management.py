import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, sql_expr, sum
import pandas as pd
import altair as alt
import warnings


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

st.title(':dart: Scenario Management')

with st.sidebar:
    scenario_actual_option = st.radio(
        '## Options',
        options=[
            'Actuals',
            'Scenario Management',
            'Faculty Approval'
        ],
        key="scenario_actual_option"
    )

    st.warning(f"Login Role **{current_role}**")

if st.session_state.scenario_actual_option == 'Actuals':
    st.header('Actuals')
    st.info('There are two main rounds to estimate, late March and early July. '
            'The Actuals in late March after Census Date for Session 1. '
            'The course enrolments of the rest of the year is based on the result to date. \n'
            'BIR Senior Analyst prepared the Actuals in the Snowflake table', icon='ℹ️')
    actual_df = session.table('commence_actual')
    actual_name_select = st.selectbox(
        '## Choose Actual Name',
        actual_df.select('ACTUAL_NAME').distinct().order_by('ACTUAL_NAME'),
        key='actual_name_select'
    )
    actual_df_format = actual_df.filter(
        col('ACTUAL_NAME') == actual_name_select
    ).select(
        [
            'COURSE_NAME',
            'OWNING_FACULTY',
            'COMMENCING_STUDY_PERIOD',
            'COURSE_LEVEL_NAME',
            'FEE_LIABILITY_GROUP',
            'COURSE_ENROLMENT_COUNT'
        ]
    ).pivot(
        "COMMENCING_STUDY_PERIOD",
        [
            'Session 1',
            'Session 2',
            'Session 3',
            'Term 1',
            'Term 2',
            'Term 3',
            'Term 4',
            'Term 5',
            'Term 6',
        ],
    ).sum("COURSE_ENROLMENT_COUNT").sort(['OWNING_FACULTY', 'COURSE_NAME'])
    with st.expander('Expand to check data'):
        st.dataframe(actual_df_format)
    st.download_button(
        f"Download {actual_name_select}.csv",
        data=actual_df.to_pandas().to_csv(index = False).encode('utf-8'),
        file_name=f'{actual_name_select}.csv',
        mime='text/csv',
        help='Click here to download the data as a CSV file'
    )

elif st.session_state.scenario_actual_option == 'Scenario Management':
    st.header('Scenario Management')
    scenario_radio = st.radio(
        '## Choose the following options',
        [
            'Create a Scenario',
            'Compare Scenarios'
        ],
        horizontal=True,
        key='scenario_radio'
    )
    st.subheader(st.session_state.scenario_radio)
    if st.session_state.scenario_radio == 'Create a Scenario':
        # load actuals
        actual_df = session.table('commence_actual')

        # load scenarios
        scenario_data_df = session.table('scenario').select(
            ['SCENARIO_NAME', 'VERSION_NAME', 'NOTES', 'IS_FINAL', 'CONFIRMED_BY_ARTS',
             'CONFIRMED_BY_MQBS', 'CONFIRMED_BY_SCI', 'CONFIRMED_BY_FMHHS']
        ).with_column('SCENARIO', sql_expr("SCENARIO_NAME || ' (' || VERSION_NAME || ')'"))

        scenario_distinct_list = [x.SCENARIO for x in scenario_data_df.select('SCENARIO').distinct().collect()]
        create_scenario_select = st.selectbox(
            '## Choose **Create Scenario** or existing ones',
            ['Create Scenario', *scenario_distinct_list],
            key='create_scenario_select'
        )
        '---'
        if st.session_state.create_scenario_select == 'Create Scenario':
            st.text_input(
                '## Scenario Name',
                value="",
                key='cs_scenario_name_input'
            )

            st.text_area(
                '## Notes',
                value="",
                key="cs_scenario_notes_input"
            )
            st.selectbox(
                'Pick which round',
                [
                    'March Round',
                    'July Round',
                ],
                key='cs_round_select'
            )
            if st.session_state.cs_round_select == 'March Round':
                st.info('Create scenario based on the selected Actuals. '
                        'Re-calibrate an existing scenario based on the selected Actuals over 2025-2028.\n'
                        'A new scenario and init version is generated and saved in Snowflake after submit')

                col1, col2 = st.columns(2)
                with col1:
                    st.selectbox(
                        '## Choose Actual Name',
                        actual_df.select('ACTUAL_NAME').distinct().order_by('ACTUAL_NAME'),
                        key='cs_actual_name_select'
                    )
                with col2:
                    st.selectbox(
                        '## Choose Base Scenario Name',
                        scenario_data_df.select('SCENARIO').distinct().order_by('SCENARIO')
                    )
                submit = st.button(
                    '## Generate Scenario'
                )
                if submit:
                    try:
                        insert_scenario_sql = \
                            f"""insert into scenario (scenario_name, version_name, notes)
                            values(
                            '{st.session_state.cs_scenario_name_input}',
                            'init',
                            '{st.session_state.cs_scenario_notes_input}'
                            )"""

                        select_scenario_id_sql = \
                            f"""select id from scenario 
                            where scenario_name='{st.session_state.cs_scenario_name_input}' 
                            and version_name='init'
                            """

                        st.success(f'Scenario **{st.session_state.cs_scenario_name_input}** is saved in Snowflake')
                    except Exception as e:
                        st.error('Failed to save')
                        st.error(e)
            elif st.session_state.cs_round_select == 'July Round':
                st.info('Create scenario based on the selected Actuals. '
                        'Set targets for 2025 and set the outlook for 2026-2029.\n'
                        'Fine tune the enrolment count based on the *Role*. '
                        'A new version is saved in Snowflake after submit')
        elif st.session_state.create_scenario_select:
            scenario_data_df_pd = scenario_data_df.to_pandas()
            st.write(f'**Scenario Name**: {st.session_state.create_scenario_select}')
            cs_pd_filter = scenario_data_df_pd[
                scenario_data_df_pd['SCENARIO'] == st.session_state.create_scenario_select
            ]
            st.write(f'**Notes**: {cs_pd_filter["NOTES"].iloc[0]}')
    elif st.session_state.scenario_radio == 'Compare Scenarios':
        # TODO
        # choose multiple scenario to compare
        st.info('todo choose multiple scenario to compare')


elif st.session_state.scenario_actual_option == 'Faculty Approval':
    st.header('Faculty Approval')



