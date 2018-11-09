#  Deluxe Music Addon
#
#      Copyright (C) 2017
#      http://
#
#  This Program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2, or (at your option)
#  any later version.
#
#  This Program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this Program; see the file LICENSE.txt.  If not, write to
#  the Free Software Foundation, 675 Mass Ave, Cambridge, MA 02139, USA.
#  http://www.gnu.org/copyleft/gpl.html
#

import os
import sys
import urllib
import urlparse

import re
import mechanize
import requests

from BeautifulSoup import BeautifulSoup

import buggalo

import json

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

CommonRootView = 50
FullWidthList = 51
ThumbnailView = 500
PictureWrapView = 510
PictureThumbView = 514

class DeluxeMusic(object):

    def getHTML(self, link):

        # init browser
        br = mechanize.Browser()
        br.set_handle_robots(False)
        #br.set_handle_gzip(True)

        response = br.open(link)
        result = response.read()

        return result

    def showSelector(self):

        if(DEBUG_PLUGIN):
            xbmc.log('- main selector -')

        # add live channel
        pic = os.path.join(ADDON.getAddonInfo('path'), 'icon_live.png')
        self.addPicture2Item('Deluxe Music LIVE', PATH + '?categories=%s' % 'live', pic, BACKG)
        # add audio channel
        pic = os.path.join(ADDON.getAddonInfo('path'), 'icon_audio.png')
        self.addPicture2Item('Deluxe Music Audio', PATH + '?categories=%s' % 'audio', pic, BACKG)
        # add mediathek
        pic = os.path.join(ADDON.getAddonInfo('path'), 'icon_mediathek.png')
        self.addPicture2Item('Deluxe Music Mediathek', PATH + '?categories=%s' % 'media', pic, BACKG)
        # add VideoOfWeek
        pic = os.path.join(ADDON.getAddonInfo('path'), 'icon_week.png')
        self.addPicture2Item('Deluxe Music Video of the Week', PATH + '?categories=%s' % 'week', pic, BACKG)

        xbmcplugin.endOfDirectory(HANDLE)

    def showCategory(self, url):

        if(DEBUG_PLUGIN):
            xbmc.log('- show category %s -' % url)

        if(url == 'live'):

            link = 'https://event.mivitec.net/dist/js/ads_https2.js'
            data = self.getHTML(link)

            match = re.search('player.src.*?src:."(?P<video>.*?)"', data)
            if(match != None):

                play = match.group('video')
                if(not USE_HTTPS):
                    play = play.replace('https','http')

                if(DEBUG_PLUGIN):
                    xbmc.log('- file - ' + play)
                xbmc.Player().play(play)
            else:
                xbmc.executebuiltin('Notification(Deluxe Music,Nothing to play, 2000)')

        elif (url == 'audio'):

            link = 'https://www.deluxemusic.tv/radio/music.html'

            data = self.getHTML(link)
            soup = BeautifulSoup(data)

            table = soup.find('div' , {'class' : 'audioplayer'} )
            if table is not None:
                tables = table.findAll('div')

                image = ''
                link = ''
                title = ''

                for item in tables:

                    if(item["class"] == 'image'):
                        img = item.find('img')
                        image = 'https://www.deluxemusic.tv' + img['src']
                    if(item["class"] == 'info'):
                        title = item.parent['class'].replace('_',' ')
                    if(item["class"] == 'link'):
                        lnk = item.find('a')
                        link = lnk['href']
                        link = link.replace('.html','')
                        link = link.replace('/radio/','')

                        self.addMediaItem(title, PATH + '?playAudio=%s' % link, image)

                xbmcplugin.endOfDirectory(HANDLE)

        elif (url == 'media'):

            thumb =''
            title =''
            idNo=''

            # get mediathek channels
            link = 'https://www.deluxemusic.tv/mediathek.html'

            data = self.getHTML(link)
            soup = BeautifulSoup(data)

            tables = soup.findAll('div' , {'class' : 'csc-default'})

            for one in tables:

                intro = one.find('div' , {'class' : 'egodeluxeelement egodeluxeelement-intro'})
                if intro is not None:

                    m = re.search('<img.src=\"(.*?)\"', str(intro))
                    if(m != None):
                        thumb =  'https://www.deluxemusic.tv' + m.group(1)

                    m = re.search('<header.*?<a.href=.*?>(.*?)\<', str(intro))
                    if(m != None):
                        title =  m.group(1)

                intro = one.find('div' , {'class' : 'egodeluxeelement'})
                if intro is not None:

                    m = re.search('<deluxe-playlist.playlist_id=\"(.*?)\"', str(intro))
                    if(m != None):
                        idNo = m.group(1)
                        self.addPicture2Item(title, PATH + '?categories=%s' % idNo, '', thumb)

            xbmcplugin.endOfDirectory(HANDLE)

        elif (url == 'week'):

            # get video of the week
            link = 'https://www.deluxemusic.tv/video-of-the-week.html'
            data = self.getHTML(link)

            # <deluxe-playlist playlist_id="21">
            m = re.search('<deluxe-playlist.playlist_id="(.*?)">', data)
            if(m != None):
                idNo = m.group(1)

                # api-endpoint
                URL = "https://deluxetv-vimp.mivitec.net/playlist_tag/search_playlist_videos.php"

                # defining a params dict for the parameters to be sent to the API
                DATA = {'playlist_id' : idNo}

                HEADER =  {'Referer' : 'https://www.deluxemusic.tv/video-of-the-week.html',
                           'Origin' : 'https://www.deluxemusic.tv'}

                # sending get request and saving the response as response object
                r = requests.post(url = URL, data = DATA, headers = HEADER)

                # extracting data in json format
                data = r.json()

                key = data[0]['mediakey']
                title = data[0]['title']
                name = data[0]['thumbnail_filename']

                thumb = 'https://deluxetv-vimp.mivitec.net/playlist_embed/thumbs/' + name

                self.addMediaItem(title, PATH + '?subitem=%s' % key, thumb)

            xbmcplugin.endOfDirectory(HANDLE)

        else:

            load = 'https://deluxetv-vimp.mivitec.net/playlist_embed/search_playlist_videos.php'

            data = {'playlist_id' : url}
            data = urllib.urlencode(data)

            header = { 'Host' : 'deluxetv-vimp.mivitec.net' ,
               'Accept' : '*/*',
               'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; WOW64; rv:54.0) Gecko/20100101 Firefox/54.0',
               'Accept-Language' : 'de,en-US;q=0.7,en;q=0.3',
               'Accept-Encoding' : 'gzip, deflate',
               'Content-Type' : 'application/x-www-form-urlencoded; charset=UTF-8',
               'Referer' : 'https://deluxetv-vimp.mivitec.net/playlist_embed/playlist.php?playlist_id=' + url,
               'X-Requested-With' : 'XMLHttpRequest'
            }

            r = requests.post(url = load, data = data, headers = header)
            js = json.loads(r.text)

            for x in xrange(0,len(js)):

                dur = js[x]['duration']
                key = js[x]['mediakey']
                desc = js[x]['description']
                title = js[x]['title']
                thumb = 'https://deluxetv-vimp.mivitec.net/playlist_embed/thumbs/' + js[x]['thumbnail_filename']

                self.addMediaItem(title, PATH + '?subitem=%s' % key, thumb)

            xbmcplugin.endOfDirectory(HANDLE)

    def showSubtitem(self, url):

        if(DEBUG_PLUGIN):
            xbmc.log('- show subitem %s -' % url)

        link = 'https://deluxetv-vimp.mivitec.net/getMedium/' + url + ".mp4"

        if(DEBUG_PLUGIN):
            xbmc.log('- file - ' + link)
        xbmc.Player().play(link)

    def playAudio(self, audio):

        if(DEBUG_PLUGIN):
            xbmc.log('- show playAudio %s -' % audio)

        link = 'https://www.deluxemusic.tv/radio/' + audio + ".html"

        data = self.getHTML(link)
        soup = BeautifulSoup(data)

        table = soup.find('audio')
        if table is not None:
            link = table['src']

            if(DEBUG_PLUGIN):
                xbmc.log('- file - ' + link)
            xbmc.Player().play(link)


