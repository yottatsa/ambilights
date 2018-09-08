### Home Assistant Platform to integrate Phillip TVs' Ambilights as a Light Component using the JointSpace API ###HOT_LAVA


import json
import string
import requests
import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.light import (ATTR_BRIGHTNESS, Light, PLATFORM_SCHEMA, ATTR_HS_COLOR,
                                            SUPPORT_BRIGHTNESS, SUPPORT_COLOR, ATTR_EFFECT, SUPPORT_EFFECT)
from homeassistant.const import (CONF_HOST, CONF_NAME, CONF_USERNAME, CONF_PASSWORD)

DEFAULT_DEVICE = 'default'
DEFAULT_HOST = '127.0.0.1'
DEFAULT_USER = ''
DEFAULT_PASS = ''
DEFAULT_NAME = 'TV Ambilights'
DEFAULT_HUE = 360
DEFAULT_SATURATION = 0
DEFAULT_BRIGHTNESS = 255
TIMEOUT = 5.0
CONNFAILCOUNT = 5

REQUIREMENTS = ['ha-philipsjs==0.0.5']

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
	vol.Required(CONF_HOST, default=DEFAULT_HOST): cv.string,
	vol.Optional(CONF_USERNAME, default=DEFAULT_USER): cv.string,
	vol.Optional(CONF_PASSWORD, default=DEFAULT_PASS): cv.string,
	vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string
})

# these are the names of the effects, change the names in the quotes to change the name displayed on the front-end
EFFECT_MANUAL = "Manual"
EFFECT_STANDARD = "Standard"
EFFECT_NATURAL = "Natural"
EFFECT_IMMERSIVE = "Football"
EFFECT_VIVID = "Vivid"
EFFECT_GAME = "Game"
EFFECT_COMFORT = "Comfort"
EFFECT_RELAX = "Relax"
EFFECT_ADAP_BRIGHTNESS = "Lumina"
EFFECT_ADAP_COLOR = "Colora"
EFFECT_RETRO = "Retro"
EFFECT_SPECTRUM = "Spectrum"
EFFECT_SCANNER = "Scanner"
EFFECT_RHYTHM = "Rhythm"
EFFECT_RANDOM = "Party"
EFFECT_HOT_LAVA = "Hot Lava"
DEFAULT_EFFECT = EFFECT_MANUAL

# this is the list of effects, you can safely remove any effects from the list below to remove them from the front-end
AMBILIGHT_EFFECT_LIST = [EFFECT_MANUAL, EFFECT_HOT_LAVA, EFFECT_STANDARD, EFFECT_NATURAL, EFFECT_IMMERSIVE, EFFECT_VIVID, 
                        EFFECT_GAME, EFFECT_COMFORT, EFFECT_RELAX, EFFECT_ADAP_BRIGHTNESS, EFFECT_ADAP_COLOR,
                        EFFECT_RETRO, EFFECT_SPECTRUM, EFFECT_SCANNER, EFFECT_RHYTHM, EFFECT_RANDOM]

def setup_platform(hass, config, add_devices, discovery_info=None):
    import haphilipsjs

    name = config.get(CONF_NAME)
    host = config.get(CONF_HOST)
    user = config.get(CONF_USERNAME)
    password = config.get(CONF_PASSWORD)
    tvapi = haphilipsjs.PhilipsTV(
        host,
        user=user or None,
        password=password or None,
    )
    add_devices([Ambilight(tvapi, name)])

OLD_STATE = [DEFAULT_HUE, DEFAULT_SATURATION, DEFAULT_BRIGHTNESS, DEFAULT_EFFECT]

