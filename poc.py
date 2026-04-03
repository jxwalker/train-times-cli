import requests
import re
import json

url = "https://ojp.nationalrail.co.uk/service/timesandfares/VIC/BTN/today/1800/dep"
resp = requests.get(url)
matches = re.findall(r'"jsonJourneyBreakdown":(\{.*?\})', resp.text)
for m in matches:
    try:
        data = json.loads(m)
        print(f"{data['departureTime']} ({data['departureStationCRS']}) -> {data['arrivalTime']} ({data['arrivalStationCRS']}) Status: {data['statusMessage']}")
    except Exception as e:
        pass
