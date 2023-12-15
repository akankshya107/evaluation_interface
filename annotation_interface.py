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
    # get the text of the article
    article_text = source_articles[summary_id]['story'].replace('\n', '\n\n')
    summary_text = source_articles[summary_id]['summary']
    inconsistency_proof = source_articles[summary_id]['davinci_response']["choices"][0]["message"]["content"].splitlines()

    st.markdown("### Story")
    st.markdown(article_text)
    st.markdown("### Summary")
    st.markdown(summary_text)

    # Load previous evaluation
    outfolder = f"data/annotations/{username}"
    os.makedirs(outfolder, exist_ok=True)
    output_name = os.path.join(outfolder, f"{summary_id}.jsonl")
    selected = dict()

    st.markdown(f"### Summary Evaluation")

    binary_choice_list = ["Yes", "No"]
    selected["consistent"] = st.radio(
        " Is the information in the summary consistent with the story? "
        + "A consistent summary should only include information that can be inferred from the original story. ",
        options=binary_choice_list,
        index=0,
    )

    # create a dictionary to store the annotation
    annotation = {
        "id": summary_id,
        "username": username,
        "story": article_text,
        "summary": summary_text,
        "annotation": selected,
        "expanded" : False,
    }

    # create a submit button and refresh the page when the button is clicked
    if st.button("Submit"):
        # write the annotation to a json file
        os.makedirs("data/annotations", exist_ok=True)
        with open(output_name, "w") as f:
            f.write(json.dumps(annotation) + "\n")
        # display a success message
        st.success("Annotation submitted successfully!")

    with st.expander("See possible AI-generated inconsistency identified in summary"):
        annotation["expanded"] = True
        os.makedirs("data/annotations", exist_ok=True)
        with open(output_name, "w") as f:
            f.write(json.dumps(annotation) + "\n")
        for line in inconsistency_proof:
            st.markdown(line)

        binary_choice_list = ["Yes", "No"]
        selected["consistent_resubmit"] = st.radio(
            " Is the information in the summary consistent with the story? "
            + "A consistent summary should only include information that can be inferred from the original story. "
            + "You can use the inconsistency identified in the summary to help answer this question.",
            options=binary_choice_list,
            index=0,
        )

        binary_choice_list = ["Yes", "No", "N/A"]
        selected["proof_correct"] = st.radio(
            " Is the possible AI-generated inconsistency identified in the summary correct? "
            + "This question can be marked as N/A if the summary is consistent.",
            options=binary_choice_list,
            index=0,
        )
        annotation["annotation"] = selected

        # create a submit button and refresh the page when the button is clicked
        if st.button("Resubmit"):
            # write the annotation to a json file
            os.makedirs("data/annotations", exist_ok=True)
            with open(output_name, "w") as f:
                f.write(json.dumps(annotation) + "\n")
            # display a success message
            st.success("Annotation resubmitted successfully!")

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