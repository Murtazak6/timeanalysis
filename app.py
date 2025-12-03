import streamlit as st
import csv
import io
from attendance_analyzer import calculate_work_hours, format_time, format_duration, determine_day_status, parse_time

st.title("📅 Attendance Analyzer — Paste Input Version")

st.write("Paste your attendance rows below (including header):")

raw_text = st.text_area("Paste data here:", height=300)

def parse_from_text(raw):
    """Parse tab-separated attendance data from raw text input."""
    entries = []

    if not raw.strip():
        return []

    # Convert to file-like object
    text_stream = io.StringIO(raw)
    reader = csv.DictReader(text_stream, delimiter="\t")

    for row in reader:
        date = row.get('Date', '').strip()
        entry_time = row.get('Entry Time', '').strip()
        in_out = row.get('In/Out', '').strip()

        if date and entry_time and in_out:
            dt = parse_time(date, entry_time)
            if dt:
                entries.append({
                    'datetime': dt,
                    'type': in_out,
                    'date': date
                })

    return entries


if st.button("Analyze"):
    entries = parse_from_text(raw_text)

    if not entries:
        st.error("No valid IN/OUT entries found. Check your data format.")
    else:
        data = calculate_work_hours(entries)

        st.subheader("📘 Summary")
        st.write(f"**First In:** {format_time(data['first_in'])}")
        st.write(f"**Last Out:** {format_time(data['last_out'])}")
        st.write(f"**Total Work:** {format_duration(data['total_minutes'])}")
        st.write(f"**Status:** {determine_day_status(data['total_hours'])}")

        st.subheader("⏱ Work Sessions")
        for s in data["work_sessions"]:
            st.write(
                f"- {format_time(s['start'])} → {format_time(s['end'])} "
                f"({format_duration(s['duration_minutes'])})"
                + (" **(Ongoing)**" if s.get("ongoing") else "")
            )

        st.subheader("☕ Breaks")
        if data["breaks"]:
            for b in data["breaks"]:
                st.write(
                    f"- {format_time(b['start'])} → {format_time(b['end'])} "
                    f"({format_duration(b['duration_minutes'])})"
                )
        else:
            st.write("No breaks detected")

        st.success("Analysis completed!")