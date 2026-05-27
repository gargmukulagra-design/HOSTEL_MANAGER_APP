import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

today_date = datetime.today().strftime("%Y-%m-%d")
today_day = datetime.today().strftime("%A").upper()


conn = sqlite3.connect("Students.DB")
client = conn.cursor()

st.title("Hostel Planner")

col_spacer, col_btn = st.columns([8, 2])

with col_btn:
    if st.button("🗑️ Reset Attendance", use_container_width=True):
        client.execute(
            "DELETE FROM attendance_log WHERE date = ?", 
            (today_date,)
        )
        conn.commit()
        st.success("Attendance reset!")
        st.rerun()


# ── Full timetable ──────────────────────────────────────────────
query = "SELECT * FROM timetable"
timetable = pd.read_sql_query(query, conn)
st.table(timetable)

# ── Today's schedule ────────────────────────────────────────────
today_query = f"SELECT TIME, {today_day} FROM timetable"
today_table = pd.read_sql_query(today_query, conn)

# ── Attendance form (THE KEY FIX) ───────────────────────────────
with st.form("attendance_form"):
    attendance_log = []

    for index, row in today_table.iterrows():
        col1, col2, col3 = st.columns([1, 3, 1])

        with col1:
            st.write(row["TIME"])
        with col2:
            st.write(row[today_day])
        with col3:
            checked = st.checkbox("", key=f"chk_{index}")

    # Single submit button for the whole form
    submitted = st.form_submit_button("Save Attendance")

# ── Only insert ONCE when the button is clicked ─────────────────
if submitted:
    # Check if attendance for today is already saved
    existing = pd.read_sql_query(
        "SELECT COUNT(*) as cnt FROM attendance_log WHERE date = ?",
        conn, params=(today_date,)
    )

    if existing["cnt"][0] > 0:
        st.warning("Attendance for today is already saved!")
    else:
        for index, row in today_table.iterrows():
            checked = st.session_state.get(f"chk_{index}", False)
            attendance_log.append((today_date, row[today_day], checked))

        client.executemany(
            "INSERT INTO attendance_log VALUES (?, ?, ?)",
            attendance_log
        )
        conn.commit()
        st.success(f"Attendance saved for {today_date}!")

#attendence tracker
if st.button("SHOW ATTENDENCE"):
        attendence_track_query = """
                        SELECT SUBJECT, COUNT(1) AS total_attendence , SUM(PRESENT) AS attended , SUM(PRESENT)/COUNT(1)*100 AS PERCENTAGE
                        FROM attendance_log
                        GROUP BY SUBJECT
                        """
        Track_table = pd.read_sql_query(attendence_track_query,conn)
        st.table(Track_table)
        


conn.close()