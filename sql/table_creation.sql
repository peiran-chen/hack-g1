use database hachathon;
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


create table scenario_notes if not exists (
    id number(38) identity,
    scenario_id number(38),
    notes varchar,
    created_by varchar(100),
    created_at timestamp(6)
);

create table scenario_data if not exists (
    id number(38) identity,
    scenario_id number(38),
    course varchar(100),
    period varchar(100),
    commencing_study_period varchar(100),
    owning_faculty_name varchar(100),
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


