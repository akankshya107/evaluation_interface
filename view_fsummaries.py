import os

import streamlit as st
import streamlit_nested_layout
import glob
import json
import nltk
import csv

query = st.query_params
st.set_page_config(layout="wide")
nltk.download('punkt')
username = query["username"]
summary_id = query["summaryid"]
peek = query["peek"]

if 'clicked' not in st.session_state:
    st.session_state.clicked = False
def clicked():
    st.session_state.clicked = True

col1, col2 = st.columns(2)
# open the jsonl containing all source articles into a dictionary
# each line is a json contains two entries: "id" and "text"
with open(f"fsummaries.json", "r") as f:
    source_articles = json.load(f)
# get the text of the article
article_text = source_articles[summary_id]['story'].replace('\n', '\n\n')
summary_text = source_articles[summary_id]['fsummary']
is_subj = source_articles[summary_id]['fsummary_subj']
themes = source_articles[summary_id]['fsummary_themes']

with col1.container(height=700):
    with st.container():
        st.markdown("### Story")
        st.markdown(article_text)
        st.markdown("---")
with col2.container(height=700):
    with st.container():
        selected = dict()
        for i, line in enumerate(summary_text):
            if peek == '1':
                if is_subj[i] == 1:
                    st.markdown(f":red[Theme {themes[i]}: {line}]")
                else:
                    st.markdown(f":green[{line}]")
            else:
                st.markdown(line)
