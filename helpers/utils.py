import streamlit as st
from snowflake.snowpark import Session

class Utils:
  @staticmethod
  def get_session():
    def create_session():
      # Snowflake session
      try:
          return get_active_session()
      except Exception as e:
          None
      # Use local session
      if 'snowflake' in st.secrets:
          return Session.builder.configs(st.secrets.snowflake).create()
      # Current connection method
      elif 'connection' in dir(st):
          return st.connection("snowflake").session()
      # 1.22
      elif 'experimental_connection' in dir(st):
          return st.experimental_connection("snowpark").session()
      else:
          raise 'Session not detected'

    if 'session' not in st.session_state:
        session = create_session()
        st.session_state['session'] = session
    else:
        session = st.session_state.session

    return session

  @staticmethod
  def get_session_role():
    session = Utils.get_session()
    return session.get_current_role().replace('"', '')
