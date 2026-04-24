import requests

def test_openalex():
    url = "https://api.openalex.org/works"
    params = {
        "search": "machine learning",
        "filter": "has_fulltext:true,is_oa:true",
        "per_page": 5
    }
    print(f"Testing OpenAlex: {url}")
    try:
        response = requests.get(url, params=params, timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            results = response.json().get("results", [])
            print(f"Found {len(results)} results.")
        else:
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_openalex()
