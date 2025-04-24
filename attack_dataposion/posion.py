import requests

url = "http://127.0.0.1:5000/add_sales_record"

print(" Starting Data Poisoning Attack: Adding fake records after 2018...\n")

for i in range(10):
    payload = {
        "brand": "B1",
        "specific_pasta": "13",
        "date": f"2019-01-{i+1:02d}",
        "sales": str(99999 + i * 50),
        "promotion": "1"
    }

    response = requests.post(url, data=payload)
   

    if "success" in response.text.lower() or response.status_code == 200:
        print(f"[+] Injected record {i+1}: 2019-01-{i+1:02d}, sales={payload['sales']}")
    else:
        print(f"[!] Record {i+1} failed to inject.")

print("\n Poisoning Attempt Completed.")




print(" Starting Out-of-Range Injection Attack...\n")

out_of_range_payloads = [
    {
        "brand": "B10",  # non-existent brand
        "specific_pasta": "3",
        "date": "2019-01-01",
        "sales": "500",
        "promotion": "0"
    },
    {
        "brand": "B1<script>",  # XSS attempt
        "specific_pasta": "10",
        "date": "2019-01-02",
        "sales": "600",
        "promotion": "1"
    },
    {
        "brand": "B3",
        "specific_pasta": "9999",  # non-existent pasta ID
        "date": "2019-01-03",
        "sales": "700",
        "promotion": "1"
    },
    {
        "brand": "B3",
        "specific_pasta": "5",
        "date": "2050-12-31",  # illogical future date
        "sales": "800",
        "promotion": "0"
    },
    {
        "brand": "B3",  # empty brand
        "specific_pasta": "-1",  # invalid negative ID
        "date": "abcd-ef-gh",  # invalid date format
        "sales": "NaN",  # non-numeric sales
        "promotion": "maybe"  # non-binary promo flag
    }
]

for i, payload in enumerate(out_of_range_payloads, 1):
    response = requests.post(url, data=payload)

    if "success" in response.text.lower() or response.status_code == 200:
        print(f"[!] Injected malformed record {i}: Payload = {payload}")
    else:
        print(f"[✓] Rejected (or error triggered) for record {i}: Payload = {payload}")

print("\n Out-of-Range Injection Attempt Completed.")
