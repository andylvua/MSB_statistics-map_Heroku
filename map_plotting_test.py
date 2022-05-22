import json

import numpy as np
import pandas as pd

from pycountry_convert import country_name_to_country_alpha2
from geopy.geocoders import Nominatim
import folium
from folium.plugins import MarkerCluster

from pymongo import MongoClient
import configparser

from regex_engine import generator

import bs4

config = configparser.ConfigParser()
config.read("config.ini")

cluster = MongoClient(config['Database']['cluster'])
db = cluster.TestBotDatabase
collection = db.TestBotCollection


def get_quantities() -> dict:
    """
    The get_quantities function takes a path to a json file containing country codes and returns
    a dictionary with the quantities of countries that match the regex for each code.

    :return: A dictionary with the country codes as keys and the number of documents that match each code as values
    """
    with open("country_codes.json") as json_file:
        country_codes = json.load(json_file)

    quantities = dict()
    generate = generator()

    for key, value in country_codes.items():
        key_splitted = key.split("–")

        if len(key_splitted) == 2:
            key_pair = (int(key_splitted[0]), int(key_splitted[1]))
            regex = generate.numerical_range(key_pair[0], key_pair[1]).strip("$")
            quantity = collection.count_documents({"code": {'$regex': f'{regex}'}})
        else:
            int_key = int(key)
            quantity = collection.count_documents({"code": {'$regex': f'^{int_key}'}})

        quantities[value] = int(quantity)

    return quantities


def get_not_empty_countries(quantities: dict) -> dict:
    """
    The get_not_empty_countries function takes a dictionary of country names and quantities as input.
    It returns a new dictionary containing only the countries that have at least one quantity greater than zero.

    :param quantities: Store the quantities of each country
    :return: A dictionary of countries that have values greater than 0 in the quantities dictionary
    """
    countries = dict()

    for key, value in quantities.items():
        if value != 0:
            countries[key] = value
        else:
            continue

    return countries


def alpha2code(countries):
    code = []
    for country in countries:
        try:
            cn_a2_code = country_name_to_country_alpha2(country)
            code.append(cn_a2_code)
        except Exception as e:
            print(e)
            cn_a2_code = 'Unknown'
            code.append(cn_a2_code)
    return code


def geolocate(country_codes):
    geolocator = Nominatim(user_agent="email@email.com")
    coordinates = []
    for country_code in country_codes:
        try:
            # Geolocate the center of the country
            loc = geolocator.geocode(country_code)
            # And return latitude and longitude
            coordinates.append((loc.latitude, loc.longitude))
        except:
            # Return missing value
            coordinates.append(np.nan)
    return coordinates


def create_dataframe(countries: dict):
    df = pd.DataFrame(countries.items(), columns=['Country', 'Quantity'])

    df['Code'] = alpha2code(df.Country)
    df = df.join(pd.DataFrame(geolocate(df.Code), columns=['Latitude', 'Longitude']))

    return df


def built_map(df: pd.DataFrame):
    world_map = folium.Map(tiles="cartodbpositron")
    marker_cluster = MarkerCluster().add_to(world_map)

    # for each coordinate, create circlemarker of user percent
    for i in range(len(df)):
        lat = df.iloc[i]['Latitude']
        long = df.iloc[i]['Longitude']
        radius = 5
        popup_text = """<b>Country:</b> {}<br>
                        <b>Medicines:</b> {}<br>"""

        popup_text = popup_text.format(df.iloc[i]['Country'],
                                       df.iloc[i]['Quantity'])

        popup = folium.Popup(popup_text, max_width=300)

        folium.CircleMarker(location=(lat, long), radius=radius, popup=popup, fill=True).add_to(marker_cluster)

    world_map.save('templates/map.html')


def create_map():
    quantities = get_quantities()
    countries = get_not_empty_countries(quantities)

    df = create_dataframe(countries=countries)

    built_map(df=df)
    insert_tags()


def insert_tags():
    with open("templates/map.html") as input:
        txt = input.read()
        soup = bs4.BeautifulSoup(txt, "lxml")

    new_link = soup.new_tag("link", rel="icon", href="/static/MSB_Logo_transparent.png")
    new_title = soup.new_tag("title")
    new_title.string = "MSB Map"
    soup.head.append(new_link)
    soup.head.append(new_title)

    with open("templates/map.html", "w") as output:
        output.write(str(soup))


if __name__ == '__main__':
    create_map()
