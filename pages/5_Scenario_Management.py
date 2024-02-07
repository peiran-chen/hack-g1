import itertools
import json
import time

import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, sql_expr, sum
import numpy as np
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
            'COURSE',
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
    ).sum("COURSE_ENROLMENT_COUNT").sort(['OWNING_FACULTY', 'COURSE'])
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
        scenario_df = session.table('scenario').select(
            ['ID', 'SCENARIO_NAME', 'VERSION_NAME', 'NOTES', 'IS_FINAL', 'CONFIRMED_BY_ARTS',
             'CONFIRMED_BY_MQBS', 'CONFIRMED_BY_SCI', 'CONFIRMED_BY_FMHHS']
        ).with_column('SCENARIO', sql_expr("SCENARIO_NAME || ' (' || VERSION_NAME || ')'"))

        scenario_distinct_list = [x.SCENARIO for x in scenario_df.select('SCENARIO').distinct().collect()]
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
                        scenario_df.select('SCENARIO').distinct().order_by('SCENARIO'),
                        key='cs_estimate_scenario_select'
                    )
                # add rule choices
                admin_roles = ['ACCOUNTADMIN', 'G1_ADMIN']
                faculty_roles = [
                    'G1_FACULTY_SCI',
                    'G1_FACULTY_ARTS',
                    'G1_FACULTY_MQBS',
                    'G1_FACULTY_FMHHS',
                ]
                recuitement_staff_roles = ['G1_RECRUITMENT_INTERNATIONAL', 'G1_RECRUITMENT_DOMESTIC']

                if current_role in admin_roles:
                    msg = 'BIR Admin can apply Admin Rules, Recruitement Rules and Faculty Rules'
                    st.info(msg, icon='ℹ️')
                    allow_rule_owner_list = [
                        *admin_roles,
                        *faculty_roles,
                        *recuitement_staff_roles
                    ]
                elif current_role in faculty_roles:
                    msg = 'Faculty Admin can apply faculty rules and Recruitement Rules'
                    st.info(msg, icon='ℹ️')
                    allow_rule_owner_list = [
                        *faculty_roles,
                        *recuitement_staff_roles
                    ]
                elif current_role in recuitement_staff_roles:
                    msg = 'Recuitement Staff does not generate estimation'
                    st.warning(msg)

                default_increase_input = st.text_input(
                    '## Default Annual Increase, eg, 0.03 is 3%',
                    value='0.03',
                    key='default_increase_input'
                )

                rule_df = session.table('rule').to_pandas()
                rule_df = rule_df[rule_df['RULE_OWNER'].isin(allow_rule_owner_list)]
                with st.expander('View All Available Rules'):
                    st.write(rule_df[['RULE_NAME', 'DESCRIPTION', 'EXTRA_COMMENT', 'RULE_OWNER']])

                rule_select = st.multiselect(
                    '**Select Rules**. Please pay attention to the sequence. '
                    'The estimation rules will be applied in order.',
                    rule_df['RULE_NAME'],
                    help="abc",
                    key='rule_select'
                )

                rule_select_text = '\n'.join([ '- ' + x for x in st.session_state.rule_select])

                description_text = f'The 2024 whole year estimation is based on the pro rata calcuation on top of the actual '\
                                   f'**{st.session_state.cs_actual_name_select}** '\
                                   f'enrolments and esitmation plan **{st.session_state.cs_estimate_scenario_select}**. \n'\
                                   f'The rest 2025-2028 calcuation applies the estimation rules, including default annual increase.' \
                                   f'The select rules are,\n' \
                                   f'{rule_select_text}'
                st.info(description_text, icon='ℹ️')

                # fetch rule details
                # rule_detail_list = rule_df[rule_df['RULE_NAME'].isin(st.session_state.rule_select)]['RULE_CONTENT']
                rule_json_list = []
                if st.session_state.rule_select:
                    for i in st.session_state.rule_select:
                        rule_str = rule_df[rule_df['RULE_NAME'] == i].RULE_CONTENT.iloc[0]
                        rule_json = json.loads(rule_str)
                        rule_json_list.append(rule_json)
                        # st.write(rule_json)
                    with st.expander('View Rules'):
                        st.write(rule_json_list)

                # apply default rules
                default_increase_float = float(st.session_state.default_increase_input)

                submit = st.button(
                    '## Generate Scenario'
                )
                if submit:
                    try:
                        # estimate current year based on March Round (Session 1)
                        # march (session 1) actual
                        march_actual_df = session.table('commence_actual').filter(
                            col('ACTUAL_NAME') == st.session_state.cs_actual_name_select
                        ).select(sum(col('COURSE_ENROLMENT_COUNT')).alias('COURSE_ENROLMENT_COUNT'))
                        s1_actual = march_actual_df.to_pandas().iloc[0]['COURSE_ENROLMENT_COUNT']

                        st.write(st.session_state.cs_estimate_scenario_select)

                        scenario_data_df = session.table('SCENARIO_DATA')

                        scenario_id = scenario_df.filter(
                            col('SCENARIO') == st.session_state.cs_estimate_scenario_select
                        ).select('ID').to_pandas().iloc[0]['ID']

                        # st.write(scenario_id)

                        scenario_data_df_filter = session.table('SCENARIO_DATA').filter(
                            (col('SCENARIO_ID') == int(scenario_id)) & (col('COMMENCING_STUDY_PERIOD') == 'Session 1') & (col('PERIOD') == '2024')
                        )
                        s1_estimate = scenario_data_df_filter.select(
                            sum('COURSE_ENROLMENT_COUNT').alias('COURSE_ENROLMENT_COUNT')
                        ).select('COURSE_ENROLMENT_COUNT').to_pandas().iloc[0]['COURSE_ENROLMENT_COUNT']
                        increase_by = float(s1_actual / s1_estimate)
                        # st.write(f'increase by {increase_by}')

                        not_s1_estimate_df = session.table('SCENARIO_DATA').filter(
                            (col('SCENARIO_ID') == int(scenario_id)) & (col('COMMENCING_STUDY_PERIOD') != 'Session 1') & (col('PERIOD') == '2024')
                        )
                        not_s1_estimate_df_pd = not_s1_estimate_df.to_pandas()
                        not_s1_estimate_df_pd['COURSE_ENROLMENT_COUNT'] = np.ceil(not_s1_estimate_df_pd['COURSE_ENROLMENT_COUNT'] * increase_by)
                        not_s1_estimate_df_pd= not_s1_estimate_df_pd.drop(columns=['ID'])
                        # st.write(not_s1_estimate_df_pd)
                        march_actual_df_pd = session.table('commence_actual').filter(
                            col('ACTUAL_NAME') == st.session_state.cs_actual_name_select
                        ).to_pandas()
                        march_actual_df_pd = march_actual_df_pd[['COURSE', 'PERIOD', 'COMMENCING_STUDY_PERIOD', 'OWNING_FACULTY', 'COURSE_LEVEL_NAME', 'FEE_LIABILITY_GROUP', 'COURSE_ENROLMENT_COUNT']]
                        march_actual_df_pd['SCENARIO_ID'] = int(scenario_id)
                        march_actual_df_pd = march_actual_df_pd[['SCENARIO_ID', 'COURSE', 'PERIOD', 'COMMENCING_STUDY_PERIOD', 'OWNING_FACULTY', 'COURSE_LEVEL_NAME', 'FEE_LIABILITY_GROUP', 'COURSE_ENROLMENT_COUNT']]
                        estimate_2024_pd = pd.concat([march_actual_df_pd, not_s1_estimate_df_pd], sort=False)

                        estimate_2024_pd['INCREASE_BY'] = float(st.session_state.default_increase_input)
                        df = estimate_2024_pd.copy()

                        estimate_all_pd = estimate_2024_pd
                        for year in ['2025', '2026', '2027', '2028']:
                            df['PERIOD'] = year
                            for rule_dict in rule_json_list:
                                x = {
                                    'COURSE': rule_dict.get('courses'),
                                    'PERIOD': rule_dict.get('periods'),
                                    'COMMENCING_STUDY_PERIOD': rule_dict.get('commencing_study_periods'),
                                    'OWNING_FACULTY': rule_dict.get('owning_faculties'),
                                    'COURSE_LEVEL_NAME': rule_dict.get('course_level_names'),
                                    'FEE_LIABILITY_GROUP': rule_dict.get('fee_liability_groups'),
                                    'INCREASE_BY': [rule_dict.get('increase_by')],
                                }
                                rule_pd = pd.DataFrame(list(itertools.product(*x.values())), columns=x.keys())
                                df = pd.merge(
                                    df, rule_pd,
                                    how="left",
                                    on=['COURSE', 'PERIOD', 'COMMENCING_STUDY_PERIOD', 'OWNING_FACULTY', 'COURSE_LEVEL_NAME', 'FEE_LIABILITY_GROUP'],
                                    suffixes=('_OLD', '')
                                )
                                st.write(df)
                                df['INCREASE_BY'].fillna(df['INCREASE_BY_OLD'], inplace=True)

                                df.drop(columns=['INCREASE_BY_OLD'], inplace=True)

                            df['COURSE_ENROLMENT_COUNT'] = np.ceil(
                                df['COURSE_ENROLMENT_COUNT'] * (1 + df['INCREASE_BY']))
                            estimate_all_pd = pd.concat([estimate_all_pd, df], sort=False)
                        # st.dataframe(estimate_all_pd)
                        # st.write(estimate_all_pd.shape)
                        session.write_pandas(estimate_all_pd, 'tmp_estimate', quote_identifiers=False, auto_create_table=True, overwrite=True)

                        insert_scenario_sql = \
                            f"""insert into scenario (scenario_name, version_name, notes)
                                                    values(
                                                    '{st.session_state.cs_scenario_name_input}',
                                                    'init',
                                                    '{st.session_state.cs_scenario_notes_input}'
                                                    )"""
                        session.sql(insert_scenario_sql).collect()

                        insert_scenario_data_sql = f"""insert into scenario_data (scenario_id, 
                                                                                    course,
                                                                                    period,
                                                                                    commencing_study_period,
                                                                                    owning_faculty,
                                                                                    course_level_name,
                                                                                    fee_liability_group,
                                                                                    course_enrolment_count)
                                                    select s.id as scenario_id,
                                                            t.course,
                                                            t.period,
                                                            t.commencing_study_period,
                                                            t.owning_faculty,
                                                            t.course_level_name,
                                                            t.fee_liability_group,
                                                            t.course_enrolment_count
                                                        from scenario s
                                                        inner join tmp_estimate as t
                                                        where s.scenario_name='{st.session_state.cs_scenario_name_input}' 
                                                            and version_name='init'
                                                    """
                        session.sql(insert_scenario_data_sql).collect()

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
            # have drop down to pick a scenario and version
            st.info(
                'Modify or save the version to a new version. \n'
                'The finalised scenario can not be modified in this page.\n'
                'Except the finalised version, BIR Admin can modify all versions. \n'
                'Faculty can modify all versions but limited to the only faculty.',
                icon='ℹ️'
            )
            st.write(st.session_state.create_scenario_select)
            scenario_df_pd = scenario_df.to_pandas()
            scenario_df_pd = scenario_df_pd[scenario_df_pd['SCENARIO'] == st.session_state.create_scenario_select]

            st.write(scenario_df_pd)
            is_final = scenario_df_pd['IS_FINAL'].iloc[0]

            if is_final == 'Y':
                st.warning(f'{st.session_state.create_scenario_select} is a final version. Can not be modified.')
            else:
                # display notes
                with st.expander('View Notes and History'):
                    st.text_area(
                        '**Notes**',
                        scenario_df_pd['NOTES'].iloc[0]
                    )
                scenario_id = scenario_df_pd['ID'].iloc[0]
                # st.write(scenario_id)
                scenario_data_df = session.table('scenario_data').filter(
                    col('SCENARIO_ID') == int(scenario_id)
                ).to_pandas()

                # manage security. Admin can access all faculty courses. Faculty can only access faculty ones
                allow_faculty_list = []
                if current_role in ('ACCOUNTADMIN', 'G1_ADMIN'):
                    allow_faculty_list = scenario_data_df['OWNING_FACULTY'].unique().tolist()
                elif current_role == 'G1_FACULTY_SCI':
                    allow_faculty_list = ['Faculty of Science and Engineering']
                elif current_role == 'G1_FACULTY_ARTS':
                    allow_faculty_list = ['Faculty of Arts']
                elif current_role == 'G1_FACULTY_MQBS':
                    allow_faculty_list = ['Macquarie Business School']
                elif current_role == 'G1_FACULTY_FMHHS':
                    allow_faculty_list = ['Faculty of Medicine, Health and Human Sciences']

                # st.write(allow_faculty_list)

                scenario_data_df_filter = scenario_data_df.copy()

                st.selectbox(
                    '## Owning Faculty',
                    sorted(scenario_data_df[scenario_data_df['OWNING_FACULTY'].isin(allow_faculty_list)]['OWNING_FACULTY'].unique()),
                    key='modify_scenario_owning_faculty'
                )
                scenario_data_df_filter = scenario_data_df_filter[scenario_data_df_filter['OWNING_FACULTY'] == st.session_state.modify_scenario_owning_faculty]

                (col1, col2) = st.columns(2)
                with col1:
                    st.selectbox(
                        '## Period',
                        sorted(scenario_data_df[scenario_data_df['OWNING_FACULTY'].isin(allow_faculty_list)]['PERIOD'].unique()),
                        key='modify_scenario_period'
                    )
                    if st.session_state.modify_scenario_period:
                        scenario_data_df_filter = scenario_data_df_filter[
                            scenario_data_df_filter['PERIOD'] == st.session_state.modify_scenario_period]

                    st.selectbox(
                        '## Commencing Study Period',
                        sorted(scenario_data_df[scenario_data_df['OWNING_FACULTY'].isin(allow_faculty_list)][
                                   'COMMENCING_STUDY_PERIOD'].unique()),
                        key='modify_scenario_commencing_study_period'
                    )
                    if st.session_state.modify_scenario_commencing_study_period:
                        scenario_data_df_filter = scenario_data_df_filter[
                            scenario_data_df_filter['COMMENCING_STUDY_PERIOD'] == st.session_state.modify_scenario_commencing_study_period]

                with col2:
                    st.multiselect(
                        '## Courses',
                        sorted(scenario_data_df[
                                   (scenario_data_df['OWNING_FACULTY'].isin(allow_faculty_list)) & (scenario_data_df['OWNING_FACULTY'] == st.session_state.modify_scenario_owning_faculty)
                               ][
                                   'COURSE'].unique()),
                        key='modify_scenario_course'
                    )
                    if st.session_state.modify_scenario_course:
                        scenario_data_df_filter = scenario_data_df_filter[
                            scenario_data_df_filter['COURSE'].isin(
                                st.session_state.modify_scenario_course)]
                    st.multiselect(
                        '## Course Level names',
                        sorted(scenario_data_df[scenario_data_df['OWNING_FACULTY'].isin(allow_faculty_list)]['COURSE_LEVEL_NAME'].unique()),
                        key='modify_scenario_course_level_name'
                    )
                    if st.session_state.modify_scenario_course_level_name:
                        scenario_data_df_filter = scenario_data_df_filter[
                            scenario_data_df_filter['COURSE_LEVEL_NAME'].isin(st.session_state.modify_scenario_course_level_name)]

                    st.multiselect(
                        '## Fee Liability Group',
                        sorted(scenario_data_df[scenario_data_df['OWNING_FACULTY'].isin(allow_faculty_list)][
                                   'FEE_LIABILITY_GROUP'].unique()),
                        key='modify_scenario_fee_liability_group'
                    )
                    if st.session_state.modify_scenario_fee_liability_group:
                        scenario_data_df_filter = scenario_data_df_filter[
                            scenario_data_df_filter['FEE_LIABILITY_GROUP'].isin(
                                st.session_state.modify_scenario_fee_liability_group)]

                if st.session_state.modify_scenario_owning_faculty:

                    edit_df = st.experimental_data_editor(
                        scenario_data_df_filter,
                        num_rows="dynamic",
                        key="modify_scenario_edit_df"
                    )
                    st.radio(
                        '**Option**',
                        ['Save to a New Version', 'Save to Current Version'],
                        key='modify_scenario_save_option'
                    )

                    if st.session_state.modify_scenario_save_option == 'Save to a New Version':
                        st.text_input(
                            '## Please Provide Version Name',
                            values="",
                            key='modify_scenario_version'
                        )

                    st.text_area(
                        '## Add comments of the change',
                        value="",
                        key='modify_scenario_notes'
                    )
                    submit_button = st.button("Save Data")

                    if submit_button:
                        st.info('button clicked')
                        try:
                            # save modified data to temp table, later merge / update
                            session.write_pandas(
                                edit_df,
                                table_name=f'tmp_modify_scenario',
                                overwrite=True,
                                create_temp_table=False,
                                quote_identifiers=False,
                                auto_create_table=True,
                                # table_type='temp'
                            )
                            time.sleep(3)

                            if st.session_state.modify_scenario_save_option == 'Save to a New Version':
                                '''
                                insert_scenario_sql = \
                            f"""insert into scenario (scenario_name, version_name, notes)
                                                    values(
                                                    '{st.session_state.cs_scenario_name_input}',
                                                    'init',
                                                    '{st.session_state.cs_scenario_notes_input}'
                                                    )"""
                        session.sql(insert_scenario_sql).collect()
                                '''
                                scenario_name = scenario_df_pd['SCENARIO_NAME'].iloc[0]
                                session.sql(
                                    f"""insert into scenario (scenario_name, version_name, notes)
                                                    values(
                                                    'scenario_name',
                                                    '{st.session_state.modify_scenario_version}',
                                                    '{st.session_state.modify_scenario_notes}'
                                                    )"""
                                ).collect()
                            elif st.session_state.modify_scenario_save_option == 'Save to Current Version':
                                session.sql(
                                    f"""update scenario_data as s
                                        set course_enrolment_count=t.course_enrolment_count
                                        from tmp_modify_scenario as t
                                        where t.id=s.id"""
                                ).collect()
                                session.sql(
                                    f"""insert into scenario_notes (scenario_id, notes, created_by, created_at)
                                    values (
                                    {scenario_id},
                                    '{st.session_state.modify_scenario_notes}',
                                    '{current_role}',
                                    current_timestamp()
                                    )
                                    """
                                ).collect()

                                msg = st.success("Data updated")
                                time.sleep(3)
                                msg.empty()
                        except:
                            st.warning("Error updating table")
                        # st.experimental_rerun()



                # st.write(scenario_data_df)
                # st.write(scenario_data_df['SCENARIO_ID'].unique())
                # get data from scenario data


            # scenario_df = session.table('scenario').to_pandas()
            # unique_scenario = scenario_df['SCENARIO_NAME'].unique()
            # st.selectbox(
            #     '## Select Scenario',
            #     unique_scenario,
            #     key="modify_scenario_select"
            # )




            # scenario_data_df = scenario_data_df.to_pandas()
            # st.write(f'**Scenario Name**: {st.session_state.create_scenario_select}')
            # cs_pd_filter = scenario_data_df_pd[
            #     scenario_data_df_pd['SCENARIO'] == st.session_state.create_scenario_select
            # ]
            # st.write(f'**Notes**: {cs_pd_filter["NOTES"].iloc[0]}')
    elif st.session_state.scenario_radio == 'Compare Scenarios':
        # choose multiple scenario to compare
        scenario_df = session.sql(
            """select s.SCENARIO_NAME || ' (' || s.VERSION_NAME || ')' as scenario,
                    sd.course,
                    sd.period,
                    sd.commencing_study_period,
                    sd.owning_faculty,
                    sd.course_level_name,
                    sd.fee_liability_group,
                    sd.course_enrolment_count
                from scenario_data as sd
                inner join scenario as s
                    on sd.scenario_id=s.id"""
        ).to_pandas()

        compare_scenario_select = st.multiselect(
            '## Choose Scenarios to compare',
            options=sorted(scenario_df['SCENARIO'].unique()),
            key='compare_scenario_select'
        )

        col1, col2 = st.columns(2)
        with col1:
            compare_period_select = st.multiselect(
                '## Choose Period to compare',
                options=sorted(scenario_df['PERIOD'].unique()),
                key='compare_period_select'
            )
            compare_commencing_study_period_select = st.multiselect(
                '## Choose Commencing Study Period to compare',
                options=sorted(scenario_df['COMMENCING_STUDY_PERIOD'].unique()),
                key='compare_commencing_study_period_select'
            )
            compare_owning_faculty_select = st.multiselect(
                '## Choose Owning Faculty to compare',
                options=sorted(scenario_df['OWNING_FACULTY'].unique()),
                key='compare_owning_faculty_select'
            )
        with col2:
            compare_fee_liability_group_select = st.multiselect(
                '## Choose Fee Liability Group to compare',
                options=sorted(scenario_df['FEE_LIABILITY_GROUP'].unique()),
                key='compare_fee_liability_group_select'
            )
            compare_course_level_select = st.multiselect(
                '## Choose Course Level to compare',
                options=sorted(scenario_df['COURSE_LEVEL_NAME'].unique()),
                key='compare_course_level_select'
            )
            compare_course_select = st.multiselect(
                '## Choose Courses to compare',
                options=sorted(scenario_df['COURSE'].unique()),
                key='compare_course_select'
            )

        scenario_df_filter = scenario_df.copy()
        scenario_df_filter = scenario_df_filter[
        scenario_df_filter['SCENARIO'].isin(st.session_state.compare_scenario_select)]

        if st.session_state.compare_period_select:
            scenario_df_filter = scenario_df_filter[scenario_df_filter['PERIOD'].isin(st.session_state.compare_period_select)]
        else:
            scenario_df_filter = scenario_df_filter
        if st.session_state.compare_commencing_study_period_select:
            scenario_df_filter = scenario_df_filter[scenario_df_filter['COMMENCING_STUDY_PERIOD'].isin(st.session_state.compare_commencing_study_period_select)]
        else:
            scenario_df_filter = scenario_df_filter
        if st.session_state.compare_owning_faculty_select:
            scenario_df_filter = scenario_df_filter[scenario_df_filter['OWNING_FACULTY'].isin(st.session_state.compare_owning_faculty_select)]
        else:
            scenario_df_filter = scenario_df_filter
        if st.session_state.compare_fee_liability_group_select:
            scenario_df_filter = scenario_df_filter[scenario_df_filter['FEE_LIABILITY_GROUP'].isin(st.session_state.compare_fee_liability_group_select)]
        else:
            scenario_df_filter = scenario_df_filter
        if st.session_state.compare_course_level_select:
            scenario_df_filter = scenario_df_filter[scenario_df_filter['COURSE_LEVEL_NAME'].isin(st.session_state.compare_course_level_select)]
        else:
            scenario_df_filter = scenario_df_filter
        if st.session_state.compare_course_select:
            scenario_df_filter = scenario_df_filter[scenario_df_filter['COURSE'].isin(st.session_state.compare_course_select)]
        else:
            scenario_df_filter = scenario_df_filter

        scenario_df_sum = scenario_df_filter.groupby(
            ["SCENARIO", "PERIOD"])["COURSE_ENROLMENT_COUNT"].sum().reset_index()

        scale_range = [0, 100]
        if not scenario_df_sum.empty:
            scale_range = [scenario_df_sum["COURSE_ENROLMENT_COUNT"].min() * 0.9,
                           scenario_df_sum["COURSE_ENROLMENT_COUNT"].max() * 1.1]
        line_chart = alt.Chart(scenario_df_sum).mark_line(
            point=alt.OverlayMarkDef(filled=False, fill="white", tooltip=True)).encode(
            x=alt.X('PERIOD:N', title="Period", scale=alt.Scale(), axis=alt.Axis(labelAngle=-45)),
            y=alt.Y(
                'COURSE_ENROLMENT_COUNT:Q',
                title="Course Enrolment Count",
                scale=alt.Scale(domain=scale_range)
            ),
            color='SCENARIO:N'
        )

        st.altair_chart(line_chart, use_container_width=True)

        st.download_button(
            f"Download Select Data",
            data=scenario_df_filter.to_csv(index=False).encode('utf-8'),
            file_name=f'scenario_data.csv',
            mime='text/csv',
            help='Click here to download the selected data as a CSV file'
        )
        if len(st.session_state.compare_scenario_select) == 2:
            st.subheader(f'Difference between {st.session_state.compare_scenario_select[0]} and {st.session_state.compare_scenario_select[1]}')
            df_1 = scenario_df_filter[scenario_df_filter['SCENARIO'] == st.session_state.compare_scenario_select[0]]
            df_2 = scenario_df_filter[scenario_df_filter['SCENARIO'] == st.session_state.compare_scenario_select[1]]
            merged_df = pd.merge(
                df_1,
                df_2,
                on=['COURSE', 'PERIOD', 'COMMENCING_STUDY_PERIOD', 'OWNING_FACULTY', 'COURSE_LEVEL_NAME', 'FEE_LIABILITY_GROUP'],
                suffixes=(' '+st.session_state.compare_scenario_select[0], ' '+st.session_state.compare_scenario_select[1])
            ).drop(columns=[f'SCENARIO {st.session_state.compare_scenario_select[0]}', f'SCENARIO {st.session_state.compare_scenario_select[1]}'])
            st.write(merged_df)


elif st.session_state.scenario_actual_option == 'Faculty Approval':
    st.header('Faculty Approval')



