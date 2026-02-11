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
    if "new_codes" not in st.session_state:
        st.session_state.new_codes = {}


def build_output_csv(df):
    coded = []
    for i in range(len(df)):
        codes = ";".join(st.session_state.codes.get(i, []))
        coded.append({
            "row": i + 1,
            "codes": codes
        })
    out_df = pd.DataFrame(coded)
    return out_df.to_csv(index=False)


# ---------- UI ----------

st.title("ThemeApp - Thematic Analysis Coding Tool V1.5.0")

data_file = st.file_uploader("Upload CSV or Excel file (one paragraph per row)", type=["csv", "xlsx"])
codebook_file = st.file_uploader("Upload codebook.txt", type=["txt"])

if data_file is not None and codebook_file is not None:
    # Read file based on type
    if data_file.name.endswith('.xlsx'):
        df = pd.read_excel(data_file, header=None)
    else:
        df = pd.read_csv(data_file, header=None)
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
        # Display all columns for this row
        for col_idx in range(len(df.columns)):
            st.write(df.iloc[i, col_idx])

    with col2:
        st.subheader("Codes")
        selected = set(st.session_state.codes.get(i, []))
        for group, codes in codebook.items():
            with st.expander(group, expanded=False):
                # Display codebook codes
                for code in codes:
                    checked = code in selected
                    if st.checkbox(code, value=checked, key=f"{i}_{group}_{code}"):
                        selected.add(code)
                    else:
                        selected.discard(code)
                
                # Display newly added codes for this group
                new_codes_key = f"{group}_new"
                if new_codes_key not in st.session_state.new_codes:
                    st.session_state.new_codes[new_codes_key] = []
                
                for new_code in st.session_state.new_codes[new_codes_key]:
                    checked = new_code in selected
                    if st.checkbox(new_code, value=checked, key=f"{i}_{group}_{new_code}_new"):
                        selected.add(new_code)
                    else:
                        selected.discard(new_code)
                
                # Add new code input
                st.divider()
                col_input, col_btn = st.columns([3, 1])
                with col_input:
                    new_code = st.text_input(
                        "Add new code",
                        placeholder="Type code name...",
                        key=f"{i}_{group}_new_code_input"
                    )
                with col_btn:
                    if st.button("Add", key=f"{i}_{group}_add_btn"):
                        if new_code and new_code not in st.session_state.new_codes[new_codes_key]:
                            st.session_state.new_codes[new_codes_key].append(new_code)
                            selected.add(new_code)
                            st.rerun()
        
        st.session_state.codes[i] = sorted(selected)

    nav_col1, nav_col2 = st.columns([1.5, 2])

    with nav_col1:
        goto_row = st.number_input(
            "Go to row",
            min_value=1,
            max_value=len(df),
            value=i + 1,
            step=1,
            key="goto_row_input"
        )
        if goto_row != i + 1:
            st.session_state.index = int(goto_row) - 1
            st.rerun()

    with nav_col2:
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
