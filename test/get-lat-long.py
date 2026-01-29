import googlemaps

gmaps = googlemaps.Client(key='AIzaSyAyXCvdwMlLa_4Om-5wgA-uVtT2uNnW-0k')

geocode_result = gmaps.geocode('Amherst, NY')
# print(type(geocode_result))
# print(geocode_result)
# geocode_result = json.loads(geocode_result)
print(geocode_result[0]['geometry']['location'])