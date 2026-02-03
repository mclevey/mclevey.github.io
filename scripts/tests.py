# import yaml

# with open("records/tests.yml", "r") as f:
#     supervision_data = yaml.safe_load(f)

# phd_students = supervision_data.get("phd")


# supervisions = {
#     "completed": ["<h3>Completed</h3><br>\n"],
#     "active": ["<h3>Active</h3><br>\n"],
# }

# for student in phd_students:
#     if isinstance(student.get("status"), int):
#         gs_str = "<p>"
#         gs_str += f"{student.get(, '')}<br>\n"
#         gs_str += f"{student.get(, '')}<br>\n"
#         gs_str += f"{student.get(, '')}<br>\n"
#         gs_str += "</p>"

#         supervisions["completed"].append(gs_str)

#     else:
#         gs_str = ""
#         supervisions["active"].append(gs_str)


# # print(supervision_data)

# # import pandas as pd

# # with open("records/teaching.yml", "r") as f:
# #     teaching_data = yaml.safe_load(f)

# # courses = teaching_data.get("courses")
# # df_courses = pd.DataFrame(courses)

# # teaching = teaching_data.get("teaching")
# # df_teaching = pd.DataFrame(teaching)


# # print(df_teaching.head())


# # # LOOKUP DICTS
# # def df_column_lookup(df, key_col, value_col):
# #     """
# #     Returns a dictionary mapping each unique value in df[key_col]
# #     to the corresponding value in df[value_col].
# #     """
# #     return dict(zip(df[key_col], df[value_col]))


# # lookup_course_id_to_number = df_column_lookup(df_courses, "id", "number")
# # lookup_course_id_to_name = df_column_lookup(df_courses, "id", "name")


# # course_strings = []

# # # Group by 'id'
# # for course_id, group in df_teaching.groupby("id"):
# #     # Sort by 'term-code' (treat as string or int where possible)
# #     group_sorted = group.sort_values(
# #         by="term-code", key=lambda col: pd.to_numeric(col, errors="coerce")
# #     )
# #     # Treat NaN enrollment as 0, sum total enrollment
# #     total_enrollment = group_sorted["enrollment"].fillna(0).astype(int).sum()
# #     # Create ordered list of semester-year values as a comma-separated string
# #     semester_years = group_sorted["semester-year"].tolist()
# #     offering_list = ", ".join(semester_years)
# #     # Get course number and name
# #     course_number = lookup_course_id_to_number.get(course_id, course_id)
# #     course_name = lookup_course_id_to_name.get(course_id, "")

# #     # Format string and add to list
# #     section_string = "<p>\n{course_number} | <strong>{course_name}</strong><br>\n"

# #     if total_enrollment > 0:
# #         section_string += f"{total_enrollment} total enrolments from {len(semester_years)} sections:<br>\n{offering_list}\n".replace(
# #             "1 sections:", "1 section:"
# #         )
# #     else:
# #         section_string += f"Scheduled for {offering_list}\n"
# #     section_string += "</p>\n"

# #     course_strings.append(section_string)

# # for s in course_strings:
# #     print(s)
