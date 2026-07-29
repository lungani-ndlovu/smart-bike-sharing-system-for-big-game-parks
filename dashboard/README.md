## Analytics Dashboard

A Python/Streamlit dashboard that displays real-time fleet data from 
the Firebase Realtime Database. Shows ride statistics, user activity, 
emergency alerts, and financial insights for park administrators.

## Running the Dashboard

1. Export your Firebase Realtime Database as JSON from the Firebase Console
2. Create a folder named `data` inside this directory
3. Place the exported file inside it and rename it to:
   `safari-cycleq-default-rtdb-export.json`
4. Install dependencies:

## pip install -r requirements.txt
5. Run the dashboard:

## streamlit run dashboard.py
6. Open your browser at `http://localhost:8501`
