import streamlit as st

st.header("This is the UI for RFP Analyser")

file = st.file_uploader("Walla!!! Upload RFP here.")

st.write(file)