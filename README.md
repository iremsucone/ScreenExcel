# 📸 ScreenExcel

**ScreenExcel** is a free local tool that turns table screenshots into editable Excel/CSV files.

It is designed for students, researchers, and engineers who often need to extract tables from papers, reports, slides, or screenshots and turn them into usable data.

The app runs locally on your computer. No API key, no cloud upload, no paid service.

---

## ✨ Features

- Upload a table screenshot (`PNG`, `JPG`, `JPEG`)
- Extract table data using OCR
- Edit extracted values directly inside the app
- Delete extra columns created by OCR
- Merge wrongly split columns
- Rename columns before saving
- Save cleaned tables into a local repository
- Re-open saved tables
- Edit saved values and column names later
- Export one table as Excel or CSV
- Export the full repository as:
  - one multi-sheet Excel file
  - one combined CSV file

---

---

## 🚀 Quick start

### 1. Clone the repository

```bash
git clone https://github.com/YOUR-USERNAME/screenexcel.git
cd screenexcel
```

### 2. Create a virtual environment

```bash
python -m venv venv
```

Activate it:

**macOS / Linux**

```bash
source venv/bin/activate
```

**Windows**

```bash
venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Tesseract OCR

ScreenExcel uses Tesseract OCR. It must be installed separately.

**macOS**

```bash
brew install tesseract
```

**Ubuntu / Linux**

```bash
sudo apt-get install tesseract-ocr
```

**Windows**

Download and install Tesseract from:

https://github.com/UB-Mannheim/tesseract/wiki

After installation, make sure Tesseract is added to your system PATH.

---

## ▶️ Run the app

```bash
streamlit run app.py
```

Then open the local Streamlit link shown in your terminal.

---

## 🧪 How to use

1. Upload a screenshot of a table.
2. Review the extracted table.
3. Delete unnecessary columns if OCR created too many.
4. Merge columns if OCR split one column into several parts.
5. Rename columns if needed.
6. Edit values directly inside the table.
7. Save the cleaned table to the repository.
8. Export one table or the full repository.

---

## 🗂️ Local repository

When you save tables, ScreenExcel automatically creates this folder:

```bash
table_repository/
```

Each saved table contains:

- a `.csv` file with the table data
- a `.json` file with metadata such as table name, source image, save date, and update date

This folder is ignored by Git by default because it contains your personal extracted data.

---

## 📦 Export options

ScreenExcel can export:

- the current extracted table as Excel
- the current extracted table as CSV
- one saved repository table as Excel
- one saved repository table as CSV
- all saved tables as one Excel file with multiple sheets
- all saved tables as one combined CSV file

---

## 🔐 Privacy

ScreenExcel runs locally.

Your screenshots and tables are not uploaded anywhere.

---

## ⚠️ Limitations

OCR quality depends on the screenshot.

Best results come from:

- clear screenshots
- high contrast
- good resolution
- tightly cropped tables
- non-rotated images

Very blurry screenshots, merged cells, complex table layouts, or small text may require manual correction.

---

## 🧭 Roadmap ideas

Possible future improvements:

- Graph generation from extracted tables
- Search inside saved tables
- Batch upload of multiple screenshots
- PDF page extraction
- Automatic unit detection
- Scientific column detection such as `LOI (%)`, `UL-94`, `wt%`, `Tg`, `Tm`
- Merge and compare tables from multiple papers

---

## 🛠️ Tech stack

- Python
- Streamlit
- Tesseract OCR
- OpenCV
- Pandas
- OpenPyXL
- Pillow

---

## 📄 License

MIT License.
# ScreenExcel
