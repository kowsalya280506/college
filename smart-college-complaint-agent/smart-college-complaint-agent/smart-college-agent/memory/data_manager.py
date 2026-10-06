import json
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.abspath(__file__)
    )
)

DATA_DIR = os.path.join(BASE_DIR, "data")


def load_data(filename):

    file_path = os.path.join(DATA_DIR, filename)

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    return data


def get_complaints():

    return load_data("complaints.json")


def get_departments():

    return load_data("departments.json")


def get_staff():

    return load_data("staff.json")


def get_history():

    return load_data("complaint_history.json")


def save_data(filename, data):

    file_path = os.path.join(DATA_DIR, filename)

    with open(file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, indent=4)


def update_complaint(complaint_id, updates):

    complaints = get_complaints()

    for complaint in complaints:

        if complaint["id"] == complaint_id:

            complaint.update(updates)

            save_data(
                "complaints.json",
                complaints
            )

            return complaint

    return None