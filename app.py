import streamlit as st
from PIL import Image
import pytesseract
import pandas as pd
import numpy as np
import io
import cv2
import os
import json
from datetime import datetime

st.set_page_config(page_title="ScreenExcel", layout="wide")

REPO_DIR = "table_repository"
os.makedirs(REPO_DIR, exist_ok=True)

st.title("📸 ScreenExcel")
st.caption("Extract, edit, save and export tables from screenshots into Excel/CSV.")


def clean_filename(name):
    name = os.path.splitext(name)[0]
    name = name.replace(" ", "_")
    name = "".join(c for c in name if c.isalnum() or c in ["_", "-"])
    return name[:80]


def clean_sheet_name(name):
    name = clean_filename(name)
    if not name:
        name = "Table"
    return name[:31]


def clean_image(image):
    img = np.array(image.convert("RGB"))
    gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)
    gray = cv2.resize(gray, None, fx=3, fy=3, interpolation=cv2.INTER_CUBIC)
    gray = cv2.GaussianBlur(gray, (3, 3), 0)

    thresh = cv2.threshold(
        gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
    )[1]

    return thresh


def ocr_words(img):
    data = pytesseract.image_to_data(
        img,
        config="--oem 3 --psm 6",
        output_type=pytesseract.Output.DATAFRAME,
    )

    data = data.dropna()
    data = data[data["conf"] > 25]
    data["text"] = data["text"].astype(str).str.strip()
    data = data[data["text"] != ""]
    return data


def group_rows(data):
    data = data.sort_values(["top", "left"]).copy()

    rows = []
    current = []
    last_y = None
    threshold = 28

    for _, row in data.iterrows():
        y = row["top"]

        if last_y is None or abs(y - last_y) <= threshold:
            current.append(row)
        else:
            rows.append(current)
            current = [row]

        last_y = y

    if current:
        rows.append(current)

    return rows


def detect_columns(rows):
    xs = []

    for row in rows:
        for word in row:
            xs.append(int(word["left"]))

    xs = sorted(xs)

    if not xs:
        return []

    clusters = [[xs[0]]]

    for x in xs[1:]:
        if x - clusters[-1][-1] < 90:
            clusters[-1].append(x)
        else:
            clusters.append([x])

    centers = [int(np.mean(c)) for c in clusters]
    return centers


def nearest_column(x, centers):
    return min(range(len(centers)), key=lambda i: abs(x - centers[i]))


def build_table(rows, centers):
    table = []

    for row in rows:
        cells = {i: [] for i in range(len(centers))}
        row = sorted(row, key=lambda r: r["left"])

        for word in row:
            col = nearest_column(int(word["left"]), centers)
            cells[col].append(str(word["text"]))

        line = [" ".join(cells[i]).strip() for i in range(len(centers))]

        if any(line):
            table.append(line)

    return table


def fix_common_ocr_errors(df):
    df = df.copy()

    for col in df.columns:
        df[col] = df[col].astype(str)
        df[col] = df[col].str.replace(" ,", ".", regex=False)
        df[col] = df[col].str.replace(",", ".", regex=False)
        df[col] = df[col].str.replace("N o", "No", regex=False)
        df[col] = df[col].str.strip()

    return df


def extract_table(image):
    cleaned = clean_image(image)
    data = ocr_words(cleaned)

    if data.empty:
        return pd.DataFrame()

    rows = group_rows(data)
    centers = detect_columns(rows)

    if len(centers) < 2:
        return pd.DataFrame()

    table = build_table(rows, centers)

    if len(table) < 2:
        return pd.DataFrame()

    max_cols = max(len(r) for r in table)

    normalized = []
    for r in table:
        r = r + [""] * (max_cols - len(r))
        normalized.append(r)

    header = normalized[0]

    header = [
        h if h.strip() else f"Column_{i + 1}"
        for i, h in enumerate(header)
    ]

    df = pd.DataFrame(normalized[1:], columns=header)
    df = df.loc[:, (df != "").any(axis=0)]
    df = fix_common_ocr_errors(df)

    return df


