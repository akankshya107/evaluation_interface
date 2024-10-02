import os

import streamlit as st
import streamlit_nested_layout
import glob
import json
import nltk

query = st.query_params
to_download = ""
if "download" in query:
    # We can download all files.
    annotations = dict()
    files = glob.glob(pathname="data/annotations/*/*")
    for output_name in files:
        with open(output_name, "r") as file:
            summid = output_name.split('/')[-1].strip(".json")
            st.write(summid)
            try:
                annotations[summid] = json.load(file)
            except:
                st.write("Failed")
                continue

    btn = st.download_button(
            label="Download all annotations",
            data=json.dumps(annotations, indent=4),
            file_name="annotations.json",
        )
# elif any(["username" not in query, "summaryid" not in query]):
#     # display summarization guidelines
#     # load summarization guideline from guideline.md
#     guideline_name = "fine_grained_guildline.md"
#     with open(guideline_name, "r") as f:
#         guideline = f.read()
#     st.markdown(guideline)
else:
    st.set_page_config(layout="wide")
    nltk.download('punkt')
    username = query["username"]
    summary_id = query["summaryid"]
    
    if 'clicked' not in st.session_state:
        st.session_state.clicked = False
    def clicked():
        st.session_state.clicked = True

    col1, col2 = st.columns(2)
    # open the jsonl containing all source articles into a dictionary
    # each line is a json contains two entries: "id" and "text"
    with open(f"storysumm.json", "r") as f:
        source_articles = json.load(f)
    # get the text of the article
    article_text = source_articles[summary_id]['story'].replace('\n', '\n\n')
    summary_text = source_articles[summary_id]['summary']
    errors = source_articles[summary_id]['errors']
    explanations = source_articles[summary_id]['explanations']

    with col1.container(height=700):
        with st.container():
            st.markdown("### Story")
            st.markdown(article_text)
            st.markdown("---")
    with col2.container(height=700):
        with st.container():
            outfolder = f"data/annotations/{username}"
            os.makedirs(outfolder, exist_ok=True)
            output_name = os.path.join(outfolder, f"{summary_id}.json")
            selected = dict()

            st.markdown(f"### Lines/Claims from the LLM-generated Summary")
            if source_articles[summary_id]['label'] == 0:
                st.markdown(f"The summary is judged: :red[Inconsistent] with difficulty: {source_articles[summary_id]['difficulty']}")
            else:
                st.markdown(f"The summary is judged: :green[Consistent] with difficulty: {source_articles[summary_id]['difficulty']}")
            st.markdown("For each line in the summary, annotate if it is ambiguous to evaluate with respect to the story.")
            st.markdown("#### Answers")
            cnt = 0
            for i, line in enumerate(summary_text):
                st.markdown(f"Line {i+1}: {line}")
                if errors[i] == 0:
                    st.markdown(f":red[Reason for inconsistency: {explanations[cnt]}]")
                    cnt += 1
                binary_choice_list = ["Yes", "No", "N/A, just commentary"]
                selected[f"ambiguous_{i}"] = st.radio(
                    "Is this claim ambiguous to evaluate?",
                    key=hash("ambiguous")+i,
                    options=binary_choice_list,
                    index=None,
                )
                if selected[f"ambiguous_{i}"] == "Yes":
                    selected[f"explanation_{i}"] = st.text_area("Provide an explanation for why this line is ambiguous to evaluate.", key=hash("explanation")+i)
                else:
                    selected[f"explanation_{i}"] = ""

            # create a dictionary to store the annotation
            annotation = source_articles[summary_id]
            annotation["username"] = username
            annotation["annotation"] = [selected[f"ambiguous_{i}"] for i in range(len(summary_text))]
            annotation["annotation_explanation"] = [selected[f"explanation_{i}"] for i in range(len(summary_text))]
            # create a submit button and refresh the page when the button is clicked
            if st.button("Submit", on_click=clicked):
                os.makedirs("data/annotations", exist_ok=True)
                with open(output_name, "w") as f:
                    json.dump(annotation, f, indent=4)
                # display a success message
                st.success("Annotation submitted successfully!")
