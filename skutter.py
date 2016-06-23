#!/usr/bin/env python3
import sys, os, re, threading, time, calendar
import pywapi
import dbus, dbus.service
from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GObject
from email.header import decode_header
import urllib.parse, urllib.request
import logging
import shutil
import configparser
import feedparser
import textwrap
import imaplib
import email



MY_NAME = __file__
# Look here: https://weather.codes
CITY_ID = ''
MPRIS = 0
WEATHER = 0
CALENDAR = 0
RSS = 0
IMAP = 0
WEATHER_UPDATE_PERIOD = 0
CALENDAR_UPDATE_PERIOD = 0
RSS_UPDATE_PERIOD = 0
IMAP_UPDATE_PERIOD = 0
LENGTH_TITLE = 0
LENGTH_ARTIST = 0
LENGTH_ALBUM = 0
FEED_ONE = 'http://www.abc.net.au/news/feed/51120/rss.xml'
FEED_TWO = 'http://www.phoronix.com/rss.php'
FEED_THREE = 'http://www.linux.com/feeds/all-content'
FEED_ONE_LINES = 4
FEED_TWO_LINES = 4
FEED_THREE_LINES = 4
rss_one_feed_length = 0
rss_two_feed_length = 0
rss_three_feed_length = 0
line_width = 46
imap0_account = ''
imap0_server = ''
imap0_port = ''
imap0_username = ''
imap0_password = ''
imap1_account = ''
imap1_server = ''
imap1_port = ''
imap1_username = ''
imap1_password = ''



#Replacement for string.format
def insert_data(string, rep_dict):
    pattern = re.compile("|".join([re.escape(k) for k in rep_dict.keys()]), re.M)
    return pattern.sub(lambda x: rep_dict[x.group(0)], string)


#Begin IMAP
class imapThread(threading.Thread):

    def __init__(self, threadID):
        threading.Thread.__init__(self)
        logging.info('IMAP Started with ID ' + str(threadID))
        print ("DEBUG " + imap0_account)
        self.outstring = ''

        try:
            os.mkfifo(os.path.expanduser('~/.local/share/skutter/imap'))
        except IOError:
            pass

    def run(self):
        while True:
            self.imap_info()
            time.sleep(int(IMAP_UPDATE_PERIOD))

    def imap_info(self):
        self.outstring = '<table cellpadding="6"><tr><td style="background-color:#268BD2;color:#eaeaea;"><b>' + imap0_account + '</b></hr></td></tr>'
        if imap0_account != 'None':
            for r,s in self.get_imap(imap0_server, int(imap0_port), imap0_username, imap0_password):
                self.outstring = self.outstring + '<tr><td><b>' + r + '</b><br>' + s + '</td></tr>'

        if imap1_account != 'None':
            self.outstring = self.outstring + '<tr><td style="background-color:#268BD2;color:#eaeaea;"><b>' + imap1_account + '</b></td></tr>'
            for r,s in self.get_imap(imap1_server, int(imap1_port), imap1_username, imap1_password):
                self.outstring = self.outstring + '<tr><td><b>' + r + '</b><br>' + s + '</td></tr>'
        
        self.outstring += '</table>'
        
        #print (self.outstring)
        with open(os.path.expanduser('~/.local/share/skutter/imap'), 'w') as f:
            f.write(self.outstring)
            f.write('\n')
        
    
    def get_imap(self, server, port, user, password):
        messages = []
        
        try:
            m = imaplib.IMAP4_SSL(server, port)
            m.login(user, password)
            m.select('inbox', readonly=True)
        
            result, data = m.uid('search', None, "(UNSEEN)")
            #print (len(data))
            if result == 'OK':
                for latemail in data[0].split():
                    result, data = m.uid('fetch', latemail, '(RFC822)')
                    if result == 'OK':
                        email_message = email.message_from_bytes(data[0][1])
                        dechead, enc = decode_header(email_message['Subject'])[0]
                        if isinstance(dechead, bytes):
                            dechead = dechead.decode(encoding='UTF-8')
                        #print(dechead)
                        decsend, enc = decode_header(email_message['From'])[0]
                        if isinstance(decsend, bytes):
                            decsend = decsend.decode(encoding='UTF-8')
                        #print(decsend)
                        #print(type(email_message['Subject']))
                        messages.append( (dechead, decsend) )
        
            m.close()
            m.logout()
            
        except:
            messages.append( ("Error accessing " + server, "Check account settings") )
        
        return messages





