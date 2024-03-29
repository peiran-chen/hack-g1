use database hackathon;
use schema group_1;

create table scenario if not exists (
    id number(38) identity,
    scenario_name varchar(100),
    version_name varchar(100), -- a date and timestamp
    is_final varchar(1) default 'N', -- [Y|N]
    confirmed_by_arts varchar(1) default 'N',
    confirmed_by_mqbs varchar(1) default 'N',
    confirmed_by_sci varchar(1) default 'N',
    confirmed_by_fmhhs varchar(1) default 'N',
    notes varchar,
    created_by varchar(100),
    created_at timestamp(6),
    updated_by varchar(100),
    updated_at timestamp(6)
);

comment on table scenario is 'Estimate Scenario. composite business key scenario_name, version_name';

-- to save comments for better collabration
create table scenario_notes if not exists (
    id number(38) identity,
    scenario_id number(38),
    notes varchar,
    created_by varchar(100),
    created_at timestamp(6)
);

comment on table scenario_notes is 'Notes and Comments associated with Scenario for better collabration'

create table scenario_data if not exists (
    id number(38) identity,
    scenario_id number(38),
    course varchar(100),
    period varchar(100),
    commencing_study_period varchar(100),
    owning_faculty_name varchar(200),
    course_level_name varchar(100),
    fee_liability_group varchar(100),
    course_enrolment_count number(38)
);


create table ref_course (
    id number(38) identity,
    course_code varchar(50),
    course_name varchar(300),
    owning_faculty_id number(38),
    active_from date,
    active_to date
);


create table ref_period (
    id number(38) identity,
    period_name varchar(300)
);

create table ref_owning_faculty (
    id number(38) identity,
    faculty_code varchar(50),
    faculty_name varchar(100)
);

create table ref_course_level (
    id number(38) identity,
    course_level_name varchar(50)
);

create table ref_fee_liability_group (
    id number(38) identity,
    fee_liability_group varchar(100),
    fee_liability_group_type varchar(50)
);

create table ref_commencing_study_period (
    id number(38) identity,
    commencing_study_period varchar(100)
);

create table if not exists rule_annual_increase (
    id number(38) identity,
    default_annual_increase float
)
;

create table if not exists rule (
    id number(38) identity,
    rule_name varchar(100),
    description varchar(4000),
    extra_comment varchar(4000),
    rule_content varchar,
    rule_owner varchar(100),
    created_by varchar(100),
    created_at timestamp(6),
    updated_by varchar(100),
    updated_at timestamp(6)
);

comment on column rule.rule_content is 'json content to combine lists of owning faculty, fee liability group, course level, period, commencing study period and courses';

