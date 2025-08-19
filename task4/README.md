# Local Food Wastage Management System (Streamlit + SQLite)

## Quickstart
```bash
python -m venv venv
# Windows: venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

pip install -r requirements.txt

# Build the SQLite DB from the provided CSVs
python init_db.py

# Launch the app
streamlit run app.py
```

## Features
- Overview metrics, filters, and data explorer
- 15+ prebuilt SQL queries from the project brief
- CRUD on Providers, Receivers, Food Listings, Claims
- Simple insights tables

## Notes
- `init_db.py` reads CSVs from absolute paths. Change them if needed.
- The app assumes `food_waste.db` in the current directory.