#Listen and send commands to player
class Magpie(dbus.service.Object):

    def __init__(self):
        busName = dbus.service.BusName('org.bedevil.Skutter', bus=dbus.SessionBus())
        dbus.service.Object.__init__(self, busName, '/Control')

    @dbus.service.method('org.bedevil.Skutter', in_signature='s', out_signature='')
    def Player(self, action):
        session_bus = dbus.SessionBus()
        for names in session_bus.list_names():
            if names.startswith('org.mpris.MediaPlayer2'):
                player_proxy = session_bus.get_object(names, '/org/mpris/MediaPlayer2')
                proxy_interface = dbus.Interface(player_proxy, 'org.mpris.MediaPlayer2.Player')
                app_interface = dbus.Interface(player_proxy, 'org.mpris.MediaPlayer2')

                if   action == "pause":
                    proxy_interface.Pause()
                elif action == "play":
                    proxy_interface.Play()
                elif action == "stop":
                    proxy_interface.Stop()
                elif action == "toggle":
                    proxy_interface.PlayPause()
                elif action == "prev":
                    proxy_interface.Previous()
                elif action == "next":
                    proxy_interface.Next()
                elif action == "show":
                    app_interface.Raise()
                break

    @dbus.service.method('org.bedevil.Skutter', in_signature='', out_signature='')
    def Restart(self):
        logging.info('Received request to restart')
        os.execv(MY_NAME, sys.argv)


# Callbacks to respond to music player
class MPRISHandler:

    def __init__(self):
        self.title = ' '
        self.artist = ' '
        self.album = ' '
        self.cover = ' '
        self.metadata = {}
        self.pauseplay = '"/usr/share/skutter/mediapause.png"'
        self.spotify_arturl = ''
        self.format_string = ''

        with open(os.path.expanduser('~/.config/skutter/mpris.format')) as f:
            for line in f:
                if line.startswith('#'):
                    continue
                self.format_string += line

        self.format_string = re.sub(r'>\s+<', '><', self.format_string)

    def callback(self, player, data, flag):
        if 'PlaybackStatus' in data:
            if str(data['PlaybackStatus']) == 'Playing':
                self.pauseplay = '"/usr/share/skutter/mediapause.png"'
            else:
                self.pauseplay = '"/usr/share/skutter/mediaplay.png"'
            self.spew_to_fifo()

        if 'Metadata' in data:
            self.metadata = data['Metadata']

            try:
                self.title = str(self.metadata['xesam:title'])
            except:
                self.title = ' '
            try:
                self.artist = str(self.metadata['xesam:artist'][0])
            except:
                self.artist = ' '
            try:
                self.album = str(self.metadata['xesam:album'])
            except:
                self.album = ' '
            try:
                self.cover = str((self.metadata['mpris:artUrl'])[7:])
                self.cover = urllib.parse.unquote(self.cover)
                self.cover = '"' + self.cover + '"'
            except:
                self.cover = '"/usr/share/skutter/blank.png"'
            try:
                if str(self.metadata['xesam:url'][:4]) == 'http':
                    self.cover = '"/usr/share/skutter/stream.png"'
            except:
                pass
            try:
                if str(self.metadata['mpris:artUrl'][:4]) == 'http':
                    logging.debug(str(self.metadata['mpris:artUrl']))
                    local_cover = os.path.expanduser('~/.local/share/skutter/spot.png')
                    shutil.copyfile('/usr/share/skutter/spotify.png', local_cover)
                    self.cover = '"' + local_cover + '"'
                    try:
                        with urllib.request.urlopen(str(self.metadata['mpris:artUrl'])) as response,\
                        open(local_cover, 'wb') as out_file:
                            shutil.copyfileobj(response, out_file)
                    except:
                        pass
            except:
                pass
            
            if len(self.title) > LENGTH_TITLE:
                self.title = self.title[:LENGTH_TITLE - 3] + '...'
            if len(self.artist) > LENGTH_ARTIST:
                self.artist = self.artist[:LENGTH_ARTIST - 3] + '...'
            if len(self.album) > LENGTH_ALBUM:
                self.album = self.album[:LENGTH_ALBUM - 3] + '...'

            self.spew_to_fifo()

    def callback2(self, player, data, flag):
        if 'MediaPlayer2' in player:
            self.title = ' '
            self.artist = ' '
            self.album = ' '
            self.cover = '"/usr/share/skutter/blank.png"'
            self.spew_to_fifo()

    def spew_to_fifo(self):
        self.mpris_munge = {'{0}': self.title, '{1}': self.artist, '{2}': self.album,
                            '{3}': self.cover, '{4}': self.pauseplay}
        self.out_string = insert_data(self.format_string, self.mpris_munge)

        with open(os.path.expanduser('~/.local/share/skutter/mpris'), 'w') as f:
            f.write(self.out_string)
            f.write('\n')


