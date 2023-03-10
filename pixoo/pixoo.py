import base64
import json
import re
import requests
from urllib.parse import urljoin

# for images
from PIL import Image, ImageOps

# for url images
from io import BytesIO

from setup_logger import logger


class PixooAPI:
    # http://doc.divoom-gz.com/web/#/12?page_id=143
    __refresh_limit = 32

    def __init__(self, ip, size=None, refresh=True):
        self._ip = ip
        self._size = size
        self._refresh = refresh
        self.buffer = []

        self.url = f'http://{ip}:80/post'
        self.remote = "https://app.divoom-gz.com/"

    def clamp(self, n, minn, maxn):
        return max(min(maxn, n), minn)

    def __post(self, url, data=None):
        response = requests.post(url, data)
        if response.status_code != 200:
            logger.warning(f"Bad Response Code: {response.status_code}")
        return response

    def __local_error(self):
        self.__error(self.attr_error_code)

    def __remote_error(self):
        self.__error(self.attr_return_code)

    def __error(self, attribute):
        if attribute != 0:
            logger.error(f"There was an error: {attribute}")

    def __remote_post(self, url, data=None):
        response = self.__post(url, data)
        self._set_attribute_from_response(response.json())
        self.__remote_error()

    def _remote_post(self, url=None, data=None):
        url = urljoin(self.remote, url)
        self.__remote_post(url, data)

    def __local_post(self, url=None, data=None):
        response = self.__post(url=url, data=json.dumps(data))
        self._set_attribute_from_response(response.json())
        self.__local_error()

    def _local_post(self, data=None):
        self.__local_post(url=self.url, data=data)

    def __camel_to_snake(self, camel):
        pattern = re.compile(r'(?<!^)(?=[A-Z])')
        snake = pattern.sub('_', camel).lower()
        return snake

    def _set_attribute_from_response(self, response):
        for key in response:
            snake = self.__camel_to_snake(key)
            snake = "_".join(("attr", snake))
            setattr(self, snake, response[key])
            logger.debug(f"Attribute Set: self.{snake} = {response[key]}")

    def find_device(self):
        '''
        Description: get the device list in local network.
        '''
        self._remote_post(url="Device/ReturnSameLANDevice")

    def dial_type(self):
        '''
        Description: select dial type.
        '''
        self._remote_post(url="Channel/GetDialType")

    def dial_list(self, dial_type=None, page=1):
        '''
        Description: select dial List.

        :param dial_type: dial type, returned from self.dial_type()
        :param page: the number of pages, for example 1, Notes: 30 per page (???)
        '''
        if not hasattr(self, 'attr_dial_type_list'):
            self.dial_type()
        if dial_type not in self.attr_dial_type_list:
            print(f"invalid dial type: {dial_type}; available: {self.attr_dial_type_list}")
            return
        data = {"DialType": dial_type, "Page": page}
        self._remote_post(url="Channel/GetDialList", data=data)

    def select_faces_channel(self, clock_id):
        '''
        Description: select Faces channel, device will work on the faces channel.

        :param clock_id: face id
        '''
        data = {"Command": "Channel/SetClockSelectId", "ClockId": clock_id}
        self._local_post(data)

    def get_select_face_id(self):
        '''
        Description: Get working Faces id.
        '''
        data = {"Command": "Channel/GetClockInfo"}
        self._local_post(data)

    def select_channel(self, select_index):
        '''
        Description: select channel, device will move to the selected channel.

        :param select_index: channel id from 0 to 3
            0: Faces
            1: Cloud Channel
            2: Visualizer
            3: Custom
            4: Black Screen
        '''
        data = {"Command": "Channel/SetIndex", "SelectIndex": select_index}
        self._local_post(data)

    def control_custom_channel(self, custom_page_index):
        '''
        Description: select Custom, device will work on the custom channel.

        :param custom_page_index: custom index, 0 to 2
        '''
        data = {"Command": "Channel/SetCustomPageIndex", "CustomPageIndex": custom_page_index}
        self._local_post(data)

    def visualizer_channel(self, eq_position=0):
        '''
        Description: select Visualizer, device will work on visualizer channel.

        :param eq_position: index, start from 0
        '''
        data = {"Command": "Channel/SetEqPosition", "EqPosition": eq_position}
        self._local_post(data)

    def cloud_channel(self, index):
        '''
        Description: select channel, device will move to the selected channel.

        :param select_index: cloud index, from 0 to 3
            0: Recommend gallery
            1: Favourite
            2: Subscribe artist
            3: Album
        '''
        data = {"Command": "Channel/CloudIndex", "Index": index}
        self._local_post(data)

    def get_current_channel(self):
        '''
        Description: get current chnanel.

        :return select_index: channel id from 0 to 3
            0: Faces
            1: Cloud Channel
            2: Visualizer
            3: Custom
            4: Black Screen
        '''
        data = {"Command": "Channel/GetIndex"}
        self._local_post(data)
        return self.attr_select_index

    def set_brightness(self, brightness):
        '''
        Description: it will set the device brightness.

        :param brightness: number from 0 to 100
        '''
        brightness = self.clamp(brightness, 0, 100)
        data = {"Command": "Channel/SetBrightness", "Brightness": brightness}
        self._local_post(data)

    def get_all_setting(self):
        '''
        Description: it will get all settings and be ok at 90104.
            brightness: 0~100, the system brightness
            rotation_flag: 1: it will switch to display faces and gifs
            clock_time: the time of displaying faces and it will be active with RotationFlag = 1
            gallery_time: the time of displaying gifs and it will be active with RotationFlag = 1
            single_gallery_time: the time of displaying each gif
            power_on_channel_id: device will display the channle when it powers on
            gallery_show_time_flag: 1: it will display time at right-top ;
            cur_clock_id: the running's face id
            time_24_flag: the display hour flag
            temperature_mode: the display hour flag
            gyrate_angle: the rotation angle: 0: normal; 1: 90; 2: 180; 3: 270
            mirror_flag: the mirror mode
            light_switch: the screen switch
        '''
        data = {"Command": "Channel/GetAllConf"}
        self._local_post(data)

    def set_weather_area(self, latitude, longitude):
        '''
        Description: it will set the Longitude and latitude which get weather
            information. All data comes from https://openweathermap.org/.

        :param latitude: latitude
        :param longitude: longitude
        '''
        data = {"Command": "Sys/LogAndLat", "Latitude": latitude, "Longitude": longitude}
        self._local_post(data)

    def set_time_zone(self, time_zone_value):
        '''
        Description: it will set the time zone.

        :param time_zone_value: time zone value
        '''
        data = {"Command": "Sys/TimeZone", "TimeZoneValue": time_zone_value}
        self._local_post(data)

    def set_system_time(self, utc):
        '''
        Description: it will set the system time when the device powers on.

        :param utc: utc time
        '''
        data = {"Command": "Device/SetUTC", "Utc": utc}
        self._local_post(data)

    def screen_switch(self, on_off):
        '''
        Description: it will switch the screen

        :param OnOff: 1: on, 0: off
        '''
        data = {"Command": "Channel/OnOffScreen", "OnOff": on_off}
        self._local_post(data)

    def get_device_time(self):
        '''
        Description: it will get the device system time.
            it will be active after 90107.
        '''
        data = {"Command": "Device/GetDeviceTime"}
        self._local_post(data)

    def set_temperature_mode(self, mode):
        '''
        Description: it will set the temperature mode with Fahrenheit or Celsius.

        :param mode: 0: Celsius, 1: Fahrenheit
        '''
        data = {"Command": "Device/SetDisTempMode", "Mode": mode}
        self._local_post(data)

    def set_rotation_angle(self, mode):
        '''
        Description: it will set the screen Rotation angle .

        :param mode: 0:normal, 1:90; 2:180; 3:270
        '''
        data = {"Command": "Device/SetScreenRotationAngle", "Mode": mode}
        self._local_post(data)

    def set_mirror_mode(self, mode):
        '''
        Description: it will set the screen mirror mode.

        :param mode: 0:disable; 1:enable
        '''
        data = {"Command": "Device/SetMirrorMode", "Mode": mode}
        self._local_post(data)

    def set_hour_mode(self, mode):
        '''
        Description: it will set the screen hour24 mode.

        :param mode: 1:24-hour;0:12-hour
        '''
        data = {"Command": "Device/SetTime24Flag", "Mode": mode}
        self._local_post(data)

    def set_hight_light_mode(self, mode):
        '''
        Description: it will set the screen high light mode.

        :param mode: 0:close; 1:open
        '''
        data = {"Command": "Device/SetHighLightMode", "Mode": mode}
        self._local_post(data)

    def set_white_balance(self, r_value, g_value, b_value):
        '''
        Description: it will set the screen White Balance.

        :param r_value: 100; 0 to 100
        :param g_value: 100; 0 to 100
        :param b_value: 100; 0 to 100
        '''
        r_value = self.clamp(r_value, 0, 100)
        g_value = self.clamp(g_value, 0, 100)
        b_value = self.clamp(b_value, 0, 100)
        data = {"Command": "Device/SetHighLightMode",
                "RValue": r_value,
                "GValue": g_value,
                "BValue": b_value}
        self._local_post(data)

    def get_weather_info(self):
        '''
        Description: it will get the display weather information of the device.
        '''
        data = {"Command": "Device/GetWeatherInfo"}
        self._local_post(data)

    def set_countdown_tool(self, minute, second, status):
        '''
        Description: it will contol the the countdown tool .

        :param minute: the countdown's minute
        :param second: the countdown's second
        :param status: 1: start; 0: stop
        '''
        data = {"Command": "Tools/SetTimer",
                "Minute": minute,
                "Second": second,
                "Status": status}
        self._local_post(data)

    def set_stopwatch_tool(self, status):
        '''
        Description: it will contol the the stopwatch tool .

        :param status: 2:reset; 1: start; 0: stop
        :param second: the countdown's second
        :param status: 1: start; 0: stop
        '''
        data = {"Command": "Tools/SetStopWatch",
                "Status": status}
        self._local_post(data)

    def set_scoreboard_tool(self, blue_score, red_score):
        '''
        Description: it will contol the the scoreboard tool .

        :param blue_score: the blue score 0~999
        :param red_score: the red score 0~999
        '''
        data = {"Command": "Tools/SetScoreBoard",
                "BlueScore": blue_score,
                "RedScore": red_score}
        self._local_post(data)

    def set_noise_tool(self, noise_status):
        '''
        Description: it will contol the the noise tool .

        :param noise_status: 1:start; 0:stop
        '''
        data = {"Command": "Tools/SetScoreBoard",
                "NoiseStatus": noise_status}
        self._local_post(data)

    def play_gif(self, filetype, filename):
        '''
        Description: play gif file, the command can select the gif file,
            the folder which includes gif files, and the net gif file.
            the gif files only support the size (1616 ,32 32 ,64 * 64).

        :param filetype: 2:play net file; 1:play tf's folder; 0:play tf's file
        :param filename: 2:net file address; 1:the folder path; 0:the file path
        '''
        data = {"Command": "Device/PlayTFGif",
                "FileType": filetype,
                "FileName": filename}
        self._local_post(data)

    def get_sending_animation_pic_id(self):
        '''
        Description: get the PicId which the command ???Draw/SendHttpGif??????
            It will return the PicId , it's value is the previous gif id plus 1, 
            the command will be implemented after the 90095 version.
        '''
        data = {"Command": "Draw/GetHttpGifId"}
        self._local_post(data)

    def reset_sending_animation_pic_id(self):
        '''
        Description: it will reset gif id , ???Send animation??? will start from PicID=1.
        '''
        data = {"Command": "Draw/ResetHttpGifId"}
        self._local_post(data)

    def send_animation(self, pic_num=1, pic_width=64, pic_offset=0, pic_id=0, pic_speed=60, pic_data=None):
        '''
        Description: send animation to device, and device will loop animation.
            This method only accepts one picture of animation at a time, and the picture format must be
            based on Base64 encoded RGB data. If the animation is composed of N pictures, it will be sent
            in N times, one picture data will be sent each time with the picture offset

        :param pic_num: total number of single pictures in the animation, must be < 60
        :param pic_width: the pixels of the animation, [16, 32, 64]
        :param pic_offset: the frame number of the animation, starting from 0
        :param pic_id: the animation ID, one per animation
        :param pic_speed: the animation speed, in ms, time between frames
        :param pic_data: the picture base64 encoded RGB data, left to right and top to bottom
        '''
        data = {
            "Command": "Draw/SendHttpGif",
            "PicNum": pic_num,
            "PicWidth": pic_width,
            "PicOffset": pic_offset,
            "PicID": pic_id,
            "PicSpeed": pic_speed,
            "PicData": pic_data,
        }
        self._local_post(data)

    def send_text(self, text_id, x, y, dirr, font, text_width, text_string, speed, color, align):
        '''
        Description: send text to device, and device will add one text in current animation.
            the command can be runned after sending animation(the ???Draw/SendHttpGif??? comand).
            the command will be active at 90102 version. It will use font types from app
            animation font, and display in one line, it will scroll if the text's length
            isn't enough. the text height is 16 point.

        :param text_id: the text id is unique and will be replaced with the same ID, it is smaller than 20
        :param x: the start x postion
        :param y: the start y postion
        :param dirr: direction of scroll
            0: scroll left
            1: scroll right
        :param font: 0 to 7, app animation's font
        :param text_width: the text width is based point and bigger than 16, smaller than 64
        :param text_string: the text string is utf8 string and lenght is smaller than 512
        :param speed: the scroll speed if it need scroll, the time (ms) the text move one step
        :param color: the font color, eg:#FFFF00
        :param align: horizontal text alignment, it will support at 90102 version.
            1: left;
            2: middle;
            3: right

        example: self.send_text(0, 0, 0, 0, 0, 64, "Hello World", 0, "#FFFF00", 2)
        '''
        if not hasattr(self, 'attr_font_list'):
            self.get_font_list()
        for _font in self.attr_font_list:
            if _font['id'] == font:
                break
        else:
            print(f"font {font} not found in font list.")
            print("something will still be displayed though.")

        data = {
            "Command": "Draw/SendHttpText",
            "TextId": text_id,
            "x": x,
            "y": y,
            "dir": dirr,
            "font": font,
            "TextWidth": text_width,
            "TextString": text_string,
            "speed": speed,
            "color": color,
            "align": align,
        }
        self._local_post(data)

    def clear_all_text_area(self):
        '''
        Description: it will clear all text area.
        '''
        data = {
            "Command": "Draw/ClearHttpText"
        }
        self._local_post(data)

    def get_font_list(self):
        self._remote_post(url="Device/GetTimeDialFontList")

    def send_display_list(self, item_list, text_id, type, x, y, dir, font, text_width, text_height, text_string, speed, color, update_time, align):
        pass

    def play_buzzer(self, active_time_in_cycle, off_time_in_cycle, play_total_time):
        '''
        Description: it plays the buzzer

        :param active_time_in_cycle: Working time of buzzer in one cycle in milliseconds
        :param off_time_in_cycle: Idle time of buzzer in one cycle in milliseconds
        :param play_total_time: Working total time of buzzer in milliseconds
        '''
        data = {"Command": "Device/PlayBuzzer",
                "ActiveTimeInCycle": active_time_in_cycle,
                "OffTimeInCycle": off_time_in_cycle,
                "PlayTotalTime": play_total_time}
        self._local_post(data)

    def play_divoom_gif(self, file_id):
        pass

    def get_img_upload_list(self, device_id=None, device_mac=None, page=1):
        if not hasattr(self, 'attr_device_list'):
            self.find_device()
        data = {"DeviceId": device_id or self.attr_device_list[0]['DeviceId'],
                "DeviceMac": device_mac or self.attr_device_list[0]['DeviceMac'],
                "Page": page}
        self._remote_post(url="Device/GetImgUploadList", data=data)

    def get_my_like_img_list(self, device_id, device_mac, page):
        pass

    def command_list(self, command_list):
        pass

    def url_command_file(self, command_file):
        pass


