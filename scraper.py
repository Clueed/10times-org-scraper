import requests
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime
import os


def request_and_parse_url(url: str):
    """Downloads webpage content from url and parses it with BeatifulSoup.

    Returns:
        BeautifulSoup: BeautifulSoup object from the parsed webpage
    """

    response = requests.get(url)
    if response.status_code != 200:
        response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    return soup


def get_event_urls(index_url: str):
    """Extracts urls to events from a top-level domain of 10times.com

    Currently only tested on https://10times.com/events.

    Returns:
        list: Unordered list of dicts which only contain event urls
    """

    soup = request_and_parse_url(index_url)

    # Find a html object <a> with a specific data atribute.
    # Specific to 10times html structure
    events = soup.find_all("a", attrs={"data-ga-category": "Event Listing"})

    eventurls = []
    for event in events:
        # A link (href) to the event page on 10times
        eventurls.append({"10t_url": event["href"]})

    return eventurls


def get_org_domain(event_page_soup: BeautifulSoup, org_name: str):
    """Tries to match organizer name with domain/homepage

    Returns:
        string: Domain url

    """

    # First looks for link to domain on 10times page for organizer
    try:
        # Selects link (href) from an object with specific id
        tentimes_org_url = event_page_soup.find(id="org-name")["href"]

        # Gets the organizer page
        tentimes_org_page = request_and_parse_url(tentimes_org_url)

        # Link to domain of organizer is not specific so css selector is used
        tentimes_org_page_link = tentimes_org_page.select_one(
            "body > header > section > div > div > div > div > div:nth-child(1) > a"
        )

        return tentimes_org_page_link["href"]

    except KeyError as e:
        if e.args[0] == "href":
            # No org domain link on organizer page
            pass
        else:
            raise

    # If no success on 10times tries clearbit api next to match organizer name with domain
    try:
        response = requests.request(
            "GET",
            "https://company.clearbit.com/v1/domains/find",
            auth=(os.getenv("CLEARBIT_API_KEY"), ""),
            params={"name": org_name},
        )

        if response.status_code != 200:
            response.raise_for_status()

        return response.json()["domain"]

    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 404:
            # 404 is no domain found but successfull request
            raise

    except Exception:
        raise

    return None


def get_event_info(event_url: str):
    """Extracts all relevant information for event from 10times.com event url

    Returns:
        dict: With organizer name, event title and org_domain (if not found = None)
    """

    soup = request_and_parse_url(event_url)

    # Element with id org-name contains organizer name.
    # Because it contains other elements like <span> .next_element is used to extract only the name
    org_name = soup.find(id="org-name").next_element.text

    # h1 is the title of the domain
    # TODO: make more specific
    title = soup.find("h1").text

    # Get domain of organizer
    org_domain = get_org_domain(soup, org_name)

    return {"org": org_name, "title": title, "org_domain": org_domain}


def save_as_csv(events: list):
    """Saves a list of event to csv

    Independent of list and sub-dict structure.

    TODO:
        - Return success
        - Remove index row (0,1,2,3)
    """

    # Create pandas dataframe from event dict
    # TODO: Why not .from_list?
    df = pd.DataFrame.from_dict(events)

    # Saves to current directory with rounded unix time to prevent overriding
    df.to_csv(f"./sample_events_{int(datetime.now().timestamp())}.csv")


def index_events(index_url: str, sample_size: int, save_csv=False, verbose=False):
    """Assemble func takes index_url and return lisk of events

    Returns:
        list: of dicts where each element is an event with all event data as dict
    """
    event_index = get_event_urls(index_url)

    # All take first x based on sample size
    event_index = event_index[0:sample_size]

    # Loops through events (only 10times urls at this point) and fills data
    for e in event_index:
        # get all event data
        event_info = get_event_info(e["10t_url"])

        # Map event data to event dict
        # TODO: Merge dict instead of match
        e["org"] = event_info["org"]
        e["title"] = event_info["title"]
        e["org_domain"] = event_info["org_domain"]

        if verbose:
            print(e)

    if save_csv:
        save_as_csv(event_index)

    return event_index


events_sample = index_events(
    "https://10times.com/events", sample_size=5, save_csv=True, verbose=True
)
