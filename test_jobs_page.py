import requests

try:
    response = requests.get('http://127.0.0.1:5000/jobs')
    print(f"Status Code: {response.status_code}")
    if response.status_code == 500:
        print("Error 500 - Internal Server Error")
        print(response.text[:500])
    else:
        print("Page loaded successfully!")
except Exception as e:
    print(f"Error: {e}")
