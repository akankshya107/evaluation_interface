import os

import streamlit as st
import glob
import json
import re

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
    guideline_name = "inconsistency_annotation.md"
    with open(guideline_name, "r") as f:
        guideline = f.read()
    st.markdown(guideline)

    # open the jsonl containing all source articles into a dictionary
    # each line is a json contains two entries: "id" and "text"
    hashes = ["6058720284769771861", "-3518530352341467729"]
    source = list()
    for hash_val in hashes:
        with open(f"responses_gpt-4_{hash_val}.json", "r") as f:
            source_articles = json.load(f)
            # turn the list of jsons into a dictionary
            source_articles = {article["id"]: article for article in source_articles}
            source.append(source_articles[summary_id])
    # get the text of the article
    article_text = source[0]['story'].replace('\n', '\n\n')
    summary_text = source[0]['summary']

    st.markdown("### Story")
    st.markdown(article_text)
    st.markdown("### Summary")
    st.markdown(summary_text)

    outfolder = f"data/annotations/{username}"
    os.makedirs(outfolder, exist_ok=True)
    output_name = os.path.join(outfolder, f"{summary_id}.jsonl")

    st.markdown(f"### Summary Evaluation")

    st.markdown('##### Possible AI-generated inconsistencies detected in summary')
    regex = r"(^.*)\n+[Reason]"
    
    inconsistency_proof = source[0]['davinci_response']["choices"][0]["message"]["content"] + "\n" + source[1]['davinci_response']["choices"][0]["message"]["content"]
    selected = dict()
    if re.search(regex, inconsistency_proof) is not None:
        matches = re.finditer(regex, inconsistency_proof, re.MULTILINE)
        for idx, match in enumerate(matches):
            if len(match.group(1)):
                st.markdown("Detected " + match.group(1))
                binary_choice_list = ["Explain why you think this detected inconsistency is correct.", "Explain why you think this detected inconsistency is incorrect."]
                selected[f"correct_{idx}"] = st.radio(
                    "",
                    key=hash("correct")+idx,
                    options=binary_choice_list,
                    index=None,
                    label_visibility="collapsed"
                )
                if selected[f"correct_{idx}"]:
                    selected[f"arg_{idx}"] = st.text_area("", key=hash("arg")+idx, label_visibility="collapsed")
                st.markdown("---")
    else:
        st.markdown("Detected " + inconsistency_proof)
        binary_choice_list = ["Explain why you think this detected inconsistency is correct.", "Explain why you think this detected inconsistency is incorrect."]
        selected[f"correct"] = st.radio(
            "",
            key=hash("correct"),
            options=binary_choice_list,
            index=None,
            label_visibility="collapsed"
        )
        if selected[f"correct"]:
            selected[f"arg"] = st.text_area("", key=hash("arg"), label_visibility="collapsed")
        st.markdown("---")

    binary_choice_list = ["Yes", "No"]
    selected["consistent"] = st.radio(
        "Overall, is the information in the summary consistent with the story? "
        + "The events and details described in a consistent summary should not misrepresent details from the story or include details that are unsupported by the story.",
        options=binary_choice_list,
        index=None,
    )

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
        with open(output_name, "w") as f:
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
            try:
                annotations.append(json.loads(file.readline()))
            except:
                st.write("Failed")
                continue

    btn = st.download_button(
            label="Download all annotations",
            data=json.dumps(annotations, indent=2),
            file_name="annotations.json",
        )