#### some functions ####

    def addFolderItem(self, title, url):
        list_item = xbmcgui.ListItem(label=title)
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, True)

    def addPictureItem(self, title, url, thumb):

        list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumb)
        list_item.setArt({'thumb': thumb,
                          'icon': thumb})

        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, True)

    def addPicture2Item(self, title, url, thumb, fanart):

        list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumb)
        list_item.setArt({'thumb': thumb,
                          'icon': thumb,
                          'fanart': fanart})

        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, True)

    def addMediaItem(self, title, url, thumb):

        list_item = xbmcgui.ListItem(label=title, thumbnailImage=thumb)
        list_item.setArt({'thumb': thumb,
                          'icon': thumb,
                          'fanart': BACKG})

        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, False)

#### main entry point ####

if __name__ == '__main__':

    ADDON = xbmcaddon.Addon()
    ADDON_NAME = ADDON.getAddonInfo('name')

    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    BACKG = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    DEBUG_PLUGIN = False;
    USE_HTTPS = False;

    if(str(xbmcplugin.getSetting(HANDLE, 'debug')) == 'true'):
        DEBUG_PLUGIN = True
    if(str(xbmcplugin.getSetting(HANDLE, 'https')) == 'true'):
        USE_HTTPS = True

try:
        deluxe = DeluxeMusic()

        if PARAMS.has_key('categories'):
            deluxe.showCategory(PARAMS['categories'][0])
        elif PARAMS.has_key('subitem'):
            deluxe.showSubtitem(PARAMS['subitem'][0])
        elif PARAMS.has_key('playAudio'):
            deluxe.playAudio(PARAMS['playAudio'][0])
        else:
            deluxe.showSelector()
except Exception:
    buggalo.onExceptionRaised()