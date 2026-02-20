import requests

def search_vns(title):
    url = "https://api.vndb.org/kana/vn"
    payload = {
        "filters": ["search", "=", title],
        "fields": "id, title, alttitle, released, languages, platforms, image.url, length, description, rating",
        "results" : 50
    }
    r = requests.post(url = url, json = payload)
    data = r.json()
    return data["results"]



#test
'''
search_test = input("What would you like to search ?")
s_results = search_vns(search_test)
for vn in s_results:
    print(vn["title"], vn["id"], vn["image"])
'''
