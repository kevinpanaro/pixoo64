import qrcode
import re
from typing import Union


class QRCode():
    def __init__(self, data=None, fill_color="black", back_color="white"):
        self.data = data
        self.fill_color = fill_color
        self.back_color = back_color

    def set_fill_color(self, color: Union[str, tuple]):
        self.fill_color = color

    def set_back_color(self, color: Union[str, tuple]):
        self.back_color = color

    def set_color(self, fill_color: Union[str, tuple], back_color: Union[str, tuple]):
        self.set_fill_color(fill_color)
        self.set_back_color(back_color)

    def generate(self):
        qr = qrcode.QRCode(
            version=10,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=1,
            border=3,
        )
        qr.add_data(self.data)
        qr.make(fit=True)

        self.img = qr.make_image(fill_color=self.fill_color, back_color=self.back_color)

    def buffer(self):
        buffer = []
        for x in range(64):
            for y in range(64):
                try:
                    val = self.img.getpixel((x, y))
                except:
                    val = 255
                buffer.append(val)
                buffer.append(val)
                buffer.append(val)
        return buffer

    def add_url(self, url):
        '''
        nothing gets checked
        '''
        self.data = url

    def add_email(self, address, cc=None, bcc=None, subject=None, body=None):
        '''
        probably add some email validation at some point
        '''
        temp_data = None
        def concat(items):
            if isinstance(items, list):
                items = ','.join(items)
            return(items)

        def format_str(string):
            string = string.split(" ")
            return "%20".join(string)

        temp_data = f"mailto:{address}"

        if cc:
            cc = concat(cc)
            temp_data = f"{temp_data}?cc={cc}"

        if bcc:
            bcc = concat(bcc)
            temp_data = f"{temp_data}?bcc={bcc}"

        if subject:
            subject = format_str(subject)
            temp_data = f"{temp_data}&subject={subject}"

        if body:
            body = format_str(body)
            temp_data = f"{temp_data}&body={body}"

        self.data = temp_data

    def add_phone(self, number, country_code=1):
        temp_data = f"tel:+{country_code}"
        number = re.sub('[^0-9]', '', number)
        temp_data = f"{temp_data}{number}"
        self.data = temp_data

    def add_vcard(self):
        pass

    def add_sms(self, number, method, subject):
        '''
        :param number: the phone number
        :param method: sms, facetime or facetime-audio
        :param subject: a prefilled message to send
        '''
        pass

    def add_maps(self, latitude, longitude, altitude=100):
        self.data = f"geo:{latitude},{longitude},{altitude}"

    def add_calendar_event(self, summary, start, end):
        pass

    def add_wifi(self, T, S, P, H, E, A, I, PH2):
        '''
        :param T: Authentication type; can be WEP
            or WPA or WPA2-EAP, or nopass for no password.
            Or, omit for no password.
        :param S: Network SSID. Required.
            Enclose in double quotes if it is an ASCII name,
            but could be interpreted as hex (i.e. "ABCD")
        :param P: Password, ignored if T is nopass (in which case it may be omitted).
            Enclose in double quotes if it is an ASCII name,
            but could be interpreted as hex (i.e. "ABCD")
        :param H: Optional. True if the network SSID is hidden.
            Note this was mistakenly also used to specify phase 2 method
            in releases up to 4.7.8 / Barcode Scanner 3.4.0.
            If not a boolean, it will be interpreted as phase 2 method (see below)
            for backwards-compatibility
        :param E: (WPA2-EAP only) EAP method, like TTLS or PWD
        :param A: (WPA2-EAP only) Anonymous identity
        :param I: (WPA2-EAP only) Identity
        :param PH2: (WPA2-EAP only) Phase 2 method, like MSCHAPV2
        '''
        pass


if __name__ == "__main__":
    qr = QRCode("Hello World")
