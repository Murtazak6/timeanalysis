#!/usr/bin/env python3
"""
Attendance Analyzer Script
Analyzes attendance log data to calculate work hours, breaks, and day status.
"""

import csv
from datetime import datetime, time, timedelta, timezone
from collections import defaultdict
import argparse


def get_current_ist_time():
    """Get current time in IST (Indian Standard Time - UTC+5:30)."""
    ist_offset = timezone(timedelta(hours=5, minutes=30))
    utc_now = datetime.now(timezone.utc)
    ist_now = utc_now.astimezone(ist_offset)
    return ist_now.replace(tzinfo=None)


def parse_time(date_str, time_str):
    """Parse date and time strings into a datetime object."""
    try:
        datetime_str = f"{date_str} {time_str}"
        return datetime.strptime(datetime_str, "%d-%b-%y %I:%M %p")
    except ValueError as e:
        print(f"Error parsing time '{date_str} {time_str}': {e}")
        return None


def parse_attendance_file(filename):
    """Parse the attendance text file and return structured data."""
    entries = []

    try:
        with open(filename, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter='\t')

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

    except FileNotFoundError:
        print(f"Error: File '{filename}' not found.")
        return []
    except Exception as e:
        print(f"Error reading file: {e}")
        return []

    return entries


def remove_duplicates(entries):
    """Remove duplicate entries while preserving order."""
    seen = set()
    unique_entries = []

    for entry in entries:
        key = (entry['datetime'], entry['type'])
        if key not in seen:
            seen.add(key)
            unique_entries.append(entry)

    return unique_entries


def calculate_work_hours(entries, use_current_time=True):
    """Calculate total work hours and breaks from attendance entries."""
    if not entries:
        return {
            'total_hours': 0,
            'total_minutes': 0,
            'breaks': [],
            'first_in': None,
            'last_out': None,
            'work_sessions': [],
            'is_currently_working': False,
            'current_time': None
        }

    entries = sorted(entries, key=lambda x: x['datetime'])
    entries = remove_duplicates(entries)

    work_sessions = []
    breaks = []
    current_in = None
    last_out = None
    first_in = None

    for entry in entries:
        if entry['type'] == 'In':
            if current_in is None:
                current_in = entry['datetime']
                if first_in is None:
                    first_in = current_in

                if last_out is not None:
                    break_duration = (current_in -
                                      last_out).total_seconds() / 60
                    breaks.append({
                        'start': last_out,
                        'end': current_in,
                        'duration_minutes': break_duration
                    })

        elif entry['type'] == 'Out':
            if current_in is not None:
                work_duration = (entry['datetime'] -
                                 current_in).total_seconds() / 60
                work_sessions.append({
                    'start': current_in,
                    'end': entry['datetime'],
                    'duration_minutes': work_duration,
                    'ongoing': False
                })
                last_out = entry['datetime']
                current_in = None
            else:
                last_out = entry['datetime']

    is_currently_working = False
    current_time = None

    if current_in is not None and use_current_time:
        current_time = get_current_ist_time()
        if current_time.date() == current_in.date() and current_time > current_in:
            work_duration = (current_time - current_in).total_seconds() / 60
            work_sessions.append({
                'start': current_in,
                'end': current_time,
                'duration_minutes': work_duration,
                'ongoing': True
            })
            is_currently_working = True

    total_minutes = sum(session['duration_minutes']
                        for session in work_sessions)
    total_hours = total_minutes / 60

    return {
        'total_hours': total_hours,
        'total_minutes': total_minutes,
        'breaks': breaks,
        'first_in': first_in,
        'last_out': last_out,
        'work_sessions': work_sessions,
        'is_currently_working': is_currently_working,
        'current_time': current_time
    }


def determine_day_status(total_hours):
    """Determine if it's a full day, half day, or incomplete based on hours worked."""
    if total_hours >= 8:
        return "Full Day"
    elif total_hours >= 4:
        return "Half Day"
    else:
        return "Incomplete Day"


def format_time(dt):
    """Format datetime object to readable string."""
    if dt:
        return dt.strftime("%I:%M %p")
    return "N/A"


def format_duration(minutes):
    """Format duration in minutes to hours and minutes."""
    hours = int(minutes // 60)
    mins = int(minutes % 60)
    if hours > 0:
        return f"{hours}h {mins}m"
    return f"{mins}m"


def display_report(data):
    """Display a formatted attendance report."""
    print("\n" + "=" * 60)
    print("           ATTENDANCE ANALYSIS REPORT")
    print("=" * 60)

    if data['first_in']:
        print(f"\nDate: {data['first_in'].strftime('%d-%b-%Y')}")

    if data['is_currently_working'] and data['current_time']:
        print(f"Current Time: {format_time(data['current_time'])}")
        print(f"Status: Currently Working ⏱️")

    print(f"\nFirst In Time:  {format_time(data['first_in'])}")
    print(f"Last Out Time:  {format_time(data['last_out'])}")

    print(f"\n{'─'*60}")
    print("WORK SESSIONS:")
    print(f"{'─'*60}")

    if data['work_sessions']:
        for i, session in enumerate(data['work_sessions'], 1):
            is_ongoing = session.get('ongoing', False)
            status_marker = " (Ongoing)" if is_ongoing else ""
            print(
                f"  Session {i}: {format_time(session['start'])} - {format_time(session['end'])} "
                f"({format_duration(session['duration_minutes'])}){status_marker}"
            )
    else:
        print("  No complete work sessions found")

    print(f"\n{'─'*60}")
    print("BREAK DETAILS:")
    print(f"{'─'*60}")

    if data['breaks']:
        for i, brk in enumerate(data['breaks'], 1):
            print(
                f"  Break {i}: {format_time(brk['start'])} - {format_time(brk['end'])} "
                f"({format_duration(brk['duration_minutes'])})")
        total_break_time = sum(brk['duration_minutes']
                               for brk in data['breaks'])
        print(f"\n  Total Break Time: {format_duration(total_break_time)}")
    else:
        print("  No breaks detected")

    print(f"\n{'─'*60}")
    print("SUMMARY:")
    print(f"{'─'*60}")

    hours = int(data['total_minutes'] // 60)
    minutes = int(data['total_minutes'] % 60)

    if data['is_currently_working']:
        print(
            f"  Total Work Hours (So Far): {hours}h {minutes}m ({data['total_hours']:.2f} hours)"
        )
    else:
        print(
            f"  Total Work Hours: {hours}h {minutes}m ({data['total_hours']:.2f} hours)"
        )

    day_status = determine_day_status(data['total_hours'])
    print(f"  Day Status: {day_status}")

    if data['total_hours'] < 8:
        remaining = 8 - data['total_hours']
        print(f"  Remaining for Full Day: {format_duration(remaining * 60)}")

        if data['is_currently_working'] and data['current_time']:
            estimated_completion = data['current_time'] + timedelta(
                minutes=remaining * 60)
            print(
                f"  Estimated Full Day Completion: {format_time(estimated_completion)}"
            )

    print("\n" + "=" * 60 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description=
        'Analyze attendance data and calculate work hours, breaks, and day status.'
    )
    parser.add_argument(
        'filename',
        nargs='?',
        default='attendance.txt',
        help='Path to attendance text file (default: attendance.txt)')

    args = parser.parse_args()

    print(f"Reading attendance data from: {args.filename}")

    entries = parse_attendance_file(args.filename)

    if not entries:
        print("No valid attendance entries found.")
        return

    data = calculate_work_hours(entries)
    display_report(data)


if __name__ == "__main__":
    main()
