import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os


def request_and_parse_url(url: str):
    response = requests.get(url)
    if response.status_code != 200:
        response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup


def get_event_urls(index_url: str):
    soup = request_and_parse_url(index_url)
    events = soup.find_all("a", attrs={"data-ga-category": "Event Listing"})

    eventurls = []
    for event in events:
        eventurls.append({"10t_url": event["href"]})

    return eventurls


def get_org_domain(event_page_soup: BeautifulSoup, org_name: str, verbose=False):

    try:
        tentimes_org_url = event_page_soup.find(id="org-name")["href"]
        tentimes_org_page = request_and_parse_url(tentimes_org_url)

        tentimes_org_page_link = tentimes_org_page.select_one(
            "body > header > section > div > div > div > div > div:nth-child(1) > a"
        )

        return tentimes_org_page_link["href"]

    except KeyError:

        if verbose:
            print("url not found on 10times")

        pass

    try:
        response = requests.request(
            "GET",
            "https://company.clearbit.com/v1/domains/find",
            auth=(os.getenv("CLEARBIT_API_KEY"), ""),
            params={"name": org_name},
        )

        return response.json()["domain"]

    except KeyError:
        if verbose:
            print("url not found on clearbit")

    return None


def get_event_info(event_url: str, verbose=False):
    soup = request_and_parse_url(event_url)

    # Possible other info available: date, location, category & type, frequency, estimated turnout

    org = soup.find(id="org-name").next_element.text
    title = soup.find("h1").text

    org_domain = get_org_domain(soup, title, verbose=verbose)

    return {"org": org, "title": title, "org_domain": org_domain}


def save_as_csv(events: dict):
    df = pd.DataFrame.from_dict(events)
    df.to_csv(f"./sample_events_{int(datetime.now().timestamp())}.csv")


def index_events(index_url: str, sample_size: int, save_csv=False, verbose=False):
    event_index = get_event_urls(index_url)

    event_index = event_index[0:sample_size]

    for e in event_index:
        event_info = get_event_info(e["10t_url"], verbose=verbose)

        e["org"] = event_info["org"]
        e["title"] = event_info["title"]
        e["org_domain"] = event_info["org_domain"]

        if verbose:
            print(e)

    if save_csv:
        save_as_csv(event_index)

    return event_index


events_sample = index_events(
    "https://10times.com/events", sample_size=100, save_csv=True, verbose=True
)
