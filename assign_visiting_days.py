#!/usr/bin/python3

# 1.25 (1/29/20) + 1.0 (1/30/20) + 2.5 (2/4/20) + 1.75 2/5/20 + 0.25 2/6/20 + 0.75 meeting with Denise 2/7/20, 0.5 2/8/20

import sys
import random
import copy

if len(sys.argv) != 2:
    print(f"Usage: {sys.argv[0]} <csv file>")
    exit(1)

footer_csv_lines = []

def read_csv_line(file):
    # import pdb; pdb.set_trace()
    values = []
    in_quote = False
    quotation = ""
    while len(values) == 0 or in_quote:
        line = file.readline()
        # if line.startswith("Faculty"):
        #     import pdb; pdb.set_trace()
        if not line:
            break
        quot_parts = line.split('"')
        for i, quot_part in enumerate(quot_parts):
            if i > 0:
                if in_quote:
                    values += [quotation]
                    quotation = ""
                in_quote = not in_quote

            if in_quote:
                quotation += quot_part
            else:
                vals = quot_part.strip().split(',')
                if i > 0:
                    vals = vals[1:]
                if i < len(quot_parts) - 1:
                    vals = vals[:-1]
                values += vals

    return values

class Student:
    def __init__(self, name, choices, times):
        self.name = name
        self.choices = choices
        self.times = times

class Faculty:
    def __init__(self, name, choices, office, allows_groups, times):
        self.name = name
        self.choices = choices
        self.office = office
        self.allows_groups = allows_groups
        self.times = times

csv_file = open(sys.argv[1], "r")
if csv_file is None:
    print(f"Could not open {sys.argv[1]}")
    exit(1)

students = dict()
faculty = dict()

# skip over student choice header
csv_line = read_csv_line(csv_file)
student_header = csv_line
valid_times = [time for time in csv_line[4:] if time]
print(f"All valid meeting times: {valid_times}")
csv_line = read_csv_line(csv_file)
# import pdb; pdb.set_trace()
while True:
    if not csv_line or csv_line[0].startswith("Faculty"):
        break
    student_name = csv_line[0].strip()
    choices = [choice.strip() for choice in csv_line[1].split(',') if choice]
    times = ["NA" if time.upper() == "NA" else time for time in csv_line[4:4+len(valid_times)]]
    students[student_name] = Student(student_name, choices, times)
    # print(f"Got student {student_name} with choices {choices}")

    csv_line = read_csv_line(csv_file)

# use faculty header to figure out all valid times
faculty_header = csv_line
# valid_times = [time for time in csv_line[4:] if time]
# print(f"All valid meeting times: {valid_times}")

csv_line = read_csv_line(csv_file)

while True:
    if not csv_line or not csv_line[0]:
        break
    faculty_name = csv_line[0].strip()
    choices = [choice.strip() for choice in csv_line[1].split(',') if choice]
    office = csv_line[2]
    allows_groups = csv_line[3].upper().startswith("Y")
    times = ["NA" if time.upper() == "NA" else [a for a in time.split(',') if a] for time in csv_line[4:4+len(valid_times)]]
    n_time_slots = sum([1 if time != "NA" else 0 for time in times])
    # if faculty_name.startswith("Jessy Grizzle"):
    faculty[faculty_name] = Faculty(faculty_name, choices, office, allows_groups, times)
    # print(f"Got professor {faculty_name} with choices {choices}, office {office}, allows groups? {allows_groups}, " +
    #       f"and {n_time_slots} available time slots")

    csv_line = read_csv_line(csv_file)

footer_csv_lines += [csv_line]
while True:
    csv_line = read_csv_line(csv_file)
    if not csv_line:
        break
    footer_csv_lines += [csv_line]

# Make sure we are cross consistant between manual faculty and student assignments
for student in students:
    stu = students[student]
    for i in range(len(valid_times)):
        prof = stu.times[i]
        if prof and prof != "NA":
            fac = faculty[prof]
            if student not in fac.times[i]:
                if fac.times[i] == "NA":
                    print(f"***Contradictory manual assignment between {student} and {prof} at {valid_times[i]}")
                fac.times[i] += [student]
