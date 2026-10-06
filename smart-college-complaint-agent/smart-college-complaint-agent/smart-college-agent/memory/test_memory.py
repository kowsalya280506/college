from data_manager import update_complaint


print("Updating complaint...")


result = update_complaint(
    "CMP001",
    {
        "status": "In Progress"
    }
)


print("Updated complaint:")

print(result)