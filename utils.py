import requests
import json

def get_city_temp(city, limit, API_KEY):
    city_link = f'http://api.openweathermap.org/geo/1.0/direct?q={city}&limit={limit}&appid={API_KEY}'
    city_request = requests.get(city_link)
    city_result = json.loads(city_request.content)
    city_lat, city_lon = city_result[0]['lat'], city_result[0]['lon']

    temp_link = f'https://api.openweathermap.org/data/2.5/weather?lat={city_lat}&lon={city_lon}&appid={API_KEY}&units=metric'
    temp_request = requests.get(temp_link)
    temp_result = json.loads(temp_request.content)
    city_temp = temp_result['main']['temp']

    return city_temp

def get_food_calory(food):
    url = f"https://world.openfoodfacts.org/cgi/search.pl?action=process&search_terms={food}&json=true"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        products = data.get('products', [])
        if products:  # Проверяем, есть ли найденные продукты
            if len(products) != 0:
                first_product = products[0]
                return first_product.get('nutriments', {}).get('energy-kcal_100g', 0)
    return 0

def get_workout_calory(activity, duration, API_KEY):
    api_url = f'https://api.api-ninjas.com/v1/caloriesburned?activity={activity}'
    response = requests.get(api_url, headers={'X-Api-Key': API_KEY})
    if response.status_code == requests.codes.ok:
        workout_calories_hour = response.json()[0]['calories_per_hour']
        print(workout_calories_hour)
        workout_calories = float(workout_calories_hour) * float(duration) / 60
        print(workout_calories)
        return workout_calories
    return 0

def get_water_baseline(weight, activity_level, temp):
    optimal_water = weight * 30 + 500 * (activity_level // 30) + 750 * int(temp > 25)
    return optimal_water

def get_calory_baseline(weight, height, age, activity_level):
    optimal_calory = weight * 10 + height * 6.25 + - age * 5 + 100 * (activity_level // 60)
    return optimal_calory