#Begin Calendar
class calendarThread(threading.Thread):

    def __init__(self, threadID):
        threading.Thread.__init__(self)
        logging.info('Calendar Started with ID ' + str(threadID))

        try:
            os.mkfifo(os.path.expanduser('~/.local/share/skutter/calendar'))
        except IOError:
            pass

    def run(self):
        while True:
            self.calendar_info()
            time.sleep(int(CALENDAR_UPDATE_PERIOD))

    def calendar_info(self):
        weekday = time.strftime("%A")
        month = time.strftime("%B")
        date = int(time.strftime("%e"))
        c = calendar.LocaleHTMLCalendar()
        q = c.formatmonth(int(time.strftime('%Y')),
                                    int(time.strftime('%m'))).replace('\n', '')
        
        month_table_temp = q.replace('padding="0"', 'padding="2"')
        month_table_temp = month_table_temp.replace('td class="',
                                                              'td align="right" class="')
        today = time.strftime("%e").strip()
        j = len(today) + 1
        x = month_table_temp.find('>' + today + '<')

        if x != -1:
            month_table = month_table_temp[:x + 1] \
            + '<span style="font-weight:bold;color:yellow;">' \
            + today + '</span>' + month_table_temp[x + j:]
        else:
            month_table = month_table_temp
        outstring_calendar = '<table align="center" cellspacing="2">\
            <tr><td align="center" style="font-size:16pt;font-weight:bold;color:white;">' \
            + weekday + '  ' + str(date) + ' ' + month + '</td></tr><tr align="center"><td align="center">' + month_table + '</td></tr></table>'

        with open(os.path.expanduser('~/.local/share/skutter/calendar'), 'w') as f:
            f.write(outstring_calendar)

