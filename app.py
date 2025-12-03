import streamlit as st
from datetime import datetime
from attendance_analyzer import calculate_work_hours, format_time, format_duration, determine_day_status

st.title("📅 Attendance Analyzer - Manual Input")

st.write("Enter your IN/OUT records below:")

# Container for dynamic rows
entries = []

num_rows = st.number_input("How many entries?", min_value=1, max_value=20, value=2)

for i in range(num_rows):
    col1, col2, col3 = st.columns(3)

    with col1:
        date = st.date_input(f"Date #{i+1}")
    with col2:
        time_val = st.time_input(f"Time #{i+1}")
    with col3:
        in_out = st.selectbox(f"Type #{i+1}", ["In", "Out"])

    # Combine date+time into datetime
    dt = datetime.combine(date, time_val)
    entries.append({
        "datetime": dt,
        "type": in_out,
        "date": date.strftime('%d-%b-%y')
    })

if st.button("Analyze Attendance"):
    # Feed directly to your function
    data = calculate_work_hours(entries)

    st.subheader("📘 Summary")
    st.write(f"**First In:** {format_time(data['first_in'])}")
    st.write(f"**Last Out:** {format_time(data['last_out'])}")
    st.write(f"**Total Work:** {format_duration(data['total_minutes'])}")
    st.write(f"**Status:** {determine_day_status(data['total_hours'])}")

    st.subheader("⏱ Work Sessions")
    for session in data['work_sessions']:
        st.write(
            f"- {format_time(session['start'])} → {format_time(session['end'])} "
            f"({format_duration(session['duration_minutes'])})"
        )

    st.subheader("☕ Breaks")
    if data['breaks']:
        for br in data['breaks']:
            st.write(
                f"- {format_time(br['start'])} → {format_time(br['end'])} "
                f"({format_duration(br['duration_minutes'])})"
            )
    else:
        st.write("No breaks detected")

    st.success("Analysis complete!")
