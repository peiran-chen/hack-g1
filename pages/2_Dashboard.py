import streamlit as st
from snowflake.snowpark.context import get_active_session
from snowflake.snowpark import Session
from snowflake.snowpark.functions import col, sql_expr, sum
import pandas as pd
import altair as alt
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


def get_ce():
    """
    scenario_type

    Final
    2023 Budget
    2023 CD1R
    2024 Load Plan 1.0
    2024 Load Plan 2.0
    """
    sql_expr_str = """
    scenario_type in ('Final', '2023 Budget', '2023 CD1R', '2024 Load Plan 1.0', '2024 Load Plan 2.0')
and (period_name in ('2023', '2024', '2025', '2026', '2027', '2028') or period_name like '%Final' )"""
    dim_list = [
        'scenario_type',
        'period_name',
        'course_name',
        'owning_faculty',
        'commencing_study_period',
        'course_level_name',
        'fee_liability_group'
    ]
    measure = 'course_enrolment_count'

    ce_df = session.table('DATA_SOURCE.COMMENCING_ESTIMATES.DRAFT_LP_CE_ESTIMATES_2024') \
        .select([*dim_list, measure]) \
        .filter(sql_expr(sql_expr_str)) \
        .group_by(dim_list).agg(sum(col(measure)).alias(measure))

    return ce_df


ce_df = get_ce().to_pandas()
ce_df["COURSE_ENROLMENT_COUNT"] = ce_df["COURSE_ENROLMENT_COUNT"].fillna(0).astype('int')

filtered_df = ce_df.copy()