class Ambilight(Light):

    def __init__(self, tvapi, name):
        self._tv = tvapi
        self._name = name
        self._state = None
        self._connfail = 0
        self._brightness = None
        self._hs = None
        self._available = False
        self._effect = None
        self._effect_list = []


    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state

    @property
    def available(self):
        return self._available

    @property
    def supported_features(self):
        return SUPPORT_BRIGHTNESS | SUPPORT_COLOR | SUPPORT_EFFECT

    @property
    def effect_list(self):
        return self._effect_list

    @property
    def brightness(self):
        return self._brightness

    @property
    def hs_color(self):
        return self._hs

    @property
    def effect(self):
        return self._effect

    @property
    def should_poll(self):
        return True

    def turn_on(self, **kwargs):
        effect = kwargs.get(ATTR_EFFECT)
        if effect:
            if self._tv.setAmbilightStyle(effect):
                self._effect = effect
        return 
        if ATTR_HS_COLOR in kwargs:
            self._hs = kwargs[ATTR_HS_COLOR]
            convertedHue = int(self._hs[0]*(255/360))
            convertedSaturation = int(self._hs[1]*(255/100))
            self._tv._postReq('ambilight/currentconfiguration',{"styleName":"FOLLOW_COLOR","isExpert":True,"algorithm":"MANUAL_HUE",
            "colorSettings":{"color":{"hue":convertedHue,"saturation":convertedSaturation,"brightness":self._brightness},
            "colorDelta":{"hue":0,"saturation":0,"brightness":0},"speed":255}} )

        elif ATTR_BRIGHTNESS in kwargs:
            convertedBrightness = kwargs[ATTR_BRIGHTNESS]
            self._tv._postReq('ambilight/currentconfiguration',{"styleName":"FOLLOW_COLOR","isExpert":True,"algorithm":"MANUAL_HUE",
            "colorSettings":{"color":{"hue":int(self._hs[0]*(255/360)),"saturation":int(self._hs[1]*(255/100)),
            "brightness":convertedBrightness},"colorDelta":{"hue":0,"saturation":0,"brightness":0},"speed":255}} )

        elif ATTR_EFFECT in kwargs:
            effect = kwargs[ATTR_EFFECT]
            self.set_effect(effect)

        else:
            if OLD_STATE[3] == EFFECT_MANUAL:
                self._tv._postReq('ambilight/currentconfiguration',{"styleName":"FOLLOW_COLOR","isExpert":True,"algorithm":"MANUAL_HUE",
                "colorSettings":{"color":{"hue":int(OLD_STATE[0]*(255/360)),"saturation":int(OLD_STATE[1]*(255/100)),
                "brightness":OLD_STATE[2]},"colorDelta":{"hue":0,"saturation":0,"brightness":0},"speed":255}} )
            else: 
                effect = self._effect
                self.set_effect(effect)

    def turn_off(self, **kwargs):
        global OLD_STATE
        OLD_STATE = [self._hs[0], self._hs[1], self._brightness, self._effect]
        self._tv.setAmbilightPower(False)
        self._state = False
		
    def getState(self):
        self._tv.getAmbilight()
        self._tv.getAmbilightStyles()
        if self._tv.ambilight:
            fullstate = self._tv.ambilight['currentconfiguration']
            self._state = self._tv.ambilight['power_on']
            self._available = True
            styleName = fullstate['styleName']
            if styleName:
                if styleName == 'FOLLOW_COLOR':
                    isExpert = fullstate['isExpert']
                    if isExpert == True:
#                         self._state = True
                        colorSettings = fullstate['colorSettings']
                        color = colorSettings['color']
                        hue = color['hue']
                        saturation = color['saturation']
                        bright = color['brightness']
                        self._hs = (hue*(360/255),saturation*(100/255))
                        self._brightness = bright
                        self._effect = EFFECT_MANUAL
                    else:
                        self._hs = (DEFAULT_HUE, DEFAULT_SATURATION)
                        self._brightness = DEFAULT_BRIGHTNESS
                    effect = fullstate['menuSetting']
                    if effect == "HOT_LAVA":
                        self._effect = EFFECT_HOT_LAVA

                elif styleName == 'FOLLOW_VIDEO':
#                     self._state = True
                    self._hs = (DEFAULT_HUE, DEFAULT_SATURATION)
                    self._brightness = DEFAULT_BRIGHTNESS
                    effect = fullstate['menuSetting']
                    if effect == "STANDARD":
                        self._effect = EFFECT_STANDARD
                    elif effect == "NATURAL":
                        self._effect = EFFECT_NATURAL
                    elif effect == "IMMERSIVE":
                        self._effect = EFFECT_IMMERSIVE
                    elif effect == "VIVID":
                        self._effect = EFFECT_VIVID
                    elif effect == "GAME":
                        self._effect = EFFECT_GAME
                    elif effect == "COMFORT":
                        self._effect = EFFECT_COMFORT
                    elif effect == "RELAX":
                        self._effect = EFFECT_RELAX
                    
                elif styleName == 'FOLLOW_AUDIO':