for prof in faculty:
    fac = faculty[prof]
    for i in range(len(valid_times)):
        if fac.times[i] == "NA":
            continue
        for student in fac.times[i]:
            stu = students[student]
            if stu.times[i] != prof:
                if stu.times[i] == "NA":
                    print(f"***Contradictory manual assignment between {student} and {prof} at {valid_times[i]}")
                stu.times[i] += prof

# Our basic approach is just a greedy algo!
# First assign mutual preferences, in random order of all mutual preferences
# Then assign professor preferences (in random order)
# Then student preferences (in random order)
# Then for any students with less than four meetings (in random order), attempt to give them a random assignment
# All this subject to the constrains:
# Students have no meetings back-to-back
# Faculty have at most four meetings in a row

def inner_attempt_assign(student, prof, report_assignment=False, max_together=1):
    if prof in students[student].times:
        return True

    prof_times = faculty[prof].times
    i = -1
    n_in_a_row = 0
    while True:
        i += 1
        if i >= len(prof_times):
            # if max_together == 1:
            #     print(f"No easy assignment of {student} to {prof}")
            break

        if prof_times[i] == "NA" or valid_times[i] == "Lunch":
            n_in_a_row = 0
            continue

        # if prof == "Jessy Grizzle" and i == 4:
        #     import pdb; pdb.set_trace()

        if len(prof_times[i]) < max_together:
            total_n_in_a_row = n_in_a_row
            for j in range(i + 1, len(prof_times)):
                if prof_times[j] == "NA" or len(prof_times[j]) == 0:
                    break
                total_n_in_a_row += 1
            if total_n_in_a_row >= 4:
                if prof_times[i] == "NA" or len(prof_times[i]) == 0:
                    n_in_a_row = 0
                continue
            if prof_times[i]:
                n_in_a_row += 1
            if students[student].times[i]:
                # student already has meeting
                continue
            if (i > 0 and students[student].times[i - 1] or
                i + 1 < len(valid_times) and students[student].times[i + 1]):
                # student needs this break
                continue
            if not prof_times[i]:
                prof_times[i] = [student]
                n_in_a_row += 1
            else:
                prof_times[i] += [student]
            students[student].times[i] = prof

            if report_assignment:
                print(f"Assigned {student} to {prof} at {valid_times[i]}")
            return True
        if prof_times[i]:
            n_in_a_row += 1

    if not faculty[prof].allows_groups:
        # print(f"No assignment possible because {prof} does not allow groups")
        return False

    if max_together > 10:
        # print(f"No possible assignment between {student} and {prof} because of necessary breaks")
        return False

    return inner_attempt_assign(student, prof, report_assignment, max_together + 1)

def attempt_assign(student, prof, report_assignment=False, report_failure=False):
    if inner_attempt_assign(student, prof, report_assignment):
        return True

    # print("Starting to look for time swap")
    # Could not make an assignment. Our strategy is try to pilfer a previous
    # student time slot for the new prof, but only if the old one can also be reassigned
    stu = students[student]
    for i in range(len(valid_times)):
        if not stu.times[i] or stu.times[i].upper() == 'NA':
            continue

        old_prof = stu.times[i]

        original_stu_times = copy.deepcopy(stu.times)
        original_old_prof_times = copy.deepcopy(faculty[old_prof].times)
        original_prof_times = copy.deepcopy(faculty[prof].times)

        stu.times[i] = ''
        faculty[old_prof].times[i].remove(student)
        if inner_attempt_assign(student, prof):
            if inner_attempt_assign(student, old_prof):
                # it worked! Keep the combo.
                # print(f"Found time swap for {student} between {old_prof} and {prof} at {valid_times[i]}")
                # if report_assignment:
                print(f"Needed to rearrange {student}'s times to assign them to {prof}")
                return True
            # revert
            faculty[prof].times = original_prof_times
        # revert
        stu.times = original_stu_times
        faculty[old_prof].times = original_old_prof_times

        # import pdb; pdb.set_trace()
        # print("")

    # Try a more radical approach of reassignments, removing _all_ existing assignments
    # and trying again with the hard prof first
    original_stu_times = copy.deepcopy(stu.times)
    original_prof_times = copy.deepcopy(faculty[prof].times)
    original_old_prof_times_set = dict()
    for i in range(len(valid_times)):
        old_prof = original_stu_times[i]
        if old_prof and old_prof != "NA":
            original_old_prof_times_set[old_prof] = copy.deepcopy(faculty[old_prof].times)
            stu.times[i] = ''
            faculty[old_prof].times[i].remove(student)
    reassignment_success = True
    if inner_attempt_assign(student, prof):
        for i in range(len(valid_times)):
            old_prof = original_stu_times[i]
            if not old_prof or old_prof == "NA":
                continue
            if not inner_attempt_assign(student, old_prof):
                reassignment_success = False
                break
    else:
        reassignment_success = False
    if reassignment_success:
        # print(f"Found complete reassignment for {student} to meet with {prof}")
        # if report_assignment:
        print(f"Needed to rearrange {student}'s times to assign them to {prof}")
        return True

    # revert
    stu.times = original_stu_times
    faculty[prof].times = original_prof_times
    for i in range(len(valid_times)):
        old_prof = original_stu_times[i]
        if old_prof and old_prof != "NA":
            faculty[old_prof].times = original_old_prof_times_set[old_prof]

    if report_failure:
        print(f"***Failed to find any time that works to assign {student} to {prof}***")
    return False

