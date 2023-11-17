import os

import streamlit as st
import glob
import json

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
    guideline_name = "guideline_summary_evaluation.md"
    with open(guideline_name, "r") as f:
        guideline = f.read()
    st.markdown(guideline)

    # open the jsonl containing all source articles into a dictionary
    # each line is a json contains two entries: "id" and "text"
    with open("responses_gpt-4_-3518530352341467729.json", "r") as f:
        source_articles = json.load(f)
        # turn the list of jsons into a dictionary
        source_articles = {article["id"]: article for article in source_articles}
    # print(source_articles.keys())
    # get the text of the article
    article_text = source_articles[summary_id]['story'].replace('\n', '\n\n')
    summary_text = source_articles[summary_id]['summary']
    inconsistency_proof = source_articles[summary_id]['davinci_response']["choices"][0]["message"]["content"].splitlines()

    st.markdown("### Story")
    st.markdown(article_text)
    st.markdown("### Summary")
    st.markdown(summary_text)
    st.markdown('### Possible inconsistency identified in summary')
    for line in inconsistency_proof:
        st.markdown(line)

    # Load previous evaluation
    outfolder = f"data/annotations/{username}"
    os.makedirs(outfolder, exist_ok=True)
    output_name = os.path.join(outfolder, f"{summary_id}.jsonl")
    if os.path.exists(output_name):
        with open(output_name, "r") as f:
            prev_eval = json.loads(f.readlines()[-1])
    else:
        prev_eval = None

    selected = dict()

    st.markdown(f"### Summary Evaluation")

    binary_choice_list = ["Yes", "No"]
    selected["consistent"] = st.radio(
        " Is the information in the summary consistent with the story? "
        + "A consistent summary should only include information that can be inferred from the original story. "
        + "Ignore any commentary for this question. Use the inconsistency identified in the summary as an aid to this question.",
        options=binary_choice_list,
        index=0
        if prev_eval is None
        else binary_choice_list.index(prev_eval["annotation"]["consistent"]),
    )

    binary_choice_list = ["Yes", "No", "N/A"]
    selected["proof_correct"] = st.radio(
        " Is the possible inconsistency identified in the summary correct? "
        + "This question can be marked as N/A if the summary is consistent.",
        options=binary_choice_list,
        index=0
        if prev_eval is None
        else binary_choice_list.index(prev_eval["annotation"]["proof_correct"]),
    )

    binary_choice_list = ["Yes", "No", "N/A"]
    selected["proof_used"] = st.radio(
        " Did the possible inconsistency identified in the summary aid in the answer to the first question? "
        + "This question can be marked as N/A if the summary is consistent.",
        options=binary_choice_list,
        index=0
        if prev_eval is None
        else binary_choice_list.index(prev_eval["annotation"]["proof_used"]),
    )

    # binary_choice_list = ["Yes", "No", "N/A"]
    # selected["commentary"] = st.radio(
    #     " If the summary contains any commentary or inferences about the story, is it consistent with how you read the story? ",
    #     options=binary_choice_list,
    #     index=0
    #     if prev_eval is None
    #     else binary_choice_list.index(prev_eval["annotation"]["commentary"]),
    # )

    # binary_choice_list = ["1", "2", "3", "4"]
    # selected["coherent"] = st.radio(
    #     " Is the summary coherent? "
    #     + "A coherent summary should have sentences that flow together nicely into a paragraph. ",
    #     options=binary_choice_list,
    #     horizontal=True,
    #     index=0
    #     if prev_eval is None
    #     else binary_choice_list.index(prev_eval["annotation"]["coherent"]),
    # )

    # binary_choice_list = ["1", "2", "3", "4"]
    # selected["narrative"] = st.radio(
    #     "  Does the summary capture the overall point of the narrative?",
    #     options=binary_choice_list,
    #     horizontal=True,
    #     index=0
    #     if prev_eval is None
    #     else binary_choice_list.index(prev_eval["annotation"]["narrative"]),
    # )

    # create a dictionary to store the annotation
    annotation = {
        "id": summary_id,
        "username": username,
        "story": article_text,
        "summary": summary_text,
        "annotation": selected,
    }

    # create a submit button and refresh the page when the button is clicked
    if st.button("Submit"):
        # write the annotation to a json file
        os.makedirs("data/annotations", exist_ok=True)
        with open(output_name, "a") as f:
            f.write(json.dumps(annotation))
        # display a success message
        st.success("Annotation submitted successfully!")

else:
    # We can download all files.
    annotations = []
    files = glob.glob(pathname="data/annotations/*/*")
    for output_name in files:
        with open(output_name, "r") as file:
            st.write(output_name)
            annotations.append(json.loads(file.readline()))

    btn = st.download_button(
            label="Download all annotations",
            data=json.dumps(annotations, indent=2),
            file_name="annotations.json",
        )