#                     self._state = True
                    self._hs = (DEFAULT_HUE, DEFAULT_SATURATION)
                    self._brightness = DEFAULT_BRIGHTNESS
                    effect = fullstate['menuSetting']
                    if effect == "VU_METER":
                        self._effect = EFFECT_RETRO
                    elif effect == "ENERGY_ADAPTIVE_BRIGHTNESS":
                        self._effect = EFFECT_ADAP_BRIGHTNESS
                    elif effect == "ENERGY_ADAPTIVE_COLORS":
                        self._effect = EFFECT_ADAP_COLOR  
                    elif effect == "SPECTUM_ANALYSER":
                        self._effect = EFFECT_SPECTRUM
                    elif effect == "KNIGHT_RIDER_ALTERNATING":
                        self._effect = EFFECT_SCANNER
                    elif effect == "RANDOM_PIXEL_FLASH":
                        self._effect = EFFECT_RHYTHM
                    elif effect == "MODE_RANDOM":
                        self._effect = EFFECT_RANDOM

        else:
            self._available = False
            self._state = False

    def update(self):
        self._tv.getAmbilight()
        self._tv.getAmbilightStyles()
        if not self._tv.ambilight:
            self._available = False
            self._state = False
            return

        self._available = True
        self._state = True

        if not self._effect_list:
            self._effect_list = list(
                self._tv.ambilight_supportedstyles.values()
            )

        current_effect = (
            self._tv.ambilight['styleName'],
            self._tv.ambilight.get('menuSetting')
        )
        self._effect = self._tv.ambilight_supportedstyles.get(current_effect)

    def set_effect(self, effect):
        if effect:
            if effect == EFFECT_MANUAL:
                self._tv._postReq('ambilight/currentconfiguration',{"styleName":"FOLLOW_COLOR","isExpert":True,"algorithm":"MANUAL_HUE",
                "colorSettings":{"color":{"hue":int(OLD_STATE[0]*(255/360)),"saturation":int(OLD_STATE[1]*(255/100)),
                "brightness":OLD_STATE[2]},"colorDelta":{"hue":0,"saturation":0,"brightness":0},"speed":255}} )
                self._hs = (OLD_STATE[0], OLD_STATE[1])
                self._brightness = OLD_STATE[2]
            elif effect == EFFECT_HOT_LAVA:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_COLOR","isExpert":False,"menuSetting":"HOT_LAVA"})
            elif effect == EFFECT_STANDARD:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_VIDEO","isExpert":False,"menuSetting":"STANDARD"})
            elif effect == EFFECT_NATURAL:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_VIDEO","isExpert":False,"menuSetting":"NATURAL"})
            elif effect == EFFECT_IMMERSIVE:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_VIDEO","isExpert":False,"menuSetting":"IMMERSIVE"})
            elif effect == EFFECT_VIVID:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_VIDEO","isExpert":False,"menuSetting":"VIVID"})
            elif effect == EFFECT_GAME:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_VIDEO","isExpert":False,"menuSetting":"GAME"})
            elif effect == EFFECT_COMFORT:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_VIDEO","isExpert":False,"menuSetting":"COMFORT"})
            elif effect == EFFECT_RELAX:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_VIDEO","isExpert":False,"menuSetting":"RELAX"})
            elif effect == EFFECT_ADAP_BRIGHTNESS:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_AUDIO","isExpert":False,"menuSetting":"ENERGY_ADAPTIVE_BRIGHTNESS"})
            elif effect == EFFECT_ADAP_COLOR:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_AUDIO","isExpert":False,"menuSetting":"ENERGY_ADAPTIVE_COLORS"})
            elif effect == EFFECT_RETRO:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_AUDIO","isExpert":False,"menuSetting":"VU_METER"})
            elif effect == EFFECT_SPECTRUM:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_AUDIO","isExpert":False,"menuSetting":"SPECTRUM_ANALYSER"})
            elif effect == EFFECT_SCANNER:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_AUDIO","isExpert":False,"menuSetting":"KNIGHT_RIDER_ALTERNATING"})
            elif effect == EFFECT_RHYTHM:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_AUDIO","isExpert":False,"menuSetting":"RANDOM_PIXEL_FLASH"})
            elif effect == EFFECT_RANDOM:
                self._tv._postReq('ambilight/currentconfiguration', {"styleName":"FOLLOW_AUDIO","isExpert":False,"menuSetting":"MODE_RANDOM"})

    def _getReq(self, path):
        try:
            if self._connfail:
                self._connfail -= 1
                return None
            resp = self._session.get(BASE_URL.format(self._host, path), verify=False, auth=HTTPDigestAuth(self._user, self._password), timeout=TIMEOUT)
            self.on = True
            return json.loads(resp.text)
        except requests.exceptions.RequestException as err:
            self._connfail = CONNFAILCOUNT
            self.on = False
            return None

    def _postReq(self, path, data):
        try:
            if self._connfail:
                self._connfail -= 1
                return False
            resp = self._session.post(BASE_URL.format(self._host, path), data=json.dumps(data), verify=False, auth=HTTPDigestAuth(self._user, self._password), timeout=TIMEOUT)
            self.on = True
            if resp.status_code == 200:
                return True
            else:
                return False
        except requests.exceptions.RequestException as err:
            self._connfail = CONNFAILCOUNT
            self.on = False
            return False
