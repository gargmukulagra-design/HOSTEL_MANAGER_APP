import streamlit as st
import pandas as pd
import sqlite3
from datetime import datetime

# ── PAGE CONFIG ─────────────────────────────────────

st.set_page_config(
    page_title="Hostel Planner",
    page_icon="📚",
    layout="wide"
)

# ── DATE INFO ───────────────────────────────────────

today_date = datetime.today().strftime("%Y-%m-%d")
today_day = datetime.today().strftime("%A").upper()

# ── DATABASE ────────────────────────────────────────

conn = sqlite3.connect("Students.DB")
client = conn.cursor()

# ── HEADER ──────────────────────────────────────────

st.title("📚 Hostel Planner")
st.caption(f"Today : {today_day} | {today_date}")

# ── SIDEBAR ─────────────────────────────────────────

st.sidebar.title("Navigation")

show_schedule = st.sidebar.checkbox("Show Full Timetable", True)
show_tracker = st.sidebar.checkbox("Show Attendance Analytics", True)

# ── RESET BUTTON ────────────────────────────────────

col1, col2 = st.columns([8,2])

with col2:

    if st.button(
        "🗑️ Reset Today",
        use_container_width=True
    ):

        client.execute(
            """
            DELETE FROM attendance_log
            WHERE DATE = ?
            """,
            (today_date,)
        )

        conn.commit()

        st.success("Today's attendance reset!")

        st.rerun()

# ── FULL TIMETABLE ──────────────────────────────────

if show_schedule:

    st.subheader("📅 Weekly Timetable")

    timetable = pd.read_sql_query(
        "SELECT * FROM timetable",
        conn
    )

    st.dataframe(
        timetable,
        use_container_width=True,
        hide_index=True
    )

# ── TODAY'S CLASSES ─────────────────────────────────

st.subheader(f"✅ Today's Classes ({today_day})")

today_query = f"""
SELECT TIME, {today_day}
FROM timetable
"""

today_table = pd.read_sql_query(
    today_query,
    conn
)

# ── FORM ────────────────────────────────────────────

with st.form("attendance_form"):

    for index, row in today_table.iterrows():

        container = st.container(border=True)

        col1, col2, col3 = container.columns([1,4,1])

        with col1:
            st.markdown(
                f"### {row['TIME']}"
            )

        with col2:
            st.markdown(
                f"### {row[today_day]}"
            )

        with col3:

            st.checkbox(
                "Present",
                key=f"chk_{index}"
            )

    submitted = st.form_submit_button(
        "💾 Save Attendance",
        use_container_width=True
    )

# ── SAVE ATTENDANCE ─────────────────────────────────

if submitted:

    existing = pd.read_sql_query(
        """
        SELECT COUNT(*) as cnt
        FROM attendance_log
        WHERE DATE = ?
        """,
        conn,
        params=(today_date,)
    )

    if existing["cnt"][0] > 0:

        st.warning(
            "Attendance already saved for today!"
        )

    else:

        attendance_log = []

        for index, row in today_table.iterrows():

            checked = st.session_state.get(
                f"chk_{index}",
                False
            )

            attendance_log.append(
                (
                    today_date,
                    row[today_day],
                    checked
                )
            )

        client.executemany(
            """
            INSERT INTO attendance_log
            VALUES (?, ?, ?)
            """,
            attendance_log
        )

        conn.commit()

        st.success(
            "Attendance Saved Successfully!"
        )

        st.balloons()

# ── ANALYTICS ───────────────────────────────────────

if show_tracker:

    st.subheader("📊 Attendance Analytics")

    attendance_track_query = """

    SELECT

        SUBJECT,

        COUNT(1) AS TOTAL,

        SUM(PRESENT) AS ATTENDED,

        ROUND(
            SUM(PRESENT) * 100.0 /
            COUNT(1),
            2
        ) AS PERCENTAGE

    FROM attendance_log

    GROUP BY SUBJECT

    """

    Track_table = pd.read_sql_query(
        attendance_track_query,
        conn
    )

    st.dataframe(
        Track_table,
        use_container_width=True,
        hide_index=True
    )
    for index, row in Track_table.iterrows():

        st.write(row["SUBJECT"])

        st.progress(
            row["PERCENTAGE"] / 100
        )

        st.write(
            f"{row['PERCENTAGE']}%"
        )

    # ── METRICS ─────────────────────────────────────

    st.subheader("📈 Quick Stats")

    total_classes = Track_table["TOTAL"].sum()
    attended = Track_table["ATTENDED"].sum()

    overall = round(
        attended * 100 / total_classes,
        2
    )

    c1, c2, c3 = st.columns(3)

    c1.metric(
        "Total Classes",
        total_classes
    )

    c2.metric(
        "Attended",
        attended
    )

    c3.metric(
        "Overall %",
        f"{overall}%"
    )

# ── CLOSE CONNECTION ────────────────────────────────

conn.close()