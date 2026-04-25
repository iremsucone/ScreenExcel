# 📸 ScreenExcel

**ScreenExcel** is a free local tool that turns screenshots of tables into editable Excel/CSV files.

You upload a screenshot, the app reads the table, then you can correct mistakes, rename columns, edit values, save tables, and export them.

It runs on your own computer.

No API key.  
No paid service.  
No data upload.

<img width="1440" height="754" alt="Image" src="https://github.com/user-attachments/assets/a426321b-0c7f-44f9-8a40-21f634f16c7a" />

---

## What you need first

Before running ScreenExcel, you need:

1. Python
2. Tesseract OCR
3. The Python packages listed in `requirements.txt`

---

## 1. Install Python

Download Python here:

https://www.python.org/downloads/

If you are on Windows, during installation, select:

```text
Add Python to PATH
```

To check if Python is installed, open Terminal or Command Prompt and run:

```bash
python --version
```

or:

```bash
python3 --version
```

---

## 2. Download this project

You have two options.

### Option A — Easy way

Click the green **Code** button on GitHub, then click:

```text
Download ZIP
```

Unzip the folder.

Open the folder in Terminal or Command Prompt.

---

### Option B — Git way

If you already use Git, run:

```bash
git clone https://github.com/YOUR-USERNAME/screenexcel.git
cd screenexcel
```

Replace `YOUR-USERNAME` with your own GitHub username.

---

## 3. Install Tesseract OCR

ScreenExcel uses Tesseract OCR to read text from images.

The Python package alone is not enough.  
You must install the Tesseract program too.

### macOS

If you use Homebrew:

```bash
brew install tesseract
```

### Ubuntu / Linux

```bash
sudo apt-get install tesseract-ocr
```

### Windows

Download Tesseract here:

https://github.com/UB-Mannheim/tesseract/wiki

After installation, restart Terminal or Command Prompt.

---

## 4. Install the Python packages

Inside the ScreenExcel folder, run:

```bash
pip install -r requirements.txt
```

If `pip` does not work, try:

```bash
python -m pip install -r requirements.txt
```

or:

```bash
python3 -m pip install -r requirements.txt
```

---

## 5. Run ScreenExcel

Inside the project folder, run:

```bash
streamlit run app.py
```

A browser page should open automatically.

If it does not open, copy the local URL from the terminal and paste it into your browser.

It usually looks like this:

```text
http://localhost:8501
```
<img width="1439" height="733" alt="Image" src="https://github.com/user-attachments/assets/64509550-7067-4495-95ea-61d5b3d26bec" />

<img width="1464" height="839" alt="Image" src="https://github.com/user-attachments/assets/c947e082-2cdd-4baf-aaa6-2bdcf1b96097" />


---

## How to use ScreenExcel

### 1. Upload a screenshot

Go to the **Extract table** tab.

Upload a `.png`, `.jpg`, or `.jpeg` image of a table.

---

### 2. Check the extracted table

The screenshot appears on the left.

The extracted table appears on the right.

OCR is not always perfect, so check the result before saving.

---

### 3. Fix columns if needed

You can fix the extracted table before saving it.

#### Delete columns

Use this if the app creates extra wrong columns.

#### Merge columns

Use this if one real column was split into two or more columns.

Example:

```text
No | rating
```

can become:

```text
No rating
```

#### Split columns

Use this if many values were placed into one column.

Example:

```text
PS1 100 0 0 18.5 NR
```

can become:

```text
Sample | PS | EG | AP | LOI | UL-94
```

You can split by:

- space
- comma
- semicolon
- slash
- custom separator

---

## Rename and edit

You can rename columns before saving.

You can also edit values directly in the table.

---

## Save tables

Click:

```text
Save table to repository
```

ScreenExcel will create a local folder called:

```text
table_repository/
```

This folder stores your saved tables on your computer.

Each saved table has:

- a `.csv` file
- a `.json` metadata file

---

## Repository tab

In the **Table repository** tab, you can:

- open saved tables
- rename saved tables
- rename saved columns
- split saved columns
- edit saved values
- save changes
- delete saved tables

---

## Export options

You can export:

### One table

- Excel
- CSV

### Full repository

- one Excel file with multiple sheets
- one combined CSV file

---

## Delete a saved table

In the repository tab, go to:

```text
Danger zone
```

Type:

```text
DELETE
```

Then click the delete button.

This prevents accidental deletion.

---

## requirements.txt

Your `requirements.txt` file should contain:

```text
streamlit
pandas
numpy
pillow
pytesseract
opencv-python
openpyxl
```

---

## Common problems

### “No table detected”

Try:

- cropping closer to the table
- using a clearer screenshot
- zooming in before taking the screenshot
- using a higher-resolution image

### “Tesseract not found”

Tesseract OCR is probably not installed correctly.

Install Tesseract again and restart your terminal.

### The table has wrong columns

Use:

- delete columns
- merge columns
- split columns
- manual editing

OCR helps, but it is not perfect.

---

## Privacy

ScreenExcel runs locally.

Your screenshots and extracted tables stay on your computer.

Nothing is uploaded online.

---

## License

MIT License.
