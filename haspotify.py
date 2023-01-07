import configparser
from requests import get
from urllib.parse import urljoin


class HASpotify:
    '''
    this uses home assistant to get the currently playing song album
    '''
    def __init__(self, **kwargs):
        config = configparser.ConfigParser()
        config.read("./config.ini")
        homeassistant = config['homeassistant']

        self.token = kwargs.get("token", homeassistant['token'])
        self.interface = kwargs.get("interace", homeassistant['interface'])
        entity_id = kwargs.get("entity_id", homeassistant['entity_id'])

        url = urljoin(self.interface, 'api/states/')
        self.url = urljoin(url, entity_id)

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "content-type": "application/json",
        }

    def album_cover_url(self):
        response = get(self.url, headers=self.headers)
        try:
            self.cover_url = urljoin(self.interface, response.json()['attributes']['entity_picture'])
        except KeyError:
            self.cover_url = None
        return self.cover_url


if __name__=="__main__":
    sp = HASpotify()