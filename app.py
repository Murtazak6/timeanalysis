import streamlit as st
import csv
import io
from datetime import timedelta
from attendance_analyzer import (
    calculate_work_hours,
    parse_time,
    format_time,
    format_duration,
    determine_day_status
)

st.title("📅 Attendance Analyzer — Paste Your Logs")

st.write("Paste your attendance data (tab-separated including header):")

raw_text = st.text_area("Paste attendance rows here:", height=300)


def parse_from_text(raw):
    """Parse the pasted attendance log text."""
    entries = []

    if not raw.strip():
        return []

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


if st.button("Analyze Attendance"):
    entries = parse_from_text(raw_text)

    if not entries:
        st.error("No valid entries found. Please check formatting.")
    else:
        data = calculate_work_hours(entries)

        st.header("📘 Summary")

        st.write(f"**First In:** {format_time(data['first_in'])}")
        st.write(f"**Last Out:** {format_time(data['last_out'])}")

        st.write(f"**Total Work:** {format_duration(data['total_minutes'])}")
        st.write(f"**Day Status:** {determine_day_status(data['total_hours'])}")

        # ---- Remaining time + estimated end ----
        remaining_hours = 8 - data["total_hours"]

        if remaining_hours > 0:
            remaining_minutes = remaining_hours * 60
            st.write(f"**Remaining for Full Day:** {format_duration(remaining_minutes)}")

            if data["is_currently_working"] and data["current_time"]:
                estimated = data["current_time"] + timedelta(minutes=remaining_minutes)
                st.write(f"**Estimated Full Day Ends At:** {estimated.strftime('%I:%M %p')}")
        else:
            st.success("🎉 Full Day Completed!")

        # ---- Half Day Calculation ----
        remaining_half_hours = 4.5 - data["total_hours"]

        if remaining_half_hours > 0:
            remaining_half_minutes = remaining_half_hours * 60
            st.write(f"**Remaining for Half Day:** {format_duration(remaining_half_minutes)}")

            if data["is_currently_working"] and data["current_time"]:
                estimated_half = data["current_time"] + timedelta(minutes=remaining_half_minutes)
                st.write(f"**Estimated Half Day Ends At:** {estimated_half.strftime('%I:%M %p')}")
        else:
            st.success("Half Day Completed!")

        # ------------- Work Sessions ----------------
        st.header("⏱ Work Sessions")
        if data["work_sessions"]:
            for s in data["work_sessions"]:
                ongoing = " (Ongoing)" if s.get("ongoing") else ""
                st.write(
                    f"- {format_time(s['start'])} → {format_time(s['end'])} "
                    f"({format_duration(s['duration_minutes'])}){ongoing}"
                )
        else:
            st.write("No completed work sessions found.")

        # ------------- Breaks ----------------
        st.header("☕ Breaks")
        if data["breaks"]:
            for b in data["breaks"]:
                st.write(
                    f"- {format_time(b['start'])} → {format_time(b['end'])} "
                    f"({format_duration(b['duration_minutes'])})"
                )

            total_break_minutes = sum(b["duration_minutes"] for b in data["breaks"])
            st.info(f"**Total Break Time:** {format_duration(total_break_minutes)}")
        else:
            st.write("No breaks recorded.")
        st.markdown("---")