#Begin Weather
class weatherThread(threading.Thread):

    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
        self.format_string = ''
        logging.info('Weather Started with ID '+ str(threadID))

        try:
            os.mkfifo(os.path.expanduser('~/.local/share/skutter/weather'))
        except:
            pass


        with open(os.path.expanduser('~/.config/skutter/weather.format')) as f:
            for line in f:
                if line.startswith('#'):
                    continue
                self.format_string += line
        self.format_string = re.sub(r'>\s+<', '><', self.format_string)

    def run(self):
        while True:
            self.weather_info()
            time.sleep(int(WEATHER_UPDATE_PERIOD))

    def weather_info(self):
        details = pywapi.get_weather_from_yahoo(CITY_ID)

        if 'error' in details:
            logging.critical('City not found. Shutting down weather thread.')
            sys.exit()
        
        weather_data = {'{0}'  : details['location']['city'],
                        '{1}'  : details['condition']['date'],
                        '{2}'  : details['condition']['code'],
                        '{3}'  : details['condition']['temp'],
                        '{4}'  : details['condition']['text'],
                        '{5}'  : details['astronomy']['sunrise'],
                        '{6}'  : details['astronomy']['sunset'],
                        '{7}'  : details['atmosphere']['humidity'],
                        '{8}'  : details['atmosphere']['pressure'],
                        '{9}'  : details['forecasts'][0]['day'],
                        '{10}' : details['forecasts'][0]['text'],
                        '{11}' : details['forecasts'][0]['code'],
                        '{12}' : details['forecasts'][0]['low'],
                        '{13}' : details['forecasts'][0]['high'],
                        '{14}' : details['forecasts'][1]['day'],
                        '{15}' : details['forecasts'][1]['text'],
                        '{16}' : details['forecasts'][1]['code'],
                        '{17}' : details['forecasts'][1]['low'],
                        '{18}' : details['forecasts'][1]['high']}

        outstring = insert_data(self.format_string, weather_data)

        with open(os.path.expanduser('~/.local/share/skutter/weather'), 'w') as g:
            g.write(outstring)


#Begin MPRIS
class mprisThread(threading.Thread):

    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
        logging.info('MPRIS Started with ID '+ str(threadID))

    def run(self):
        global format_string
        if not os.path.isdir(os.path.expanduser('~/.local/share/skutter')):
            os.makedirs(os.path.expanduser('~/.local/share/skutter'))
        try:
            os.mkfifo(os.path.expanduser('~/.local/share/skutter/mpris'))
        except:
            pass

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        bus = dbus.SessionBus()
        music = MPRISHandler()
        bus.add_signal_receiver(music.callback,
                                dbus_interface="org.freedesktop.DBus.Properties",
                                signal_name="PropertiesChanged")
        bus.add_signal_receiver(music.callback2,
                                dbus_interface="org.freedesktop.DBus",
                                signal_name="NameOwnerChanged")
        birdy = Magpie()
        loop = GObject.MainLoop()
        loop.run()


