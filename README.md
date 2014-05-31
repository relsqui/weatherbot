weatherbot
===========

kitn-based IRC bot for summarizing weather forecasts


setup (module in an existing kitn bot)
----------

download just the kitn module file into your bot's directory:
```
wget https://raw.githubusercontent.com/relsqui/weatherbot/master/kitnweather.py
```
get a free API key from weather underground: http://www.wunderground.com/weather/api/

add a [weather] section to your bot's config, containing at least an api_key key with your API key as the value. because of this step, you'll have to reload the config file; restarting the bot will do that if you don't have another way. this is a good time to add kitnweather to your autoloaded modules list if you want to. otherwise, tell your bot to `load kitnweather` when it gets back.


setup (standalone bot)
----------

install dependencies:
```
pip install -r requirements.txt
```

or, if you're not root,
```
pip install --user -r requirements.txt
```

get a free API key from weather underground: http://www.wunderground.com/weather/api/

set up the configuration:
```
cp bot.cfg.example bot.cfg
```
and then open it up and change AT LEAST the following:
* **host**, in the *server* section (to the address of the network you want to connect to)
* **admins** (either set it to yours or remove it if you don't want to control the bot through IRC)
* **channels** (either replace with a list of channels to autojoin, or remove it)
* **api_key**, in the *weather* section (to the key you got from weather underground)

you probably also want to change the nick, password, etc.

start the bot:
```
./start.sh
```


usage
--------

* `!weather` summarizes the forecast for the default location
* `!weather Paris, France` summarizes the forecast for Paris, France
* `weatherbot: help` shows the commands and default values

easter eggs
----------

yes
