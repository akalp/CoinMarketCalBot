import Webhook as wh
import schedule as sc
import time
from datetime import datetime, timedelta
import requests as r
import json

CMC_ID = "712_zx0dpmsv6pcockk44gwckccwwkk4sws0wwkwgswgo48w4k480"
CMC_SECRET = "5ali6ds8vh8gk804c04o8wgkgkscw0c8w0gk84kogw40csc4gw"
WEBHOOK_URL = "https://discordapp.com/api/webhooks/450070522873774082/HeDjfKR9bOE9bocK8IaPwQ5SrIkePJXyNt10yhJdMREZyx8npWU63OBmUr1QDrCqvl8-"

tokenJSON = {}
eventsJSON = {}


def getToken():
    global tokenJSON

    payload = {'grant_type': 'client_credentials', 'client_id': CMC_ID, 'client_secret': CMC_SECRET}
    url = "https://api.coinmarketcal.com/oauth/v2/token"
    try:
        events = r.post(url, data=payload)
        tokenJSON = json.loads(events.text)
    except json.decoder.JSONDecodeError:
        print("JSONDecodeError")
        tokenJSON = []


def getEvents(token, page=None, max=None, dateRangeStart=None, dateRangeEnd=None,
              coins=None, categories=None, sortBy=None, showOnly=None):
    payload = {
            "page": page,
            "max": max,
            "dateRangeStart": dateRangeStart,
            "dateRangeEnd": dateRangeEnd,
            "coins": coins,
            "categories": categories,
            "sortBy": sortBy,
            "showOnly": showOnly,
            'access_token': token,
             }

    url = "https://api.coinmarketcal.com/v1/events"
    try:
        events = r.get(url, params=payload)
        result = json.loads(events.text)
    except json.decoder.JSONDecodeError:
        print("JSONDecodeError")
        result = []
    return result


def getEvents(day=2):
    global eventsJSON

    total = []

    today = datetime.today().strftime("%d/%m/%Y")
    tomorrow = (datetime.today() + timedelta(day-1)).strftime("%d/%m/%Y")

    page = 1
    temp = getEvents(tokenJSON["access_token"], page=page,
                         max=150,
                         dateRangeStart=today,
                         dateRangeEnd=tomorrow)
    while isinstance(temp, list):
        total += temp
        page += 1
        temp = getEvents(tokenJSON["access_token"], page=page,
                             max=150,
                             dateRangeStart=today,
                             dateRangeEnd=tomorrow)

    for event in total:
        date = event["date_event"].split("T")[0]
        if not date in eventsJSON:
            eventsJSON[date] = []
        eventsJSON[date].append(event)


def sendEventsDateByDate():
    getEvents()
    for date in eventsJSON:

        post = wh.Webhook(WEBHOOK_URL, title="Date: {}".format(date),
                          footer_icon="https://pbs.twimg.com/profile_images/984423152116781056/Z9MUJT_7_400x400.jpg",
                          footer="https://coinmarketcal.com/")

        for event in eventsJSON[date]:

            coins = ""
            for coin in event["coins"]:
                coins += "${} ".format(coin["symbol"])

            desc = event["description"] if event["description"] is not None else ""
            if desc is "":
                value = "[___Proof___]({})\t\t[___Source___]({})".format(event["proof"], event["source"])
            else:
                value = "{}\n[___Proof___]({})\t\t[___Source___]({})".format(desc, event["proof"], event["source"])

            post.add_field(name="\nEvent: **{}** for {}".format(event["title"], coins), value=value, inline=False)

        post.post()


getToken()
sendEventsDateByDate()

# sc.every(30).days.do(getToken) #Her 30 günde bir yeni token alacak
# sc.every().day.do(sendEventsDateByDate) #Her gün etkinlikleri postlayacak
#
# while True:
#     sc.run_pending()
#     time.sleep(1)
