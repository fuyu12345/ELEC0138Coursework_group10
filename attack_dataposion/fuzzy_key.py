import requests
from bs4 import BeautifulSoup
import itertools

url = "http://127.0.0.1:5000/add_sales_record"

# All possible candidate fields to test
field_candidates = [
    "brand", "specific_pasta", "date", "sales", "promotion",
    "product", "product_id", "quantity", "value", "day",
    "username", "password", "name", "item", "amount"
]

#  Get the default response messages as a baseline
print("Step 1: Getting baseline response messages")
baseline = requests.post(url, data={})
soup = BeautifulSoup(baseline.text, 'html.parser')
default_msgs = set([a.get_text(strip=True) for a in soup.find_all("div", class_="alert")])
print("Collected default messages:", default_msgs)

#  Try field combinations from size 3 to 6
print("\nStep 2: Trying field combinations...\n")

found_sets = []

for size in range(3, 7):
    for combo in itertools.combinations(field_candidates, size):
        payload = {k: "test" for k in combo}
        res = requests.post(url, data=payload)
        soup = BeautifulSoup(res.text, 'html.parser')
        messages = [a.get_text(strip=True) for a in soup.find_all("div", class_="alert")]
        diff_msgs = [m for m in messages if m not in default_msgs]

        if diff_msgs:
            print(f"Valid combination {combo} triggered different response:")
            for m in diff_msgs:
                print("   Message:", m)
            found_sets.append((combo, diff_msgs))

# Print all valid field combinations discovered
print("\nAll valid field combinations that triggered new messages:")
for fs in found_sets:
    print("Field combination:", fs[0])
    print("   Returned messages:", fs[1])