#Begin RSS
class rssThread(threading.Thread):

    def __init__(self, threadID):
        threading.Thread.__init__(self)
        self.threadID = threadID
        logging.info('RSS Started')
        
        try:
            os.mkfifo(os.path.expanduser('~/.local/share/skutter/calendar'))
        except IOError:
            pass
        
        global rss_one_feed_length, rss_two_feed_length, rss_three_feed_length
        self.outstring='<table align="left" cellspacing="6" cellpadding="4">'
        
        logging.info("Feed One Connecting...")
        self.rss_one = feedparser.parse(FEED_ONE)
        
        if not 'title' in self.rss_one.feed:
            logging.debug("Feed One didn't load. Check URL.")
            rss_one_feed_length = -1
        
        logging.info("Feed Two Connecting...")
        self.rss_two = feedparser.parse(FEED_TWO)
        
        if not 'title' in self.rss_two.feed:
            logging.debug("Feed Two didn't load. Check URL.")
            rss_two_feed_length = -1
        
        logging.info("Feed Three Connecting...")
        self.rss_three = feedparser.parse(FEED_THREE)
        
        if not 'title' in self.rss_three.feed:
            logging.debug("Feed Three didn't load. Check URL.")
            rss_three_feed_length = -1

    def run(self):
         while True:
            self.fetch_feeds()
            time.sleep(int(RSS_UPDATE_PERIOD))
    
    def fetch_feeds(self):
        global rss_one_feed_length, rss_two_feed_length, rss_three_feed_length
        if not rss_one_feed_length == -1:
            rss_one_feed_length = min(FEED_ONE_LINES, len(self.rss_one['entries']))
            logging.debug(rss_one_feed_length)
            self.outstring += '<tr><td style="background-color:#268BD2;color:#eaeaea;"><b>' + self.rss_one.feed['title'] + '</td></tr>'
            for i in range(rss_one_feed_length):
                logging.debug(self.rss_one.entries[i].link)
                tmp_title = textwrap.wrap(self.rss_one.entries[i].title, line_width)
                tmp = re.sub('<[^<]+?>', '', self.rss_one.entries[i].summary)
                tmp_summary = textwrap.wrap(tmp, line_width+12)
                self.outstring += '<tr><td><a href="' + self.rss_one.entries[i].link + '"><span style="font-weight:bold;text-decoration:none;">'
                for i in tmp_title:
                    self.outstring += i + '<br>'
                self.outstring = self.outstring[:-4] + '</a></span><br><small>'
                for i in tmp_summary:
                    self.outstring += i + '<br>'
                self.outstring = self.outstring[:-4] + '</small></td></tr>'
            
        
        if not rss_two_feed_length == -1:
            rss_two_feed_length = min(FEED_ONE_LINES, len(self.rss_two['entries']))
            logging.debug(rss_two_feed_length)
            self.outstring += '<tr><td><span style="color:red;font-size:14pt;text-decoration:none;">' + self.rss_two.feed['title'] + '</span></td></tr>'
            for i in range(rss_two_feed_length):
                logging.debug(self.rss_two.entries[i].link)
                tmp_title = textwrap.wrap(self.rss_two.entries[i].title, line_width)
                tmp = re.sub('<[^<]+?>', '', self.rss_two.entries[i].summary)
                tmp_summary = textwrap.wrap(tmp, line_width+12)
                self.outstring += '<tr><td><a href="' + self.rss_two.entries[i].link + '"><span style="color:red;text-decoration:none;">'
                for i in tmp_title:
                    self.outstring += i + '<br>'
                self.outstring = self.outstring[:-4] + '</a></span><br><small>'
                for i in tmp_summary:
                    self.outstring += i + '<br>'
                self.outstring = self.outstring[:-4] + '</small></td></tr>'
        
        if not rss_three_feed_length == -1:
            rss_three_feed_length = min(FEED_ONE_LINES, len(self.rss_three['entries']))
            logging.debug(rss_three_feed_length)
            self.outstring += '<tr><td><span style="color:red;font-size:14pt;text-decoration:none;">' + self.rss_three.feed['title'] + '</span></td></tr>'
            for i in range(rss_three_feed_length):
                logging.debug(self.rss_three.entries[i].link)
                tmp_title = textwrap.wrap(self.rss_three.entries[i].title, line_width)
                tmp = re.sub('<[^<]+?>', '', self.rss_three.entries[i].summary)
                tmp_summary = textwrap.wrap(tmp, line_width+12)
                self.outstring += '<tr><td><a href="' + self.rss_three.entries[i].link + '"><span style="color:red;text-decoration:none;">'
                for i in tmp_title:
                    self.outstring += i + '<br>'
                self.outstring = self.outstring[:-4] + '</a></span><br><small>'
                for i in tmp_summary:
                    self.outstring += i + '<br>'
                self.outstring = self.outstring[:-4] + '</small></td></tr>'

        self.outstring += '</table>'

        with open(os.path.expanduser('~/.local/share/skutter/rss'), 'w') as g:
                g.write(self.outstring)
        