def merge_columns(df, cols_to_merge, new_col_name):
    df = df.copy()

    if len(cols_to_merge) < 2:
        return df

    first_position = df.columns.get_loc(cols_to_merge[0])

    df[new_col_name] = (
        df[cols_to_merge]
        .astype(str)
        .replace("nan", "")
        .agg(" ".join, axis=1)
        .str.replace("  ", " ", regex=False)
        .str.strip()
    )

    df = df.drop(columns=cols_to_merge)

    cols = list(df.columns)
    cols.remove(new_col_name)
    cols.insert(first_position, new_col_name)

    return df[cols]


def split_column(df, column_to_split, separator, new_column_names):
    df = df.copy()

    if column_to_split not in df.columns:
        return df

    first_position = df.columns.get_loc(column_to_split)

    if separator == "Space":
        sep = r"\s+"
        split_data = df[column_to_split].astype(str).str.split(sep, expand=True, regex=True)
    elif separator == "Comma":
        split_data = df[column_to_split].astype(str).str.split(",", expand=True)
    elif separator == "Semicolon":
        split_data = df[column_to_split].astype(str).str.split(";", expand=True)
    elif separator == "Slash":
        split_data = df[column_to_split].astype(str).str.split("/", expand=True)
    else:
        split_data = df[column_to_split].astype(str).str.split(separator, expand=True)

    split_data = split_data.fillna("")

    if new_column_names.strip():
        names = [x.strip() for x in new_column_names.split(",") if x.strip()]
    else:
        names = []

    if len(names) != split_data.shape[1]:
        names = [f"{column_to_split}_{i + 1}" for i in range(split_data.shape[1])]

    split_data.columns = names

    df = df.drop(columns=[column_to_split])

    left_cols = list(df.columns[:first_position])
    right_cols = list(df.columns[first_position:])

    df_left = df[left_cols]
    df_right = df[right_cols]

    result = pd.concat([df_left, split_data, df_right], axis=1)

    return result


def delete_columns(df, cols_to_delete):
    df = df.copy()

    if cols_to_delete:
        df = df.drop(columns=cols_to_delete)

    return df


def rename_columns(df, new_column_names):
    df = df.copy()
    df.columns = new_column_names
    return df


def save_table(df, table_name, source_file):
    safe_name = clean_filename(table_name)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    csv_path = os.path.join(REPO_DIR, f"{safe_name}_{timestamp}.csv")
    meta_path = os.path.join(REPO_DIR, f"{safe_name}_{timestamp}.json")

    df.to_csv(csv_path, index=False)

    metadata = {
        "table_name": table_name,
        "source_file": source_file,
        "saved_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "rows": len(df),
        "columns": len(df.columns),
        "csv_file": os.path.basename(csv_path),
        "meta_file": os.path.basename(meta_path),
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)

    return csv_path


def update_saved_table(df, metadata, new_table_name):
    csv_path = os.path.join(REPO_DIR, metadata["csv_file"])
    df.to_csv(csv_path, index=False)

    metadata["table_name"] = new_table_name
    metadata["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    metadata["rows"] = len(df)
    metadata["columns"] = len(df.columns)

    meta_file = metadata.get("meta_file")

    if meta_file:
        meta_path = os.path.join(REPO_DIR, meta_file)
    else:
        csv_base = os.path.splitext(metadata["csv_file"])[0]
        meta_path = os.path.join(REPO_DIR, f"{csv_base}.json")

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4, ensure_ascii=False)


def delete_saved_table(metadata):
    csv_path = os.path.join(REPO_DIR, metadata["csv_file"])

    if os.path.exists(csv_path):
        os.remove(csv_path)

    meta_file = metadata.get("meta_file")

    if meta_file:
        meta_path = os.path.join(REPO_DIR, meta_file)
    else:
        csv_base = os.path.splitext(metadata["csv_file"])[0]
        meta_path = os.path.join(REPO_DIR, f"{csv_base}.json")

    if os.path.exists(meta_path):
        os.remove(meta_path)


