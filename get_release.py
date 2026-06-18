import requests
r = requests.get("https://api.github.com/repos/espeak-ng/espeak-ng/releases/latest")
data = r.json()
print(f"Tag: {data.get('tag_name')}")
for a in data.get("assets", []):
    print(f"  {a['name']}: {a['browser_download_url']}")