def get_rc(rc_file):
    global CITY_ID, MPRIS, WEATHER, CALENDAR, WEATHER_UPDATE_PERIOD, CALENDAR_UPDATE_PERIOD
    global LENGTH_TITLE, LENGTH_ARTIST, LENGTH_ALBUM, RSS, RSS_UPDATE_PERIOD, IMAP
    global FEED_ONE, FEED_TWO, FEED_THREE, FEED_ONE_LINES, FEED_TWO_LINES, FEED_THREE_LINES
    global line_width, imap0_server, imap0_port, imap0_username, imap0_password
    global imap1_server, imap1_port, imap1_username, imap1_password, IMAP_UPDATE_PERIOD
    global imap0_account, imap1_account
    conf_parser = configparser.ConfigParser()
    rc = conf_parser.read(rc_file)
    rc_sections = conf_parser.sections()
    MPRIS = conf_parser.get('skutter', 'start_mpris')
    WEATHER = conf_parser.get('skutter', 'start_weather')
    CALENDAR = conf_parser.get('skutter', 'start_calendar')
    RSS = conf_parser.get('skutter', 'start_rss')
    IMAP = conf_parser.get('skutter', 'start_imap')
    CITY_ID = conf_parser.get('weather', 'city_id')
    WEATHER_UPDATE_PERIOD = conf_parser.get('weather', 'update_period')
    CALENDAR_UPDATE_PERIOD = conf_parser.get('calendar', 'update_period')
    RSS_UPDATE_PERIOD = conf_parser.get('rss', 'update_period')
    IMAP_UPDATE_PERIOD = conf_parser.get('imap', 'update_period')
    LENGTH_TITLE = int(conf_parser.get('mpris', 'length_title'))
    LENGTH_ARTIST = int(conf_parser.get('mpris', 'length_artist'))
    LENGTH_ALBUM = int(conf_parser.get('mpris', 'length_album'))
    FEED_ONE = conf_parser.get('rss', 'feed_one')
    FEED_TWO = conf_parser.get('rss', 'feed_two')
    FEED_THREE = conf_parser.get('rss', 'feed_three')
    FEED_ONE_LINES = int(conf_parser.get('rss', 'feed_one_lines'))
    FEED_TWO_LINES = int(conf_parser.get('rss', 'feed_two_lines'))
    FEED_THREE_LINES = int(conf_parser.get('rss', 'feed_three_lines'))
    line_width = int(conf_parser.get('rss', 'line_width'))
    imap0_account = conf_parser.get('imap', 'imap0_account')
    imap0_server = conf_parser.get('imap', 'imap0_server')
    imap0_port = conf_parser.get('imap', 'imap0_port')
    imap0_username = conf_parser.get('imap', 'imap0_username')
    imap0_password = conf_parser.get('imap', 'imap0_password')
    imap1_account = conf_parser.get('imap', 'imap1_account')
    imap1_server = conf_parser.get('imap', 'imap1_server')
    imap1_port = conf_parser.get('imap', 'imap1_port')
    imap1_username = conf_parser.get('imap', 'imap1_username')
    imap1_password = conf_parser.get('imap', 'imap1_password')

def main():
    logging.basicConfig(level=logging.INFO,
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        datefmt="%H:%M:%S")

    rc_file = os.path.expanduser('~/.config/skutter/skutterrc')
    
    if not os.path.isdir(os.path.expanduser('~/.config/skutter')):
            logging.debug('local dir does not exist')
            os.mkdir(os.path.expanduser('~/.config/skutter'))

    if os.path.exists(rc_file) == False:
        try:
            logging.info("Local config not found. Copying system config.")
            shutil.copy('/usr/share/skutter/mpris.format',
                            os.path.expanduser('~/.config/skutter/'))
            shutil.copy('/usr/share/skutter/weather.format',
                            os.path.expanduser('~/.config/skutter/'))
            shutil.copy('/usr/share/skutter/skutterrc', rc_file)
        except:
            logging.critical("Unable to find a config. I won't continue.")
            sys.exit(1)

    get_rc(rc_file)

    if not os.path.isdir(os.path.expanduser('~/.local/share/skutter')):
        os.makedirs(os.path.expanduser('~/.local/share/skutter'))
    logging.info(MPRIS)
    if CALENDAR == '1':
        fit1 = calendarThread(1)
        fit1.start()

    if WEATHER == '1':
        fit2 = weatherThread(2)
        fit2.start()

    if MPRIS == '1':
        fit3 = mprisThread(3)
        fit3.start()

    if RSS == '1':
        fit4 = rssThread(4)
        fit4.start()

    if IMAP == '1':
        fit5 = imapThread(5)
        fit5.start()


if __name__ == '__main__':
    main()
