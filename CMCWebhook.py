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


def getEventsDateByDate(days=2):
    eventsJSON = {}

    total = []

    today = datetime.today().strftime("%d/%m/%Y")
    next = (datetime.today() + timedelta(days - 1)).strftime("%d/%m/%Y")

    page = 1
    temp = getEvents(tokenJSON["access_token"], page=page,
                     max=150,
                     dateRangeStart=today,
                     dateRangeEnd=next)
    while isinstance(temp, list):
        total += temp
        page += 1
        temp = getEvents(tokenJSON["access_token"], page=page,
                         max=150,
                         dateRangeStart=today,
                         dateRangeEnd=next)

    for event in total:
        date = event["date_event"].split("T")[0]
        if not date in eventsJSON:
            eventsJSON[date] = []
        eventsJSON[date].append(event)

    return eventsJSON


def sendEventsDateByDate(days=2):
    events = getEventsDateByDate(days)
    for date in events:
        post = wh.Webhook(WEBHOOK_URL, title="Date: {}".format(date),
                          footer_icon="https://pbs.twimg.com/profile_images/984423152116781056/Z9MUJT_7_400x400.jpg",
                          footer="https://coinmarketcal.com/")
        eventCount = 0
        for event in events[date]:
            coins = ""
            for coin in event["coins"]:
                coins += "${} ".format(coin["symbol"])

            desc = event["description"] if event["description"] is not None else ""
            if desc is "":
                value = "[___Proof___]({})\t\t[___Source___]({})".format(event["proof"], event["source"])
            else:
                value = "{}\n[___Proof___]({})\t\t[___Source___]({})".format(desc, event["proof"], event["source"])

            post.add_field(name="\nEvent: **{}** for {}".format(event["title"], coins), value=value, inline=False)
            eventCount += 1
            if eventCount == 25:
                eventCount = 0
                post.post()
                post = wh.Webhook(WEBHOOK_URL,
                                  footer_icon="https://pbs.twimg.com/profile_images/984423152116781056/Z9MUJT_7_400x400.jpg",
                                  footer="https://coinmarketcal.com/")

        post.post()


def sendShortEventsDateByDate(days=7):
    events = getEventsDateByDate(days)
    dates = list(events.keys())
    post = wh.Webhook(WEBHOOK_URL, title="Events of -> {} - {}".format(dates[0], dates[-1]),
                      footer_icon="https://pbs.twimg.com/profile_images/984423152116781056/Z9MUJT_7_400x400.jpg",
                      footer="https://coinmarketcal.com/")
    for date in dates:
        output = ""
        count = 1
        b = False
        for event in events[date]:
            coins = ""
            for coin in event["coins"]:
                coins += "${} ".format(coin["symbol"])
            output += "{}. *{}* **{}**\n".format(count, event["title"], coins)
            count += 1
            if len(output) > 950:
                post.add_field(name="Date: {}".format(date), value=output, inline=False)
                output = ""
                b = True

        print(len(output))
        post.add_field(name="Date: {}".format(date) if not b else "...", value=output, inline=False)

    post.post()


getToken()
sendEventsDateByDate()

sc.every(30).days.do(getToken)  # Her 30 günde bir yeni token alacak
sc.every().day.do(sendEventsDateByDate)  # Her gün (iki günlük) etkinlikleri postlayacak
sc.every().monday.do(sendShortEventsDateByDate)  # Her pazartesi (haftalık) etkinlikleri postlayacak

while True:
    sc.run_pending()
