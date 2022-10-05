from django.conf import settings
import requests
from geopy import distance

from foodcartapp.models import Order


def fetch_coordinates(apikey, address):
    base_url = 'https://geocode-maps.yandex.ru/1.x'
    response = requests.get(base_url, params={
        'geocode': address,
        'apikey': apikey,
        'format': 'json',
    })
    response.raise_for_status()
    found_places = response.json()['response']['GeoObjectCollection']['featureMember']

    if not found_places:
        return None

    most_relevant = found_places[0]
    lon, lat = most_relevant['GeoObject']['Point']['pos'].split(' ')
    return lon, lat


def evaluate_distance(source_address: str, destination_address: str):
    api_key = settings.YANDEX_GEOCODER_API_KEY

    source_coordinate = fetch_coordinates(api_key, source_address)
    destination_coordinate = fetch_coordinates(api_key, destination_address)

    distance_between = distance.distance(source_coordinate, destination_coordinate).km

    return distance_between


def get_distances(order: Order, restaurants, sort=False):
    restaurants_with_distance = [
        (restaurant, evaluate_distance(restaurant.address, order.address))
        for restaurant in restaurants
    ]

    if sort:
        restaurants_with_distance.sort(key=lambda _: _[1])

    return restaurants_with_distance
