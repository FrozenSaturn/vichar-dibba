import requests

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
}

def fetch_and_save(url, filename):
    try:
        response = requests.get(url, headers=headers)
        with open(filename, 'w') as f:
            f.write(response.text)
        print(f"Saved {url} to {filename}")
    except Exception as e:
        print(f"Error fetching {url}: {e}")

fetch_and_save("https://www.ycombinator.com/companies", "yc_debug.html")
fetch_and_save("https://www.failory.com/cemetery", "failory_debug.html")
fetch_and_save("http://autopsy.io", "autopsy_debug.html")
