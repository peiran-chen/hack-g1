use role accountadmin;
-- admin role
create role if not exists g1_admin;
-- recruitment staff role
create role if not exists g1_recruitment_international;
create role if not exists g1_recruitment_domestic;
-- faculty role
create role if not exists g1_faculty_sci;
create role if not exists g1_faculty_arts;
create role if not exists g1_faculty_mqbs;
create role if not exists g1_faculty_fmhhs;

create role if not exists g1_role;

grant role g1_role to role g1_admin;
grant role g1_role to role g1_recruitment_international;
grant role g1_role to role g1_recruitment_domestic;
grant role g1_role to role g1_faculty_sci;
grant role g1_role to role g1_faculty_arts;
grant role g1_role to role g1_faculty_mqbs;
grant role g1_role to role g1_faculty_fmhhs;


-- warehouse for team 1
create warehouse if not exists g1_wh;

grant usage on warehouse g1_wh to role g1_admin;
grant usage on warehouse g1_wh to role g1_recruitment_international;
grant usage on warehouse g1_wh to role g1_recruitment_domestic;
grant usage on warehouse g1_wh to role g1_faculty_sci;
grant usage on warehouse g1_wh to role g1_faculty_arts;
grant usage on warehouse g1_wh to role g1_faculty_mqbs;
grant usage on warehouse g1_wh to role g1_faculty_fmhhs;

-- users
create user if not exists g1_admin password='***' login_name="g1_admin" email="peiran.chen@mq.edu.au" default_role=g1_admin default_warehouse=g1_wh;
create user if not exists g1_recruitment_international password='***' login_name="g1_recruitment_international" email="peiran.chen@mq.edu.au" default_role=g1_recruitment_international default_warehouse=g1_wh;
create user if not exists g1_recruitment_domestic password='***' login_name="g1_recruitment_domestic" email="peiran.chen@mq.edu.au" default_role=g1_recruitment_domestic default_warehouse=g1_wh;
create user if not exists g1_faculty_sci password='***' login_name="g1_faculty_sci" email="peiran.chen@mq.edu.au" default_role=g1_faculty_sci default_warehouse=g1_wh;
create user if not exists g1_faculty_arts password='***' login_name="g1_faculty_arts" email="peiran.chen@mq.edu.au" default_role=g1_faculty_arts default_warehouse=g1_wh;
create user if not exists g1_faculty_mqbs password='***' login_name="g1_faculty_mqbs" email="peiran.chen@mq.edu.au" default_role=g1_faculty_mqbs default_warehouse=g1_wh;
create user if not exists g1_faculty_fmhhs password='***' login_name="g1_faculty_fmhhs" email="peiran.chen@mq.edu.au" default_role=g1_faculty_fmhhs default_warehouse=g1_wh;

-- grants
grant role g1_admin to user g1_admin;
grant role g1_recruitment_international to user g1_recruitment_international;
grant role g1_recruitment_domestic to user g1_recruitment_domestic;
grant role g1_faculty_sci to user g1_faculty_sci;
grant role g1_faculty_arts to user g1_faculty_arts;
grant role g1_faculty_mqbs to user g1_faculty_mqbs;
grant role g1_faculty_fmhhs to user g1_faculty_fmhhs;

grant usage on database hackathon to role g1_admin;
grant usage on database hackathon to role g1_recruitment_international;
grant usage on database hackathon to role g1_recruitment_domestic;
grant usage on database hackathon to role g1_faculty_sci;
grant usage on database hackathon to role g1_faculty_arts;
grant usage on database hackathon to role g1_faculty_mqbs;
grant usage on database hackathon to role g1_faculty_fmhhs;

grant usage on schema hackathon.group_1 to role g1_admin;
grant usage on schema hackathon.group_1 to role g1_recruitment_international;
grant usage on schema hackathon.group_1 to role g1_recruitment_domestic;
grant usage on schema hackathon.group_1 to role g1_faculty_sci;
grant usage on schema hackathon.group_1 to role g1_faculty_arts;
grant usage on schema hackathon.group_1 to role g1_faculty_mqbs;
grant usage on schema hackathon.group_1 to role g1_faculty_fmhhs;

grant usage on warehouse g1_wh to role g1_admin;
grant usage on warehouse g1_wh to role g1_recruitment_international;
grant usage on warehouse g1_wh to role g1_recruitment_domestic;
grant usage on warehouse g1_wh to role g1_faculty_sci;
grant usage on warehouse g1_wh to role g1_faculty_arts;
grant usage on warehouse g1_wh to role g1_faculty_mqbs;
grant usage on warehouse g1_wh to role g1_faculty_fmhhs;
