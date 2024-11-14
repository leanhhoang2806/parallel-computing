import requests

# Replace with the actual URL of your FastAPI endpoint
url = "http://localhost:8000/add_task/"

# Sample task data to send
task_data = {"task_id": 1, "description": "Sample task"}

# Send the POST request
try:
    response = requests.post(url, json=task_data, verify=False)  # Set verify=False if self-signed SSL
    if response.status_code == 200:
        print("Task added successfully:", response.json())
    else:
        print("Failed to add task:", response.status_code, response.text)
except requests.RequestException as e:
    print("Request failed:", e)