def load_repository():
    tables = []

    for file in os.listdir(REPO_DIR):
        if file.endswith(".json"):
            meta_path = os.path.join(REPO_DIR, file)

            with open(meta_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)

            metadata["meta_file"] = file
            csv_path = os.path.join(REPO_DIR, metadata["csv_file"])

            if os.path.exists(csv_path):
                tables.append(metadata)

    tables = sorted(
        tables,
        key=lambda x: x.get("updated_at", x.get("saved_at", "")),
        reverse=True,
    )

    return tables


def export_all_tables_excel(saved_tables):
    buffer = io.BytesIO()
    used_sheet_names = set()

    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for i, table in enumerate(saved_tables, start=1):
            csv_path = os.path.join(REPO_DIR, table["csv_file"])
            df = pd.read_csv(csv_path)

            base_name = clean_sheet_name(table["table_name"])
            sheet_name = f"{i}_{base_name}"[:31]

            counter = 1
            original_sheet_name = sheet_name

            while sheet_name in used_sheet_names:
                suffix = f"_{counter}"
                sheet_name = original_sheet_name[: 31 - len(suffix)] + suffix
                counter += 1

            used_sheet_names.add(sheet_name)
            df.to_excel(writer, index=False, sheet_name=sheet_name)

    return buffer.getvalue()


def export_all_tables_csv(saved_tables):
    buffer = io.StringIO()

    for table in saved_tables:
        csv_path = os.path.join(REPO_DIR, table["csv_file"])
        df = pd.read_csv(csv_path)

        buffer.write(f"### {table['table_name']} ###\n")
        buffer.write(f"Source screenshot: {table['source_file']}\n")
        buffer.write(f"Saved at: {table['saved_at']}\n")
        buffer.write(f"Updated at: {table.get('updated_at', table['saved_at'])}\n")
        df.to_csv(buffer, index=False)
        buffer.write("\n\n")

    return buffer.getvalue().encode("utf-8")


def make_excel_download(df, sheet_name="Table"):
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name=clean_sheet_name(sheet_name))
    return buffer.getvalue()


tab1, tab2 = st.tabs(["📤 Extract table", "📚 Table repository"])


