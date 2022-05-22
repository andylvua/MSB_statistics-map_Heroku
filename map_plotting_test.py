import json

import numpy as np
import pandas as pd

from pycountry_convert import country_name_to_country_alpha2
from geopy.geocoders import Nominatim
import folium
from folium.plugins import MarkerCluster


def create_map():
    with open("countries.json") as json_file:
        countries_json = json.load(json_file)

    df = pd.DataFrame(countries_json.items(), columns=['Country', 'Quantity'])

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

    df['Code'] = alpha2code(df.Country)
    df = df.join(pd.DataFrame(geolocate(df.Code), columns=['Latitude', 'Longitude']))

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
