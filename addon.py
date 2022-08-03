#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Deluxe Music Addon
#
#      Copyright (C) 2020 Mark König
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

import os
import sys
import urllib
import urllib.parse as urlparse
import time

import re
import requests

import json

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin
import xbmcvfs

CommonRootView = 50
FullWidthList = 51
ThumbnailView = 500
PictureWrapView = 510
PictureThumbView = 514

class DeluxeMusic(object):

    def getHTML(self, link):

        response = requests.get(link)
        if (response.status_code == 200):
            return response.text

        return ''

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

        xbmcplugin.endOfDirectory(HANDLE)

    def showCategory(self, url):

        if(DEBUG_PLUGIN):
            xbmc.log('- show category %s -' % url)

        if(url == 'live'):

            url = 'https://deluxemusic.de/mediathek/?v='
            self.playMedia(url)

        elif (url == 'audio'):

            # why they have wired stations names?
            channels = [("Lounge", "deluxe-lounge"),
                        ("Music", "deluxe-music"),
                        ("80s", "deluxe-80s"),
                        ("Easy", "deluxe-easy"),
                        ("Disco", "discodeluxe"),
                        ("Top 40", "deluxe-top40"),
                        ("Jukebox", "jukeboxradio"),
                        ("Dance", "deluxe-famous"),
                        ("New", "deluxe-arrivals"),
                        ("RCK", "rckradio"),
                        ("KAVKA", "kanalkavka"),
                        ("Chefsessel", "deluxe-chefsessel")]

            link = 'https://deluxemusic.de/radio/'

            r = requests.get(link)
            if r.status_code == requests.codes.ok:

                xbmc.log('- load audio data')
                result = r.text

                regex = '<div.class="col-md-3">.*?<a.href="(.*?)".*?alt="(.*?)".*?<img.src="(https:.*?)".*?<\/noscript>'
                match = re.findall(regex,result,re.DOTALL)

                for m in match:

                    name = m[1]
                    xbmc.log('- station ' + name)

                    thumb = m[2]

                    link = ''

                    for a,b in channels:
                        if(a in name):
                            link = b

                    if(len(link) > 0):
                        timestamp = int(time.time())
                        link = "https://deluxe.hoerradar.de/" + link + "-aac-mq?amsparams=playerid:website;skey:" + str(timestamp)
                        self.addMediaItem(name, link, thumb)

            xbmcplugin.endOfDirectory(HANDLE)

        elif (url == 'media'):

            # show mediathek content

            thumb =''
            url = ''

            # get mediathek channels
            link = 'https://deluxemusic.de/mediathek/'

            r = requests.get(link)
            if r.status_code == requests.codes.ok:

                xbmc.log('- load mediathek data')
                result = r.text

                regex = '<a.href="(\?v=.*?)".*?data-id=".*?".*?data-lazy-src="(http.*?)"'
                match = re.findall(regex, result, re.DOTALL)

                for m in match:

                    url = link + m[0]
                    thumb = m[1]

                    self.addPictureItem('', PATH + '?playmedia=%s' % url, thumb)

            xbmcplugin.endOfDirectory(HANDLE)

        else:
            # play mediathek files
            self.playVideo(url)

    def playVideo(self, url):

        # init playlist
        pl = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
        pl.clear()
        pl.add(url)

        xbmc.Player().play(pl)

    def playMedia(self, url):

        xbmc.log('- play mediathek: ' + url)

        r = requests.get(url)
        if r.status_code == requests.codes.ok:
            result = r.text

            # find webID
            s1 = 'dataId:.*?"(.*?)"'
            match = re.search(s1,result, re.DOTALL)

            # fallback Homepage
            if match is None:
                s1 = 'window.playerSource.dataId.*?\'(.*?)\''
                match = re.search(s1,result, re.DOTALL)

            if match is not None:
                webID = match.group(1).strip()

                # get information
                url = 'https://playout.3qsdn.com/config/' + webID+ '?key=0&timestamp=0'

                r = requests.get(url)
                if r.status_code == requests.codes.ok:
                    result = r.text

                    js = json.loads(result)
                    src = js['sources']

                    xbmc.log('- Titlte: ' + js['title'])

                    # get playlist (first entry)
                    for s in src:
                        if src[s] is not None:

                            r = requests.get(src[s])
                            if r.status_code == requests.codes.ok:
                                result = r.text

                                lines = result.split('\n');

                                cnt = 0
                                data = {}

                                # scan for streams / resolution
                                for l in lines:
                                    if l.startswith('#EXT-X-STREAM-INF'):
                                        s1 = 'RESOLUTION=(.*?)x'
                                        match = re.search(s1,l, re.DOTALL)
                                        data[match.group(1)] = lines[cnt + 1]

                                    cnt += 1

                                # find highest resolution
                                resolution = 0
                                link = ''

                                for i, (k, v) in enumerate(data.items()):
                                    if int(k) > resolution:
                                        resolution = int(k)
                                        link = v

                                xbmc.log('- resolution: %s' % resolution)

                                if len(link) > 0:
                                    url = os.path.dirname(src[s]) + '/' + link

                                    xbmc.log('- url: %s' % url)
                                    self.playVideo(url)

                            break

#### some functions ####

# ----------------------------------------------------------------------------

    def addFolderItem(self, title, url):
        list_item = xbmcgui.ListItem(label=title)
        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, True)

    def addPictureItem(self, title, url, thumb):

        list_item = xbmcgui.ListItem(label=title)
        list_item.setArt({'thumb': thumb,
                          'icon': thumb})

        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, True)

    def addPicture2Item(self, title, url, thumb, fanart):

        list_item = xbmcgui.ListItem(label=title)
        list_item.setArt({'thumb': thumb,
                          'icon': thumb,
                          'fanart': fanart})

        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, True)

    def addMediaItem(self, title, url, thumb):

        list_item = xbmcgui.ListItem(label=title)
        list_item.setArt({'thumb': thumb,
                          'icon': thumb,
                          'fanart': BACKG})

        list_item.setInfo('music',{'title', title})
        list_item.setProperty('IsPlayable','true')

        xbmcplugin.addDirectoryItem(HANDLE, url, list_item, False)

#### main entry point ####

# ----------------------------------------------------------------------------

if __name__ == '__main__':

    ADDON = xbmcaddon.Addon()
    ADDON_NAME = ADDON.getAddonInfo('name')

    PATH = sys.argv[0]
    HANDLE = int(sys.argv[1])
    PARAMS = urlparse.parse_qs(sys.argv[2][1:])

    ICON = os.path.join(ADDON.getAddonInfo('path'), 'icon.png')
    BACKG = os.path.join(ADDON.getAddonInfo('path'), 'fanart.jpg')

    DEBUG_PLUGIN = False;

    if(str(xbmcplugin.getSetting(HANDLE, 'debug')) == 'true'):
        DEBUG_PLUGIN = True

#try:
    deluxe = DeluxeMusic()

    if ('categories' in PARAMS):
        deluxe.showCategory(PARAMS['categories'][0])
    elif ('playmedia' in PARAMS):
        deluxe.playMedia(PARAMS['playmedia'][0])
    else:
        deluxe.showSelector()
#except Exception as e:
#   xbmc.log('DELUXE MUSIC Exception: ' + str(e))