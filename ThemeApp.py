import streamlit as st
import pandas as pd
from pathlib import Path
from tempfile import NamedTemporaryFile

st.set_page_config(page_title="Thematic Analysis Coder", layout="wide")

# ---------- Helpers ----------

def load_codebook(path: Path):
    code_groups = {}
    current_group = None
    if not path.exists():
        return code_groups
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                current_group = line.replace("#", "").strip()
                code_groups[current_group] = []
            else:
                if current_group is not None:
                    code_groups[current_group].append(line)
    return code_groups


def init_state(df_len):
    if "index" not in st.session_state:
        st.session_state.index = 0
    if "codes" not in st.session_state:
        st.session_state.codes = {i: [] for i in range(df_len)}


def build_output_csv(df):
    coded = []
    for i, row in df.iterrows():
        codes = ";".join(st.session_state.codes.get(i, []))
        coded.append({
            "paragraph": row[0],
            "codes": codes
        })
    out_df = pd.DataFrame(coded)
    return out_df.to_csv(index=False)


# ---------- UI ----------

st.title("Thematic Analysis Coding Tool")

csv_file = st.file_uploader("Upload CSV file (one paragraph per row)", type=["csv"])
codebook_file = st.file_uploader("Upload codebook.txt", type=["txt"])

if csv_file is not None and codebook_file is not None:
    df = pd.read_csv(csv_file, header=None)
    # Use a cross-platform temporary directory

    if "codebook_text" not in st.session_state:
        st.session_state.codebook_text = codebook_file.getvalue().decode("utf-8")

    with NamedTemporaryFile(delete=False, suffix=".txt", mode="w", encoding="utf-8") as tmp:
        tmp.write(st.session_state.codebook_text)
        codebook_path = Path(tmp.name)

    codebook = load_codebook(codebook_path)


    init_state(len(df))

    i = st.session_state.index

    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader(f"Paragraph {i + 1} of {len(df)}")
        st.write(df.iloc[i, 0])

    with col2:
        st.subheader("Codes")
        selected = set(st.session_state.codes.get(i, []))
        for group, codes in codebook.items():
            with st.expander(group, expanded=False):
                for code in codes:
                    checked = code in selected
                    if st.checkbox(code, value=checked, key=f"{i}_{group}_{code}"):
                        selected.add(code)
                    else:
                        selected.discard(code)
        st.session_state.codes[i] = sorted(selected)

    nav_col1, nav_col2, nav_col3 = st.columns([1, 1, 2])

    with nav_col1:
        if st.button("Back") and i > 0:
            st.session_state.index -= 1
            st.rerun()

    with nav_col2:
        if st.button("Next") and i < len(df) - 1:
            st.session_state.index += 1
            st.rerun()

    with nav_col3:
        if st.button("Prepare coded CSV"):
            csv_data = build_output_csv(df)
            st.download_button(
                label="Download coded_output.csv",
                data=csv_data,
                file_name="coded_output.csv",
                mime="text/csv"
            )


else:
    st.info("Upload both a CSV file and a codebook.txt to begin.")