with tab1:
    uploaded = st.file_uploader("Upload table screenshot", type=["png", "jpg", "jpeg"])

    if uploaded:
        image = Image.open(uploaded)
        default_table_name = clean_filename(uploaded.name)

        left, right = st.columns(2)

        with left:
            st.subheader("Original screenshot")
            st.image(image, use_container_width=True)

        with right:
            st.subheader("Extracted table")

            extracted_df = extract_table(image)

            if extracted_df.empty:
                st.error("No table detected. Try cropping closer to the table.")
            else:
                if (
                    "df" not in st.session_state
                    or st.session_state.get("last_file") != uploaded.name
                ):
                    st.session_state["df"] = extracted_df
                    st.session_state["last_file"] = uploaded.name

                df = st.session_state["df"]

                table_name = st.text_input("Table name", value=default_table_name)

                st.success(f"Detected {len(df)} rows × {len(df.columns)} columns")

                st.markdown("### Fix columns before saving")

                cols_to_delete = st.multiselect(
                    "Delete extra columns:",
                    options=list(df.columns),
                    key="delete_cols_extract",
                )

                if st.button("Delete selected columns", key="delete_extract"):
                    st.session_state["df"] = delete_columns(df, cols_to_delete)
                    st.rerun()

                cols_to_merge = st.multiselect(
                    "Merge columns that were split wrongly:",
                    options=list(df.columns),
                    key="merge_cols_extract",
                )

                new_col_name = st.text_input(
                    "Name for merged column:",
                    value="Merged_column",
                    key="merge_name_extract",
                )

                if st.button("Merge selected columns", key="merge_extract"):
                    if len(cols_to_merge) >= 2:
                        st.session_state["df"] = merge_columns(
                            df, cols_to_merge, new_col_name
                        )
                        st.rerun()
                    else:
                        st.warning("Select at least 2 columns to merge.")

                st.markdown("### Split a column")

                column_to_split = st.selectbox(
                    "Choose column to split:",
                    options=list(st.session_state["df"].columns),
                    key="split_col_extract",
                )

                separator_choice = st.selectbox(
                    "Choose separator:",
                    options=["Space", "Comma", "Semicolon", "Slash", "Custom"],
                    key="split_sep_extract",
                )

                custom_separator = ""

                if separator_choice == "Custom":
                    custom_separator = st.text_input(
                        "Custom separator:",
                        value="-",
                        key="custom_sep_extract",
                    )

                split_names = st.text_input(
                    "New column names, separated by commas (optional):",
                    placeholder="Sample, PS, EG, AP, LOI",
                    key="split_names_extract",
                )

                if st.button("Split selected column", key="split_extract"):
                    sep = custom_separator if separator_choice == "Custom" else separator_choice

                    if sep:
                        st.session_state["df"] = split_column(
                            st.session_state["df"],
                            column_to_split,
                            sep,
                            split_names,
                        )
                        st.rerun()
                    else:
                        st.warning("Choose or enter a separator.")

                st.markdown("### Rename columns before saving")

                current_cols = list(st.session_state["df"].columns)
                renamed_cols = []

                for i, col in enumerate(current_cols):
                    renamed_cols.append(
                        st.text_input(
                            f"Column {i + 1}",
                            value=col,
                            key=f"extract_rename_col_{i}",
                        )
                    )

                if st.button("Apply column names", key="apply_extract_columns"):
                    if len(set(renamed_cols)) != len(renamed_cols):
                        st.warning("Column names must be unique.")
                    else:
                        st.session_state["df"] = rename_columns(
                            st.session_state["df"], renamed_cols
                        )
                        st.rerun()

                if st.button("Reset extraction", key="reset_extract"):
                    st.session_state["df"] = extracted_df
                    st.rerun()

                st.markdown("### Edit values before saving")

                edited_df = st.data_editor(
                    st.session_state["df"],
                    use_container_width=True,
                    num_rows="dynamic",
                    key="extract_editor",
                )

                st.session_state["df"] = edited_df

                st.markdown("### Save or export")

                col_a, col_b, col_c = st.columns(3)

                with col_a:
                    if st.button("💾 Save table to repository"):
                        save_table(edited_df, table_name, uploaded.name)
                        st.success("Table saved to repository.")

                with col_b:
                    st.download_button(
                        "📥 Download Excel",
                        make_excel_download(edited_df, table_name),
                        file_name=f"{clean_filename(table_name)}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )

                with col_c:
                    csv = edited_df.to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "📥 Download CSV",
                        csv,
                        file_name=f"{clean_filename(table_name)}.csv",
                        mime="text/csv",
                    )


