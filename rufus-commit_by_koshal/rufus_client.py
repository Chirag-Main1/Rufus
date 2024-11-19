import requests

class RufusClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "http://localhost:8000"

    def scrape(self, url, instructions, depth=1, keywords=None):
        headers = {'Authorization': f'Bearer {self.api_key}'}
        payload = {'url': url, 'instructions': instructions, 'depth': depth, 'keywords': keywords}
        response = requests.post(f"{self.base_url}/scrape", json=payload, headers=headers)
        return response.json()
