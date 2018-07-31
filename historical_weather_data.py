import numpy as np
import pandas as pd
import requests


def get_historical_forecast_given_time(latitude, longitude, date, time):  # date = "2018-07-29", time = "15:30"
    df = get_historical_forecast_given_date(latitude, longitude, date)
    if df.shape[0] == 0:
        return df
    given_hour, given_minute = time.split(":")
    normalized_time = 60*int(given_hour) + int(given_minute)
    available_times = df["time"].values.tolist()
    available_times_splitted = [available_time.split(":") for available_time in available_times]
    available_normalized_times = [60*int(hour) + int(minute) for hour, minute in available_times_splitted]

    minimum_difference = 1e6
    minimum_difference_index = 0

    for index, available_normalized_time in enumerate(available_normalized_times):
        difference = abs(normalized_time - available_normalized_time)
        if difference < minimum_difference:
            minimum_difference = difference
            minimum_difference_index = index

    return df.loc[[minimum_difference_index]]


def get_historical_forecast_given_date(latitude, longitude, date):  # date = "2018-07-29"
    gid = get_gid(latitude, longitude)
    district_name = get_district_name(gid)
    station_id = get_station_id(gid)
    url = "https://tr.freemeteo.com/havadurumu/" + district_name + "/history/daily-history/?gid=" + str(gid) + "&date=" + date + "&station=" + \
        str(station_id) + "&language=turkish&country=turkey"
    table = pd.read_html(url)[5]
    df = pd.DataFrame(data=table)
    df.drop(columns=['Simge', 'Rüzgarın Şiddeti'], inplace=True)
    df.rename(columns={'Saat': 'time', 'Sıcaklık': 'temperature', 'Hissedilir Sıcaklık': 'windchill_temperature', 'Rüzgar': 'wind_power',
                       'Bağıl Nem': 'relative_humidity', 'Çiğ oluşma derecesi': 'dewpoint_temperature', 'Basınç': 'pressure',
                       'TarifAyrıntılar': 'cloudness'}, inplace=True)
    df['fog_stability_index'] = df['temperature']
    for index, row in df.iterrows():
        df.set_value(index, 'temperature', edit_temperature(row[1]))
        df.set_value(index, 'windchill_temperature', edit_temperature(row[2]))
        df.set_value(index, 'wind_power', edit_wind(row[3]))
        df.set_value(index, 'relative_humidity', edit_relative_humidity(row[4]))
        df.set_value(index, 'dewpoint_temperature', edit_temperature(row[5]))
        df.set_value(index, 'pressure', edit_pressure(row[6]))
        df.set_value(index, 'cloudness', edit_cloudness(row[7]))
        df.set_value(index, 'fog_stability_index', edit_fog_stability_index(row[1], row[5]))
    return df


def get_gid(latitude, longitude):
    url = "https://tr.freemeteo.com/Services/GeoLocation/PointByCoordinates/?cid=213&la=17&lat=" + str(latitude) + "&lon=" + str(longitude)
    source_code = requests.get(url)
    plain_text = str(source_code.text)
    startIndex = plain_text.index("?gid=") + 5
    numbers = []
    for i in range(startIndex, len(plain_text)):
        current_char = plain_text[i]
        if current_char != "&":
            numbers.append(current_char)
        else:
            break
    gid = "".join(numbers)
    return gid


def get_district_name(gid):
    url = "https://tr.freemeteo.com/Services/Weather/SevenDaysChart?la=17&charts=Humidity&pointID=" + str(gid) + "&pointType=Land&unit=Metric&v=2"
    source_code = requests.get(url)
    plain_text = str(source_code.text)
    start_index = plain_text.index("/havadurumu/") + 12
    district_letters = []
    for j in range(start_index, len(plain_text)):
        char_at_j = plain_text[j]
        if char_at_j != "/":
            district_letters.append(char_at_j)
        else:
            break
    district_name = "".join(district_letters)
    return district_name


def get_station_id(gid):
    url = "https://tr.freemeteo.com/Services/Weather/Stations?pointid=" + str(gid) + "&la=17&stationType=CurrentWeather&units=Metric&ck=1"
    source_code = requests.get(url)
    plain_text = str(source_code.text)
    start_index = 7
    station_id_numbers = []
    for j in range(start_index, len(plain_text)):
        char_at_j = plain_text[j]
        if char_at_j != ",":
            station_id_numbers.append(char_at_j)
        else:
            break
    station_id = "".join(station_id_numbers)
    return station_id


def edit_temperature(temperature):
    temperature = str(temperature)
    return int(temperature[:-2])


def edit_wind(wind_power):
    wind_power = str(wind_power)
    try:
        wind_power = wind_power.split()[-2]
        wind_power_numbers = []
        for i in range(len(wind_power)):
            j = len(wind_power) - i - 1
            char_at_j = wind_power[j]
            if char_at_j.isdigit():
                wind_power_numbers.insert(0, char_at_j)
            else:
                break
        return int("".join(wind_power_numbers))
    except:
        return "NA"


def edit_relative_humidity(relative_humidity):
    relative_humidity = str(relative_humidity)
    return float(relative_humidity[:-1])/100


def edit_pressure(pressure):
    pressure = str(pressure)
    pressure = pressure[:-2].replace(',', '.')
    return float(pressure)


def edit_cloudness(cloudness):
    cloudness = str(cloudness)
    if cloudness[42].isdigit():
        return int(cloudness[41:43])
    else:
        return int(cloudness[41])


def edit_fog_stability_index(temperature, dewpoint_temperature):
    temperature = float(temperature)
    dewpoint_temperature = float(dewpoint_temperature)
    fog_stability_index = 0.2*np.log(temperature) / \
        (2*(temperature - dewpoint_temperature) / float(1000))
    return min(fog_stability_index, 5.0)


"""
for i in range(100):
    latitude = 40 + i * 0.01
    for j in range(100):
        longitude = 35 + j * 0.01
        print(latitude, ", ", longitude, ", ", "2018-07-26")
        df = get_historical_forecast_given_time(latitude, longitude, "2018-07-26", "14:36")
        print(df.shape)
        print(df)
        break
        print("############################################")
        print("")
    break
"""
