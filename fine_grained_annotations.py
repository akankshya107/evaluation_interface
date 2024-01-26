import os

import streamlit as st
import streamlit_nested_layout
import glob
import json
import nltk

query = st.experimental_get_query_params()
to_download = ""
if "download" in query:
    to_download = query["download"][0]
elif any(["username" not in query, "summaryid" not in query]):
    st.error("Ill-formatted url. Please enter the url we provided")
    st.stop()
else:
    username = query["username"][0]
    summary_id = query["summaryid"][0]

if not to_download:
    # display summarization guidelines
    # load summarization guideline from guideline.md
    guideline_name = "fine_grained_guildline.md"
    with open(guideline_name, "r") as f:
        guideline = f.read()
    st.markdown(guideline)
    nltk.download('punkt')
    # Initialize the key in session state
    if 'clicked' not in st.session_state:
        st.session_state.clicked = False
    def clicked():
        st.session_state.clicked = True

    # open the jsonl containing all source articles into a dictionary
    # each line is a json contains two entries: "id" and "text"
    with open("responses_gpt-4_-3518530352341467729.json", "r") as f:
        source_articles = json.load(f)
        # turn the list of jsons into a dictionary
        source_articles = {article["id"]: article for article in source_articles}
    # get the text of the article
    article_text = source_articles[summary_id]['story'].replace('\n', '\n\n')
    summary_text = source_articles[summary_id]['summary']
    inconsistency_proof = source_articles[summary_id]['davinci_response']["choices"][0]["message"]["content"].splitlines()

    st.markdown("### Story")
    st.markdown(article_text)
    st.markdown("### Summary")
    st.markdown(summary_text)

    outfolder = f"data/annotations/{username}"
    os.makedirs(outfolder, exist_ok=True)
    output_name = os.path.join(outfolder, f"{summary_id}.jsonl")
    selected = dict()

    st.markdown(f"### Summary Evaluation")
    st.markdown("For each line in the summary, evaluate if it is consistent with the story.")
    st.markdown("Along with the selected input, you can provide an explanation as to why you selected a particular answer, *if you mark the line as inconsistent to the story*. When evaluating, remember that the events and details described in a consistent summary should not misrepresent details from the story or include details that are unsupported by the story.")
    st.markdown("#### Answers")
    for i, line in enumerate(nltk.tokenize.sent_tokenize(summary_text)):
        st.markdown(f"Line {i+1}: {line}")
        binary_choice_list = ["Yes", "No", "N/A, just commentary"]
        selected[f"consistent_{i}"] = st.radio(
            "Is this line in the summary consistent with the story?",
            key=hash("consistent")+i,
            options=binary_choice_list,
            index=None,
        )
        if selected[f"consistent_{i}"] == "No":
            selected[f"explanation_{i}"] = st.text_area("Provide an explanation for your selection.", key=hash("explanation")+i)

    st.markdown("---")
    binary_choice_list = ["Yes", "No"]
    selected["consistent_full"] = st.radio(
        "Overall, is the information in the summary consistent with the story? "
        + "The events and details described in a consistent summary should not misrepresent details from the story or include details that are unsupported by the story. ",
        options=binary_choice_list,
        index=None,
    )
    selected[f"explanation_full"] = st.text_area("Provide an explanation for your selection.")
    # create a dictionary to store the annotation
    annotation = {
        "id": summary_id,
        "username": username,
        "story": article_text,
        "summary": summary_text,
        "annotation": selected,
    }
    # create a submit button and refresh the page when the button is clicked
    if st.button("Submit", on_click=clicked):
        os.makedirs("data/annotations", exist_ok=True)
        with open(output_name, "w") as f:
            f.write(json.dumps(annotation) + "\n")
        # display a success message
        st.success("Annotation submitted successfully!")

else:
    # We can download all files.
    st.write("Only the latest annotations are available.")
    annotations = []
    files = glob.glob(pathname="data/annotations/*/*")
    for output_name in files:
        with open(output_name, "r") as file:
            st.write(output_name)
            try:
                annotations.append(json.loads(file.readlines()[-1]))
            except:
                st.write("Failed")
                continue

    btn = st.download_button(
            label="Download all annotations",
            data=json.dumps(annotations, indent=2),
            file_name="annotations.json",
        )
