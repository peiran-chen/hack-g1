# Streamlit hackathon app

## To run

Setup virtualenv:

```bash
python3 -m venv venv
source ./venv/bin/activate
pip install --requirement requirements.txt
```

Create `secrets.toml` (change `account` and `user`):

```bash
mkdir .streamlit
cat > .streamlit/secrets.toml <<'EOT'
[connections.snowflake]
account = "vd12345-example"
user = "john.smith@example.com"
authenticator = "EXTERNALBROWSER"
EOT
```

Start app:

```bash
./start-app.sh
```

## To deploy

```bash
SNOWSQL_PWD='0*******o' snowsql --accountname 'vd12345-hackathon' --username 'jsmith' --dbname 'hackathon' --schemaname 'group_1' --warehouse 'compute_wh' --rolename 'ACCOUNTADMIN'
drop stage hackathon.group_1.streamlit_stage;
create or replace stage hackathon.group_1.streamlit_stage;
PUT 'file:///home/klo/Projects/mq/hack-g1/1_Commence_Estimates.py' @hackathon.group_1.streamlit_stage overwrite=true auto_compress=false;
PUT 'file:///home/klo/Projects/mq/hack-g1/environment.yml' @hackathon.group_1.streamlit_stage overwrite=true auto_compress=false;
PUT 'file:///home/klo/Projects/mq/hack-g1/pages/2_Dashboard.py' @hackathon.group_1.streamlit_stage/pages overwrite=true auto_compress=false;
PUT 'file:///home/klo/Projects/mq/hack-g1/pages/3_Reference_Data.py' @hackathon.group_1.streamlit_stage/pages overwrite=true auto_compress=false;
PUT 'file:///home/klo/Projects/mq/hack-g1/pages/4_Rule_Settings.py' @hackathon.group_1.streamlit_stage/pages overwrite=true auto_compress=false;
PUT 'file:///home/klo/Projects/mq/hack-g1/pages/5_Scenario_Management.py' @hackathon.group_1.streamlit_stage/pages overwrite=true auto_compress=false;
```

```sql
create or replace streamlit group_1
root_location = '@hackathon.group_1.streamlit_stage'
main_file = '/1_Commence_Estimates.py'
query_warehouse = 'compute_wh';


-- create or replace streamlit kokyantest
-- root_location = '@hackathon.group_1.streamlit_stage'
-- main_file = '/1_📓_Commence_Estimates.py'
-- query_warehouse = 'compute_wh';

-- SHOW STREAMLITS;
-- DESC STREAMLIT kokyantest;
-- ALTER STREAMLIT kokyantest RENAME TO group_1;
-- DROP STREAMLIT group_1;
```