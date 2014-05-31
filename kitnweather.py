#!/usr/bin/python

from urllib2 import urlopen, HTTPError
from urllib import quote
from json import loads
from xml.dom.minidom import parseString
from datetime import datetime, timedelta
from math import floor
from random import randrange
from ConfigParser import DuplicateSectionError
from logging import getLogger

from kitnirc.modular import Module


_log = getLogger(__name__)

defaults = {
        "default_location_ID": "94709",
        "default_location_name": "Berkeley, CA",
        "forecast_length": 12,
        # this won't work if it remains default, but it shouldn't;
        # you need an API key to use this module
        "api_key": 0
}


class WeatherModule(Module):
    def __init__(self, *args, **kwargs):
        super(WeatherModule, self).__init__(*args, **kwargs)
        config = self.controller.config
        try:
            config.add_section("weather")
        except DuplicateSectionError:
            pass

        self.default_location_ID = config.get("weather", "default_location_ID",
                                              defaults)
        self.default_location_name = config.get("weather",
                                                "default_location_name",
                                                defaults)
        self.forecast_length = config.get("weather", "forecast_length",
                                          defaults)
        self.api_key = config.get("weather", "api_key", defaults);


    @Module.handle('PRIVMSG')
    def tell_weather(self, client, actor, recipient, message):
        if str(recipient) != client.user.nick:
            # This was in a channel, not a PM. Was it to us?
            if message.startswith(client.user.nick):
                message = message.split(None, 1)[1]
            elif message.startswith("!rollcall"):
                client.reply(recipient, actor, "Meow!");
            elif message.startswith("!weather"):
                pass
            else:
                # Nope.
                return

        if message.startswith("help"):
            help_msg = self.help_msg.format(self.forecast_length, self.default_location)
            client.reply(recipient, actor, help_msg)
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
        _log.info("Looking up the weather in {} ({}).".format(url_location, location))
        f = urlopen("http://api.wunderground.com/api/{}/conditions/hourly/q/{}.json".format(self.api_key, url_location))
        json_string = f.read()
        f.close
        parsed_json = loads(json_string)

        temperatures = {}
        conditions = []
        if parsed_json["response"].has_key("results"):
            # There was more than one location.
            choices = []
            for city in parsed_json["response"]["results"]:
                if city["state"]:
                    region = city["state"]
                else:
                    region = city["country_name"]
                choices.append("{}, {}".format(city["city"], region))
            choice_string = " / ".join(choices)
            return "I don't know which one you mean. Maybe one of these? " + choice_string
        elif parsed_json.has_key("hourly_forecast"):
            next_forecast = parsed_json['hourly_forecast'][0]
            location = parsed_json['current_observation']['display_location']['full']
        else:
            return "Sorry, I don't know where that is."
        self.forecast_length = min(self.forecast_length, len(parsed_json['hourly_forecast']) - 2)

        if not randrange(100):
            return "The {}-hour forecast for {} is your face.".format(self.forecast_length, location)

        for hour in xrange(self.forecast_length):
            forecast = next_forecast
            next_forecast = parsed_json['hourly_forecast'][hour+1]

            condition = forecast['condition'].lower()
            next_condition = next_forecast['condition'].lower()
            next_time = next_forecast['FCTTIME']['civil']
            if condition != next_condition:
                if next_time == "12:00 PM":
                    next_time = "noon"
                if next_time == "12:00 AM":
                    next_time = "midnight"
                conditions.append("{} until {}".format(condition, next_time))

            time = forecast['FCTTIME']['civil']
            temperature = forecast['temp']['english']
            if temperature not in temperatures:
                temperatures[temperature] = time

            # print "{}   {}".format(time, condition)

        if not len(conditions) or not conditions[-1].startswith(condition):
            conditions.append(condition)

        if len(conditions) < 4:
            condition_string = "The {}-hour forecast for {} is {}.".format(self.forecast_length, location, ", then ".join(conditions))
        else:
            condition_string = "The {}-hour forecast for {} is {}, then {}.".format(self.forecast_length, location, ", ".join(conditions[:-1]), conditions[-1])

        high = max(map(lambda x: int(x), temperatures))
        low = min(map(lambda x: int(x), temperatures))
        temperature_string = "High is {} degrees at {}. Low is {} degrees at {}.".format(high, temperatures[str(high)], low, temperatures[str(low)])

        return " ".join([condition_string, temperature_string])

module = WeatherModule
