#!/usr/bin/python

from urllib2 import urlopen, HTTPError
from urllib import quote
from json import loads
from xml.dom.minidom import parseString
from datetime import datetime, timedelta
from math import floor
from random import randrange
from ConfigParser import DuplicateSectionError, NoOptionError
from logging import getLogger

from kitnirc.modular import Module


_log = getLogger(__name__)

defaults = {
    "default_location_ID": "94709",
    "default_location_name": "home",
    "forecast_length": 12,
    # this won't work if it remains default, but it shouldn't;
    # you need an API key to use this module
    "api_key": 0
}


def time_name(time):
    if time == "12:00 AM":
        return "midnight"
    if time == "12:00 PM":
        return "noon"
    return time


class WeatherModule(Module):
    def __init__(self, *args, **kwargs):
        super(WeatherModule, self).__init__(*args, **kwargs)
        config = self.controller.config
        try:
            config.add_section("weather")
        except DuplicateSectionError:
            pass

        for key in ["default_location_ID", "default_location_name",
                    "forecast_length", "api_key"]:
            try:
                setattr(self, key, config.get("weather", key))
                log_string = "Set {} to {} from config."
                _log.debug(log_string.format(key, getattr(self, key)))
            except NoOptionError:
                setattr(self, key, defaults[key])
                log_string = "Set {} to {} from defaults."
                _log.debug(log_string.format(key, getattr(self, key)))
        self.forecast_length = int(self.forecast_length)

    @Module.handle('PRIVMSG')
    def tell_weather(self, client, actor, recipient, message):
        if str(recipient) != client.user.nick:
            # This was in a channel, not a PM. Was it to us?
            if message.startswith(client.user.nick):
                message = message.split(None, 1)[1]
            elif message.startswith("!rollcall"):
                client.reply(recipient, actor, "Meow!")
                return
            elif message.startswith("!weather"):
                pass
            else:
                # Nope.
                return

        if message.startswith("help"):
            client.reply(recipient, actor,
                         "I'm very simple! Just say !weather to get "
                         "a summary of the {}-hour forecast for {}, or "
                         "!weather <location> for another city, ZIP, "
                         "etc.".format(self.forecast_length,
                                       self.default_location_name))
            return

        if message.startswith("!weather"):
            try:
                where = message.split(None, 1)[1]
            except IndexError:
                where = None
        else:
            # We're in a PM, but didn't ask for help or weather.
            return

        client.reply(recipient, actor, self.get_forecast(where))

    def get_forecast(self, location):
        if location:
            url_location = quote(location)
        else:
            url_location = self.default_location_ID
            location = self.default_location_name
        url = "http://api.wunderground.com/api/{}/conditions/hourly/q/{}.json"
        url = url.format(self.api_key, url_location)
        _log.info("Looking up the weather in {} ({}).".format(url_location,
                                                              location))
        _log.debug("Query URL is {}".format(url))
        f = urlopen(url)
        json_string = f.read()
        f.close
        parsed_json = loads(json_string)

        temperatures = {}
        conditions = []
        types = []
        if "results" in parsed_json["response"]:
            # There was more than one location.
            choices = []
            for city in parsed_json["response"]["results"]:
                if city["state"]:
                    region = city["state"]
                else:
                    region = city["country_name"]
                choices.append("{}, {}".format(city["city"], region))
            choice_string = " / ".join(choices)
            reply = "I don't know which one you mean. Maybe one of these? "
            return reply + choice_string
        elif "hourly_forecast" in parsed_json:
            try:
                next_forecast = parsed_json['hourly_forecast'][0]
            except ValueError:
                return ("Hmm, I didn't get well-formed data from my API. "
                        "Please give me a few minutes and try again. "
                        "Sorry about that.")
            if url_location != self.default_location_ID:
                loc = parsed_json['current_observation']['display_location']
                location = loc['full']
        else:
            return "Sorry, I don't know where that is."
        log_string = "Forecast length setting is {}, got data for {} hours."
        _log.debug(log_string.format(self.forecast_length,
                                     len(parsed_json['hourly_forecast'])))
        self.forecast_length = min(self.forecast_length,
                                   len(parsed_json['hourly_forecast']) - 2)
        _log.debug("Generating {}-hour forecast.".format(self.forecast_length))

        if not randrange(100):
            reply = "The {}-hour forecast for {} is your face."
            return reply.format(self.forecast_length, location)

        for hour in xrange(self.forecast_length):
            forecast = next_forecast
            next_forecast = parsed_json['hourly_forecast'][hour+1]

            condition = forecast['condition'].lower()
            next_condition = next_forecast['condition'].lower()
            next_time = time_name(next_forecast['FCTTIME']['civil'])
            if condition != next_condition:
                conditions.append("{} until {}".format(condition, next_time))
            types.append(condition)

            time = time_name(forecast['FCTTIME']['civil'])
            temperature = forecast['temp']['english']
            if temperature not in temperatures:
                temperatures[temperature] = time

            # print "{}   {}".format(time, condition)

        if not len(conditions) or not conditions[-1].startswith(condition):
            conditions.append(condition)

        unique_types = list(set(types))
        if len(types) >= 4 and len(unique_types) == 2:
            condition_string = ("The {}-hour forecast for {} is "
                                "intermittently {} and {}.")
            condition_string = condition_string.format(self.forecast_length,
                                                       location,
                                                       unique_types[0],
                                                       unique_types[1])
        elif len(conditions) < 4:
            condition_string = "The {}-hour forecast for {} is {}."
            condition_substring = ", then ".join(conditions)
            condition_string = condition_string.format(self.forecast_length,
                                                       location,
                                                       condition_substring)
        else:
            condition_string = "The {}-hour forecast for {} is {}, then {}."
            condition_substring = ", ".join(conditions[:-1])
            condition_string = condition_string.format(self.forecast_length,
                                                       location,
                                                       condition_substring,
                                                       conditions[-1])

        high = max(map(lambda x: int(x), temperatures))
        low = min(map(lambda x: int(x), temperatures))
        temperature_string = ("High is {} degrees at {}. "
                              "Low is {} degrees at {}.")
        temperature_string = temperature_string.format(high,
                                                       temperatures[str(high)],
                                                       low,
                                                       temperatures[str(low)])

        return " ".join([condition_string, temperature_string])

module = WeatherModule