class PixooDevice(PixooAPI):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def screen_switch_on(self):
        '''
        turns off the screen
        '''
        self.screen_switch(on_off=1)

    def screen_switch_off(self):
        '''
        turns on the screen
        '''
        self.screen_switch(on_off=0)

    def clear_buffer(self):
        '''
        clears the buffer.
        '''
        self.buffer = []

    def set_buffer(self, buffer):
        '''
        sets the buffer.
        :param buffer: the buffer
        '''
        self.buffer = buffer

    def set_buffer_from_frame(self, frame):
        '''
        :param frame: a single image frame,
            this can be either an image or a frame from a gif
        '''
        if frame.mode != 'RGB':
            frame = frame.convert("RGB")
        buffer = []
        size_x, size_y = frame.size
        for x in range(size_x):
            for y in range(size_y):
                r, g, b = frame.getpixel((x, y))
                buffer.append(r)
                buffer.append(g)
                buffer.append(b)
        self.set_buffer(buffer)

    def _prepare_buffer(self):
        '''
        encodes the buffer
        '''
        self.buffer_str = str(base64.b64encode(bytearray(self.buffer)).decode())

    def send_url_gif(self, url):
        '''
        sends a gif from the internet!
        try this one! https://www.mathworks.com/matlabcentral/mlc-downloads/downloads/submissions/21944/versions/3/screenshot.gif
        or this https://media0.giphy.com/media/3o6vXTpomeZEyxufGU/giphy.gif
        '''
        self._send_url_gif(url)

    def _send_url_gif(self, url=None):
        response = requests.get(url, headers={'User-Agent': 'null'}, stream=True)
        with Image.open(BytesIO(response.content)) as gif:
            self._send_gif(gif)

    def send_local_gif(self, filename):
        self._send_local_gif(filename=filename)

    def _send_local_gif(self, filename=None):
        '''
        this iterates over the frames of a gif and sends them to the device.
        there's some weird stuff going on with the first frames, so we skip them
        '''
        with Image.open(filename) as gif:
            self._send_gif(gif)

    def _send_gif(self, gif=None):
        '''
        This sends the gif, sampling if needed
        '''
        pic_speeds = []
        pic_offset = 0
        total_frames = gif.n_frames
        pic_num, frame_offset = self._sample_gif(gif)

        logger.info(f"{total_frames / frame_offset}")
        self.get_sending_animation_pic_id()
        try:
            while True:
                logger.debug(f"Frame: {pic_offset} of {pic_num}")
                logger.debug(f"Frame offset: {frame_offset}")

                # append pic speeds, use most common
                pic_speeds.append(gif.info['duration'])
                try:
                    pic_speed = mode(pic_speeds)
                except:
                    pic_speed = pic_speeds[0]
                logger.debug(f"Pic Speed: {pic_speed}")

                # prepare data to send
                frame = self.prepare_frame(gif)
                self.set_buffer_from_frame(frame)
                self._prepare_buffer()

                self.send_animation(pic_num=pic_num,
                                    pic_width=self._size,
                                    pic_offset=pic_offset,
                                    pic_id= self.attr_pic_id,
                                    pic_speed=pic_speed * frame_offset,
                                    pic_data=self.buffer_str)
                
                # increment pic offset for the next frame
                pic_offset += 1

                # set gif to next frame
                gif.seek(gif.tell() + frame_offset)
        except EOFError:
            pass

    def _sample_gif(self, gif):
        for denom in range(1, gif.n_frames):
            if gif.n_frames / denom < 60:
                frame_offset = denom
                pic_num = int(gif.n_frames / frame_offset) + (gif.n_frames % frame_offset > 0)
                logger.debug(f"Pic Num {pic_num} with offset {frame_offset}.")
                return (pic_num, frame_offset)

    def send_image(self):
        '''
        This uploads the image in the buffer to the Pixoo 64
        '''
        if not self.buffer:
            print(f"The buffer is empty.")
            return
        self._send_image()

    def _send_image(self):
        self._prepare_buffer()
        self.get_sending_animation_pic_id()
        self.send_animation(pic_num=1,
                            pic_width=self._size,
                            pic_offset=0,
                            pic_id=self.attr_pic_id,
                            pic_speed=1000,
                            pic_data=self.buffer_str)

    def send_url_image(self, img_url):
        self.url_img_to_buffer(img_url)
        self.send_image()

    def url_img_to_buffer(self, img_url):
        response = requests.get(img_url, headers={'User-Agent': 'null'}, stream=True)
        with Image.open(BytesIO(response.content)) as img:
            frame = self.prepare_frame(img)
            self.set_buffer_from_frame(frame)

    def send_local_image(self, filename):
        self.local_img_to_buffer(filename=filename)
        self.send_image()

    def local_img_to_buffer(self, filename=None):
        with Image.open(filename) as img:
            frame = self.prepare_frame(img)
            self.set_buffer_from_frame(frame)

    def prepare_frame(self, frame):
        if True:  # make it square
            x, y = frame.size
            size = max(x, y)
            square = Image.new("RGB", (size, size), (0, 0, 0))
            square.paste(frame, (int((size - x) / 2), int((size - y) / 2)))
            frame = square.resize((self._size, self._size), Image.Resampling.BILINEAR)
        else:
            frame = frame.resize((self._size, self._size), Image.Resampling.BILINEAR)

        frame = frame.rotate(270)
        frame = ImageOps.mirror(frame)
        return frame

    def _fit_to_matrix(self, frame, fill_color=(0, 0, 0):
        '''
        Description: fits the given frame to the matrix, by padding the edges and make
            it square. Adds black bars on the edges by default.

        :param frame: the image frame
        :param fill_color: the color to fill the screen with, default is black
        '''
        x, y = frame.size
        size = max(x, y)
        square = Image.new("RGB", (size, size), fill_color)
        square.paste(frame, (int((size - x) / 2), int((size - y) / 2))
        frame = square.resize((self._size, self._size), Image.Resampling.BILINEAR)

        frame = frame.rotate(270)
        frame = ImageOps.mirror(frame)
        return frame

    def _zoom_to_fit(self, frame, offset=None):
        '''
        Description: zoom into the image to fill the entire matrix, offset

        :param frame: the imagee frame
        :param offset: number of rows to offset from the top, or left of the image
        '''
        x, y = frame.size
        frame = frame.crop()
        

    def make_square(self, min_size):
        pass


class Pixoo64(PixooDevice):
    def __init__(self, ip):
        super().__init__(ip=ip, size=64)


if __name__ == "__main__":
    pixoo = Pixoo64("192.168.0.154")
    # pixoo.screen_switch_on()
    # pixoo.reset_sending_animation_pic_id()
    # pixoo.send_url_gif("https://media0.giphy.com/media/KxhWj5grlueu9ajWXw/200w.gif?cid=82a1493bol3szba1riw6yoe6zdztke27tmh8p8g5a0v7pssf&rid=200w.gif&ct=g")
    # pixoo.send_local_gif("awake.gif")
    pixoo.send_local_image('jules.jpg')
    pixoo.find_device()
