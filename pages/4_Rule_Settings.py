import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import Session
import json
from datetime import datetime
from snowflake.snowpark.functions import col, sql_expr, sum


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

with st.sidebar:
    rule_option = st.radio('## Options', options=[
        'Default Settings',
        'Rule Management',
    ])
    st.session_state['rule_option'] = rule_option
    st.info('The Reference Data is readonly. Only Admin can edit it.', icon='ℹ️')
    st.warning(f"Login Role **{current_role}**")


st.title(':triangular_ruler: Rule Settings')
st.header(rule_option)

if 'rule_option' in st.session_state:
    if st.session_state.rule_option == 'Default Settings':

        st.subheader("Default Annual Increase")
        st.info("The **Default Annual Increase** is a broad blanket % change to be applied on all courses to "
                "estimate the next year course enrolments. "
                "A defined **Estimate Rule** can override the default value.", icon="ℹ️")
        dai_df = session.table('rule_annual_increase')
        st.dataframe(dai_df)

    if st.session_state.rule_option == 'Rule Management':
        option_rule_mgmt = st.radio(
            "Choose Operation",
            options=[
                'List Rules',
                'Create a New Rule',
            ],
            horizontal=True,
        )
        if option_rule_mgmt == 'Create a New Rule':

            period_name_list = [
                '2025', '2026', '2027', '2028', '2029'
            ]
            course_level_name_df = session.table('ref_course_level')
            owning_faculty_df = session.table('ref_owning_faculty')
            commencing_study_period_list = [
                'Session 1',
                'Session 2',
                'Session 3',
                'Term 1',
                'Term 2',
                'Term 3',
                'Term 4',
                'Term 5',
                'Term 6'
            ]
            fee_liability_group_df = session.table('ref_fee_liability_group')
            course_df = session.table('ref_course')
            course_faculty_df = course_df.join(
                owning_faculty_df,
                (course_df['OWNING_FACULTY_ID'] == owning_faculty_df['ID'])
            ).select(["COURSE_NAME", "FACULTY_NAME"])

            if current_role in ['ACCOUNTADMIN', 'G1_ADMIN']:
                st.warning("You can create and modify **Scenario Rules** as Admin")
                course_level_name_df_pd = course_level_name_df.to_pandas()
                owning_faculty_df_pd = owning_faculty_df.to_pandas()
                fee_liability_group_df_pd = fee_liability_group_df.to_pandas()
                course_faculty_df_pd = course_faculty_df.to_pandas()
            elif current_role == 'G1_RECRUITMENT_INTERNATIONAL':
                st.warning("You can create and modify **Scenario Rules** for **International Estimates** changes.")
                course_level_name_df_pd = course_level_name_df.to_pandas()
                owning_faculty_df_pd = owning_faculty_df.to_pandas()
                fee_liability_group_df_pd = fee_liability_group_df.filter(
                    col("FEE_LIABILITY_GROUP_TYPE") == 'International'
                ).to_pandas()
                course_faculty_df_pd = course_faculty_df.to_pandas()
            elif current_role == 'G1_RECRUITMENT_DOMESTIC':
                st.warning("You can create and modify **Scenario Rules** for **Domestic Estimates** changes.")
                course_level_name_df_pd = course_level_name_df.to_pandas()
                owning_faculty_df_pd = owning_faculty_df.to_pandas()
                fee_liability_group_df_pd = fee_liability_group_df.filter(
                    col("FEE_LIABILITY_GROUP_TYPE") == 'Domestic'
                ).to_pandas()
                course_faculty_df_pd = course_faculty_df.to_pandas()
            elif current_role == 'G1_FACULTY_SCI':
                st.warning("You can create and modify **Scenario Rules** for **Faculty of Science and Engineering**.")
                course_level_name_df_pd = course_level_name_df.to_pandas()
                owning_faculty_df_pd = owning_faculty_df.select(
                    col('FACULTY_NAME') == 'Faculty of Science and Engineering'
                ).to_pandas()
                fee_liability_group_df_pd = fee_liability_group_df.to_pandas()
                course_faculty_df_pd = course_faculty_df.to_pandas()
            elif current_role == 'G1_FACULTY_ARTS':
                st.warning("You can create and modify **Scenario Rules** for **Faculty of Arts**.")
                course_level_name_df_pd = course_level_name_df.to_pandas()
                owning_faculty_df_pd = owning_faculty_df.select(
                    col('FACULTY_NAME') == 'Faculty of Arts'
                ).to_pandas()
                fee_liability_group_df_pd = fee_liability_group_df.to_pandas()
                course_faculty_df_pd = course_faculty_df.to_pandas()
            elif current_role == 'G1_FACULTY_MQBS':
                st.warning("You can create and modify **Scenario Rules** for **Macquarie Business School**.")
                course_level_name_df_pd = course_level_name_df.to_pandas()
                owning_faculty_df_pd = owning_faculty_df.select(
                    col('FACULTY_NAME') == 'Macquarie Business School'
                ).to_pandas()
                fee_liability_group_df_pd = fee_liability_group_df.to_pandas()
                course_faculty_df_pd = course_faculty_df.to_pandas()
            elif current_role == 'G1_FACULTY_FMHHS':
                st.warning("You can create and modify **Scenario Rules** for "
                           "**Faculty of Medicine, Health and Human Sciences**.")
                course_level_name_df_pd = course_level_name_df.to_pandas()
                owning_faculty_df_pd = owning_faculty_df.select(
                    col('FACULTY_NAME') == 'Faculty of Medicine, Health and Human Sciences'
                ).to_pandas()
                fee_liability_group_df_pd = fee_liability_group_df.to_pandas()
                course_faculty_df_pd = course_faculty_df.to_pandas()
            else:
                st.error("You don't have permission to access this page.")

            option_period = st.multiselect("## Period (Year)", period_name_list)
            option_owning_faculty = st.multiselect('## Owning Faculty', sorted(owning_faculty_df_pd['FACULTY_NAME']))

            st.session_state['option_owning_faculty'] = option_owning_faculty

            option_course = st.multiselect(
                '## Courses (please choose faculty first)',
                sorted(
                    course_faculty_df_pd[course_faculty_df_pd['FACULTY_NAME'].isin(st.session_state.option_owning_faculty)].COURSE_NAME
                )
            )
            option_fee_liability_group = st.multiselect('## Fee Liability', sorted(fee_liability_group_df_pd['FEE_LIABILITY_GROUP']))
            option_course_level = st.multiselect(
                '## Course Level',
                sorted(
                    course_level_name_df_pd["COURSE_LEVEL_NAME"]
                )
            )
            option_commencing_study_period = st.multiselect('## Commencing Study Period', commencing_study_period_list)
            input_increase_by = st.text_input(
                "## Annual Increse By. e.g, input 0.03 for 3% increasement from previous year.",
                value="0.03"
            )

            if option_period:
                period_name_text = '; '.join(option_period)
                period_name_json = option_period
            else:
                period_name_text = '; '.join(period_name_list)
                period_name_json = period_name_list

            if option_owning_faculty:
                owning_faculty_text = '; '.join(option_owning_faculty)
                owning_faculty_json = option_owning_faculty
            else:
                owning_faculty_text = '; '.join(sorted(owning_faculty_df_pd['FACULTY_NAME']))
                owning_faculty_json = sorted(owning_faculty_df_pd['FACULTY_NAME'])

            if option_fee_liability_group:
                fee_liability_text = '; '.join(option_fee_liability_group)
                fee_liability_json = option_fee_liability_group
            else:
                fee_liability_text = '; '.join(sorted(fee_liability_group_df_pd['FEE_LIABILITY_GROUP']))
                fee_liability_json = sorted(fee_liability_group_df_pd['FEE_LIABILITY_GROUP'])

            if option_course_level:
                course_level_text = '; '.join(option_course_level)
                course_level_json = option_course_level
            else:
                course_level_text = '; '.join(sorted(course_level_name_df_pd['COURSE_LEVEL_NAME']))
                course_level_json = sorted(course_level_name_df_pd['COURSE_LEVEL_NAME'])

            if option_commencing_study_period:
                commencing_study_period_text = '; '.join(option_commencing_study_period)
                commencing_study_period_json = option_commencing_study_period
            else:
                commencing_study_period_text = '; '.join(commencing_study_period_list)
                commencing_study_period_json = commencing_study_period_list

            if option_course:
                course_text = '; '.join(option_course)
                course_json = option_course
            else:
                course_text = f'All courses owned by select faculties ({owning_faculty_text})'
                if option_owning_faculty:
                    course_json = sorted(
                        course_faculty_df_pd[course_faculty_df_pd['FACULTY_NAME'].isin(
                            st.session_state.option_owning_faculty)].COURSE_NAME
                    )
                else:
                    course_json = sorted(course_faculty_df_pd['COURSE_NAME'])
            rule_name = st.text_input("Estimate Rule Name", value="")

            # TODO generate json content for the new rule
            # json generation
            rule_dict = {
                'rule_name': rule_name,
                'increase_by': float(input_increase_by),
                'periods': period_name_json,
                'commencing_study_periods': commencing_study_period_json,
                'owning_faculties': owning_faculty_json,
                'fee_liability_groups': fee_liability_json,
                'course_level_names': course_level_json,
                'courses': course_json,
            }
            with st.expander('Rule Data'):
                st.write(rule_dict)

            estimate_rule_text = (
                f"**New Rule** {rule_name}\n\n"
                f"Increase by {round(float(input_increase_by)*100,4)}% , applying on \n\n"
                f"**Period**: {period_name_text}\n\n"
                f"**Owning Faculty**: {owning_faculty_text}\n\n"
                f"**Fee Liability**: {fee_liability_text}\n\n"
                f"**Course Level**: {course_level_text}\n\n"
                f"**Commencing Study Period**: {commencing_study_period_text}\n\n"
                f"**Course**: {course_text}\n\n"
            )
            description = st.text_area("Estimate Rule Description", estimate_rule_text, height=300, disabled=True)

            extra_comment = st.text_area("Extra Comment", "")

            submit = st.button("Create New Rule")
            if submit:
                try:
                    session.sql(f"""insert into rule (rule_name, description, extra_comment, rule_content, rule_owner)
                    values
                    ('{rule_name}-{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}', '{description}', '{extra_comment}', 
                    '{json.dumps(rule_dict).replace("'", "''")}', '{current_role}' )
                    """).collect()
                    st.success(f"""New Rule **{rule_name}-{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}** is saved""")
                    # TODO reset values in the form
                except Exception as e:
                    st.error('Failed to save the rule')
                    st.error(e)
        elif option_rule_mgmt == 'List Rules':
            st.dataframe(session.table('rule'))