st.sidebar.markdown("""
    <style>
    [data-testid='stSidebarNav'] > ul {
        min-height: 40vh;
    } 
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    # course filter on sidebar
    course_df = pd.DataFrame(sorted(ce_df["COURSE_NAME"].unique()), columns=['COURSE_NAME'])
    unique_course_name = course_df
    filter_course_name = st.multiselect("## Course Name", unique_course_name)

    if filter_course_name:
        filtered_df = filtered_df[filtered_df["COURSE_NAME"].isin(filter_course_name)]
    else:
        filtered_df = filtered_df

    # owning_faculty filter on sidebar
    unique_owning_faculty = sorted(ce_df["OWNING_FACULTY"].unique())
    filter_owning_faculty = st.multiselect('## Owning Faculty', unique_owning_faculty)
    if filter_owning_faculty:
        filtered_df = filtered_df[filtered_df["OWNING_FACULTY"].isin(filter_owning_faculty)]
    else:
        filtered_df = filtered_df

    # course_level_name filter on sidebar
    unique_course_level_name = sorted(ce_df["COURSE_LEVEL_NAME"].unique())
    filter_course_level_name = st.multiselect('## Course Level', unique_course_level_name)
    if filter_course_level_name:
        filtered_df = filtered_df[filtered_df["COURSE_LEVEL_NAME"].isin(filter_course_level_name)]
    else:
        filtered_df = filtered_df

    # fee_liability_group filter on sidebar
    unique_fee_liability_group = sorted(ce_df["FEE_LIABILITY_GROUP"].unique())
    filter_fee_liability_group = st.multiselect('## Fee Liability Group', unique_fee_liability_group)
    if filter_fee_liability_group:
        filtered_df = filtered_df[filtered_df["FEE_LIABILITY_GROUP"].isin(filter_fee_liability_group)]
    else:
        filtered_df = filtered_df

    # scenario_type filter on sidebar
    unique_scenario_type = ['2023 Budget', '2023 CD1R', '2024 Load Plan 1.0', '2024 Load Plan 2.0', 'Final']
    filter_scenario_type = st.multiselect('## Scenario Type', unique_scenario_type, default=unique_scenario_type)

    if filter_scenario_type:
        if 'Final' not in filter_scenario_type:
            filter_scenario_type.append('Final')
    else:
        filter_scenario_type = unique_scenario_type

    filtered_df = filtered_df[filtered_df["SCENARIO_TYPE"].isin(filter_scenario_type)]

    current_role = session.get_current_role().replace('"', '')
    st.warning(f"Login Role **{current_role}**")

st.title(":chart_with_upwards_trend: Dashboard")

col1, col2 = st.columns(2)
with col1:
    st.subheader('Actuals')
with col2:
    st.subheader('Estimates')

actual_ce_df_sum = filtered_df[filtered_df["SCENARIO_TYPE"] == "Final"].groupby("PERIOD_NAME")[
    "COURSE_ENROLMENT_COUNT"].sum().reset_index()

ce_df_sum = filtered_df[filtered_df["SCENARIO_TYPE"].isin(
    ['2023 Budget', '2023 CD1R', '2024 Load Plan 1.0', '2024 Load Plan 2.0', 'Final'])].groupby(
    ["SCENARIO_TYPE", "PERIOD_NAME"])["COURSE_ENROLMENT_COUNT"].sum().reset_index()

ce_df_sum_term = filtered_df[filtered_df["SCENARIO_TYPE"].isin(
    ['2023 Budget', '2023 CD1R', '2024 Load Plan 1.0', '2024 Load Plan 2.0', 'Final'])].groupby(
    ["SCENARIO_TYPE", "PERIOD_NAME", "COMMENCING_STUDY_PERIOD"])["COURSE_ENROLMENT_COUNT"].sum().reset_index()

estimate_ce_df_sum = ce_df_sum[
    ce_df_sum["SCENARIO_TYPE"].isin(['2023 Budget', '2023 CD1R', '2024 Load Plan 1.0', '2024 Load Plan 2.0'])]

scale_range = [0, 100]
if not ce_df_sum.empty:
    scale_range = [ce_df_sum["COURSE_ENROLMENT_COUNT"].min() * 0.9, ce_df_sum["COURSE_ENROLMENT_COUNT"].max() * 1.1]

line_chart = alt.Chart(ce_df_sum).mark_line(point=alt.OverlayMarkDef(filled=False, fill="white", tooltip=True)).encode(
    x=alt.X('PERIOD_NAME:N', title="Period Name", scale=alt.Scale(), axis=alt.Axis(labelAngle=-45)),
    y=alt.Y(
        'COURSE_ENROLMENT_COUNT:Q',
        title="Course Enrolment Count",
        scale=alt.Scale(domain=scale_range)
    ),
    color='SCENARIO_TYPE:N'
)

st.altair_chart(line_chart, use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    with st.expander('View Data'):
        st.dataframe(actual_ce_df_sum)

with col2:
    with st.expander('View Data'):
        estimate_ce_df_sum_pivot = estimate_ce_df_sum.pivot(index="SCENARIO_TYPE", columns="PERIOD_NAME",
                                                            values="COURSE_ENROLMENT_COUNT")
        for c in estimate_ce_df_sum_pivot.columns:
            estimate_ce_df_sum_pivot[c] = estimate_ce_df_sum_pivot[c].fillna(0).astype('int')
        estimate_ce_df_sum_pivot = estimate_ce_df_sum_pivot.reset_index()
        st.dataframe(estimate_ce_df_sum_pivot)
        ce_df_sum_term_filter = ce_df_sum_term[ce_df_sum_term['SCENARIO_TYPE'].isin(estimate_ce_df_sum_pivot['SCENARIO_TYPE'])]
        ce_df_sum_term_pivot = ce_df_sum_term_filter.pivot(
            index=["SCENARIO_TYPE", "PERIOD_NAME"],
            columns="COMMENCING_STUDY_PERIOD",
            values="COURSE_ENROLMENT_COUNT",
        )
        ce_df_sum_term_pivot['Total'] = ce_df_sum_term_pivot.sum(axis=1)
        for c in ce_df_sum_term_pivot.columns:
            ce_df_sum_term_pivot[c] = ce_df_sum_term_pivot[c].fillna(0).astype('int')
        st.dataframe(ce_df_sum_term_pivot, )

