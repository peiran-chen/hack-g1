from snowflake.snowpark import Row, Session
from helpers.utils import Utils
class Scenario:

  @staticmethod
  def find(id: int):
    session = Utils.get_session()
    row = session.sql('select * from scenario where id=?', params=[id]).collect()[0].as_dict()
    scenario = Scenario()
    # Set attributes
    for column_name in row.keys():
      setattr(scenario, column_name.lower(), row[column_name])
    return scenario

  @staticmethod
  def find_by_ui_value(scenario_text: str):
    session = Utils.get_session()
    row = session.sql("select * from scenario where SCENARIO_NAME||' - '||VERSION_NAME = ?", params=[scenario_text]).collect()[0].as_dict()
    return Scenario.find(row['ID'])

  def __init__(self):
    self.id = None
    self.scenario_name = None
    self.version_name = None
    self.is_final = None
    self.confirmed_by_arts = None
    self.confirmed_by_mqbs = None
    self.confirmed_by_sci = None
    self.confirmed_by_fmhhs = None
    self.notes = None
    self.created_by = None
    self.created_at = None
    self.updated_by = None
    self.updated_at = None

  def __str__(self):
    return self.__dict__.__str__()

  def testFn(self):
    session = Utils.get_session()
    results = session.sql('select current_user').to_pandas().to_csv()
    return 'Test Fn text'

  def testFn(self):
    session = Utils.get_session()
    results = session.sql('select current_user').to_pandas().to_csv()
    return 'Test Fn text'


  def approve(self):
    role = Utils.get_session_role()
    if role == 'G1_FACULTY_ARTS':
        self.confirmed_by_arts = 'Y'
    elif role == 'G1_FACULTY_MQBS':
        self.confirmed_by_mqbs = 'Y'
    elif role == 'G1_FACULTY_SCI':
        self.confirmed_by_sci = 'Y'
    elif role == 'G1_FACULTY_FMHHS':
        self.confirmed_by_fmhhs = 'Y'
    elif role in ('ACCOUNTADMIN', 'G1_ADMIN'):
        self.is_final = 'Y'
    else:
        raise f"No role match: {role}"

    self.save()

  def has_role_approved(self):
    role = Utils.get_session_role()
    if role == 'G1_FACULTY_ARTS':
        return self.confirmed_by_arts == 'Y'
    elif role == 'G1_FACULTY_MQBS':
        return self.confirmed_by_mqbs == 'Y'
    elif role == 'G1_FACULTY_SCI':
        return self.confirmed_by_sci == 'Y'
    elif role == 'G1_FACULTY_FMHHS':
        return self.confirmed_by_fmhhs == 'Y'
    elif role in ('ACCOUNTADMIN', 'G1_ADMIN'):
        return self.is_final == 'Y'
    else:
        raise f"No role match: {role}"


  def save(self):
    session = Utils.get_session()
    tbl = session.table('scenario')
    tbl.update(
      {
        'SCENARIO_NAME': self.scenario_name,
        'VERSION_NAME': self.version_name,
        'IS_FINAL': self.is_final,
        'CONFIRMED_BY_ARTS': self.confirmed_by_arts,
        'CONFIRMED_BY_MQBS': self.confirmed_by_mqbs,
        'CONFIRMED_BY_SCI': self.confirmed_by_sci,
        'CONFIRMED_BY_FMHHS': self.confirmed_by_fmhhs,
        'NOTES': self.notes,
        'CREATED_BY': self.created_by,
        'CREATED_AT': self.created_at,
        'UPDATED_BY': self.updated_by,
        'UPDATED_AT': self.updated_at
      },
      tbl['ID'] == self.id
    )