def find_mutual_preferences(students, faculty):
    mutual_prefs = []
    for student in students:
        for prof in students[student].choices:
            if student in faculty[prof].choices:
                mutual_prefs += [(student, prof)]
    return mutual_prefs

mutual_prefs = find_mutual_preferences(students, faculty)
print(f"\nMutual prefs:")# {mutual_prefs}")

random.shuffle(mutual_prefs)
for (student, prof) in mutual_prefs:
    attempt_assign(student, prof, report_failure=True)

print("\nFaculty prefs:")
faculty_prefs = []
for prof in faculty:
    for student in faculty[prof].choices:
        faculty_prefs += [(student, prof)]
random.shuffle(faculty_prefs)
for (student, prof) in faculty_prefs:
    attempt_assign(student, prof, report_failure=True)

print("\nStudent prefs:")
student_prefs = []
for student in students:
    for prof in students[student].choices:
        student_prefs += [(student, prof)]
random.shuffle(student_prefs)
for (student, prof) in student_prefs:
    attempt_assign(student, prof, report_failure=True)

def min_assigned_faculty_besides(besides):
    profs = [prof for prof in faculty if prof not in besides]
    if len(profs) == 0:
        return []
    min_count = min([len([time for time in faculty[prof].times if time != "NA" and time]) for prof in profs])
    return [prof for prof in profs if min_count == len([time for time in faculty[prof].times if time != "NA" and time])]

print("\nNow filling students up to four assignments:")
student_names = [student for student in students]
random.shuffle(student_names)
remaining_prefs = []
for student in student_names:
    attempts = 0
    unassignable_profs = []
    while True:
        profs = [time for time in students[student].times if time and time != "NA"]
        count = len(profs)
        # print(f"{student} has {count} assignments so far: {profs}")
        if count >= 4:
            break
        prof_names = min_assigned_faculty_besides(profs + unassignable_profs)
        if len(prof_names) == 0:
            print(f"***No faculty left to assign. Could not fill 4 meetings for {student}***")
            break
        # print(f"Min assigned faculty: {prof_names}")
        random.shuffle(prof_names)
        if not attempt_assign(student, prof_names[0], report_assignment=True):
            unassignable_profs += [prof_names[0]]
        attempts += 1
        if attempts > 10:
           print(f"***Could not fill 4 meetings for {student}***")
           break

out_file = open("assignments.csv", "w")
if out_file is None:
    print("Could not open assignments.csv to write the file")
    exit(1)

def write_csv_vals(file, vals):
    vals = [f'"{v}"' if ',' in v or '\n' in v else v for v in vals]
    file.write(",".join(vals) + "\n")

write_csv_vals(out_file, student_header)

for student in students:
    stu = students[student]
    vals = [student, ",".join(stu.choices), "", ""]
    for assignment in stu.times:
        vals += [assignment]
    write_csv_vals(out_file, vals)

write_csv_vals(out_file, faculty_header)

for prof in faculty:
    fac = faculty[prof]
    vals = [prof, ",".join(fac.choices), fac.office, "Y" if fac.allows_groups else "N"]
    for assignment in fac.times:
        vals += ["NA" if assignment == "NA" else ",".join(assignment)]
    write_csv_vals(out_file, vals)

for line in footer_csv_lines:
    write_csv_vals(out_file, line)
