import time
import streamlit as st
from shared.constants import SERVER, ServerType
from utils.common_utils import get_current_user
from ui_components.components.query_logger_page import query_logger_page

from utils.data_repo.data_repo import DataRepo


def app_settings_page():
    data_repo = DataRepo()

    st.markdown("#### App Settings")
    st.markdown("***")
            
    if SERVER != ServerType.DEVELOPMENT.value:
        with st.expander("Purchase Credits", expanded=True):
            user_credits = get_current_user(invalidate_cache=True).total_credits
            user_credits = round(user_credits, 2) if user_credits else 0
            st.write(f"Total Credits: {user_credits}")
            c1, c2 = st.columns([1,1])
            with c1:
                if 'input_credits' not in st.session_state:
                    st.session_state['input_credits'] = 10

                credits = st.number_input("Credits (1 credit = $1)", value = st.session_state['input_credits'], step = 10)
                if credits != st.session_state['input_credits']:
                    st.session_state['input_credits'] = credits
                    st.rerun()

                if st.button("Generate payment link"):
                    if credits < 10:
                        st.error("Minimum credit value should be atleast 10")
                        time.sleep(0.7)
                        st.rerun()
                    else:
                        payment_link = data_repo.generate_payment_link(credits)
                        payment_link = f"""<a target='_self' href='{payment_link}'> PAYMENT LINK </a>"""
                        st.markdown(payment_link, unsafe_allow_html=True)
    
    # TODO: rn storing 'update_state' in replicate_username inside app_setting to bypass db changes, will change this later
    app_setting = data_repo.get_app_setting_from_uuid()
    update_enabled = True if app_setting.replicate_username and app_setting.replicate_username in ['update', 'bn'] else False
    with st.expander("App Update", expanded=True):
        
        # st.info("We recommend auto-updating the app to get the latest features and bug fixes. However, if you'd like to update manually, you can turn this off and use './scripts/entrypoint.sh --update' when you're starting the app to update.")
        st.toggle("Auto-update app upon restart", key='enable_app_update', value=update_enabled, on_change=update_toggle, help="This will update the app automatically when a new version is available.")

    with st.expander("Inference Logs", expanded=False):
        query_logger_page()

def update_toggle():
    data_repo = DataRepo()
    data_repo.update_app_setting(replicate_username='update' if st.session_state['enable_app_update'] else 'no_update')