with tab2:
    st.subheader("📚 Saved table repository")

    saved_tables = load_repository()

    if not saved_tables:
        st.info("No saved tables yet.")
    else:
        table_labels = [
            f"{t['table_name']} | {t['rows']} rows × {t['columns']} columns | updated {t.get('updated_at', t['saved_at'])}"
            for t in saved_tables
        ]

        selected = st.selectbox("Choose a saved table", table_labels)

        selected_index = table_labels.index(selected)
        metadata = saved_tables[selected_index]

        csv_path = os.path.join(REPO_DIR, metadata["csv_file"])
        repo_df = pd.read_csv(csv_path)

        st.markdown(f"### {metadata['table_name']}")
        st.write(f"**Source screenshot:** {metadata['source_file']}")
        st.write(f"**Saved at:** {metadata['saved_at']}")
        st.write(f"**Last updated:** {metadata.get('updated_at', metadata['saved_at'])}")

        st.markdown("### Edit saved table")

        new_table_name = st.text_input(
            "Repository table name",
            value=metadata["table_name"],
            key="repo_table_name",
        )

        st.markdown("#### Split a saved column")

        repo_split_column = st.selectbox(
            "Choose saved column to split:",
            options=list(repo_df.columns),
            key=f"repo_split_col_{selected_index}",
        )

        repo_separator_choice = st.selectbox(
            "Choose separator:",
            options=["Space", "Comma", "Semicolon", "Slash", "Custom"],
            key=f"repo_split_sep_{selected_index}",
        )

        repo_custom_separator = ""

        if repo_separator_choice == "Custom":
            repo_custom_separator = st.text_input(
                "Custom separator:",
                value="-",
                key=f"repo_custom_sep_{selected_index}",
            )

        repo_split_names = st.text_input(
            "New column names, separated by commas (optional):",
            placeholder="Sample, PS, EG, AP, LOI",
            key=f"repo_split_names_{selected_index}",
        )

        if st.button("Split saved column", key=f"repo_split_button_{selected_index}"):
            sep = repo_custom_separator if repo_separator_choice == "Custom" else repo_separator_choice

            if sep:
                repo_df = split_column(
                    repo_df,
                    repo_split_column,
                    sep,
                    repo_split_names,
                )
                st.session_state[f"repo_split_df_{selected_index}"] = repo_df
            else:
                st.warning("Choose or enter a separator.")

        if f"repo_split_df_{selected_index}" in st.session_state:
            repo_df = st.session_state[f"repo_split_df_{selected_index}"]

        st.markdown("#### Rename saved columns")

        repo_current_cols = list(repo_df.columns)
        repo_renamed_cols = []

        for i, col in enumerate(repo_current_cols):
            repo_renamed_cols.append(
                st.text_input(
                    f"Saved column {i + 1}",
                    value=col,
                    key=f"repo_rename_col_{selected_index}_{i}",
                )
            )

        if len(set(repo_renamed_cols)) != len(repo_renamed_cols):
            st.warning("Column names must be unique before saving changes.")
            safe_to_save_columns = False
        else:
            safe_to_save_columns = True

        if safe_to_save_columns:
            repo_df.columns = repo_renamed_cols

        st.markdown("#### Edit saved values")

        edited_repo_df = st.data_editor(
            repo_df,
            use_container_width=True,
            num_rows="dynamic",
            key=f"repo_editor_{selected_index}",
        )

        col_save, col_info = st.columns([1, 2])

        with col_save:
            if st.button("💾 Save repository changes"):
                if safe_to_save_columns:
                    update_saved_table(edited_repo_df, metadata, new_table_name)

                    split_key = f"repo_split_df_{selected_index}"
                    if split_key in st.session_state:
                        del st.session_state[split_key]

                    st.success("Repository table updated.")
                    st.rerun()
                else:
                    st.error("Fix duplicate column names first.")

        with col_info:
            st.info("You can rename columns, split columns, edit values, add rows, then save the changes.")

        st.markdown("---")
        st.markdown("### Export options")

        export_col1, export_col2 = st.columns(2)

        with export_col1:
            st.markdown("#### This table")

            st.download_button(
                "📥 Download THIS table as Excel",
                make_excel_download(edited_repo_df, new_table_name),
                file_name=f"{clean_filename(new_table_name)}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            csv = edited_repo_df.to_csv(index=False).encode("utf-8")

            st.download_button(
                "📥 Download THIS table as CSV",
                csv,
                file_name=f"{clean_filename(new_table_name)}.csv",
                mime="text/csv",
            )

        with export_col2:
            st.markdown("#### Full repository")

            st.download_button(
                "📦 Download ALL tables as one Excel file",
                export_all_tables_excel(saved_tables),
                file_name="all_saved_tables.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

            st.download_button(
                "📦 Download ALL tables as one CSV file",
                export_all_tables_csv(saved_tables),
                file_name="all_saved_tables.csv",
                mime="text/csv",
            )

        st.markdown("---")
        st.markdown("### Danger zone")

        st.warning("Deleting a saved table removes it permanently from the local repository.")

        confirm_delete_text = st.text_input(
            "Type DELETE to confirm deletion",
            key=f"delete_confirm_{selected_index}",
        )

        if st.button("🗑️ Delete this saved table", key=f"delete_table_{selected_index}"):
            if confirm_delete_text == "DELETE":
                delete_saved_table(metadata)
                st.success("Saved table deleted.")
                st.rerun()
            else:
                st.error("Type DELETE exactly to confirm.")