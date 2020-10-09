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

from bs4 import BeautifulSoup

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

            url = 'https://deluxemusic.tv'

            r = requests.get(url)
            if r.status_code == requests.codes.ok:
                result = r.text

                # find webcast
                s1 = 'webcastId:(.*?),'
                match = re.search(s1,result, re.DOTALL)
                if match is not None:
                    webID = match.group(1).strip()
                    xbmc.log('- web ID %s' % webID)

                    # find applicationId
                    s1 = 'applicationId:(.*?),'
                    match = re.search(s1,result, re.DOTALL)
                    if match is not None:
                        appID = match.group(1).strip()
                        xbmc.log('- app ID %s' % appID)

                        url = 'https://player.cdn.tv1.eu/pservices/player/_x_s-' + appID + '_w-' + webID + '/playlist?playout=hls&noflash=true&theov=2.64.0'
                        xbmc.log('- url%s' % url)

                        self.playVideo(url)

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
            title =''
            idNo=''
            postNo = ''

            # get mediathek channels
            link = 'https://deluxemusic.de/mediathek/'

            r = requests.get(link)
            if r.status_code == requests.codes.ok:

                xbmc.log('- load mediathek data')
                result = r.text

                regex = 'data-id="(.*?)".*?data-post-id="(.*?)".*?data-lazy-src="(.*?)"(.*?)<\/a>'
                match = re.findall(regex, result, re.DOTALL)

                for m in match:

                    idNo = m[0]
                    postNo = m[1]
                    thumb = m[2]

                    data = m[3]

                    # try to read title through logo
                    regex = 'alt="(.*?)"'
                    match = re.search(regex, result, re.DOTALL)

                    regex = '<div.class="logo">.*?alt="(.*?)"'
                    match = re.search(regex, data, re.DOTALL)
                    if(match is not None):
                        title = match.group(1)
                        self.addPictureItem(title, PATH + '?playmedia=%s&post=%s' % (idNo,postNo), thumb)

            xbmcplugin.endOfDirectory(HANDLE)

        else:
            # play mediathek files
            self.playVideo(url)

    def showSubtitem(self, url):

        if(DEBUG_PLUGIN):
            xbmc.log('- show subitem %s -' % url)

        link = 'https://deluxetv-vimp.mivitec.net/getMedium/' + url + ".mp4"

        if(DEBUG_PLUGIN):
            xbmc.log('- file - ' + link)
        xbmc.Player().play(link)

    def playVideo(self, url):

        header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:73.0) Gecko/20100101 Firefox/73.0',
                                  'Referer': 'https://player.cdn.tv1.eu/statics/player/6.5.3/standalone/production/index.html?ext=true&l=e&id=player'
                    }

        r = requests.get(url, headers = header)
        if r.status_code == requests.codes.ok:
            result = r.text

            jObj = json.loads(r.text)

            title = jObj['additional']['pl']['entries'][0]['title']
            #print jObj['additional']['pl']['entries'][0]['video']['src']
            #print jObj['additional']['pl']['entries'][0]['images'][1]['src']

            playlist = jObj['additional']['pl']['entries'][0]['video']['src']

            # init playlist
            pl = xbmc.PlayList(1)
            pl.clear()

            playitem = xbmcgui.ListItem(path=playlist)
            playitem.setInfo('video', { 'plot': title })
            playitem.setProperty('inputstreamaddon', 'inputstream.adaptive')
            playitem.setProperty('inputstream.adaptive.manifest_type', 'hls')

            playitem.setContentLookup(False)

            pl.add(playlist,playitem)
            xbmc.Player().play(pl)

    def playMedia(self, id, post):

        link = 'https://deluxemusic.de/wp-admin/admin-ajax.php?action=get_teaser_video&teaser_id=%s&post_id=%s'  % (id,post)
        r = requests.get(link)
        if r.status_code == requests.codes.ok:

            xbmc.log('- teaser')
            result = r.text

            # find playlistId:
            s1 = 'playlistId:(.*?),'
            match = re.search(s1,result, re.DOTALL)
            if match is not None:
                playlistId = match.group(1).strip()
                xbmc.log('- playlistId ID %s' % playlistId)

                # find applicationId
                s1 = 'applicationId:(.*?),'
                match = re.search(s1,result, re.DOTALL)
                if match is not None:
                    appID = match.group(1).strip()
                    xbmc.log('- app ID %s' % appID)

                    # https://player.cdn.tv1.eu/pservices/player/_x_s-2749759488/playlist?playout=hls&noflash=true&theov=2.64.0&pl=3159818244
                    url = 'https://player.cdn.tv1.eu/pservices/player/_x_s-' + appID + '/' + playlistId + '/playlist?playout=hls&noflash=true&theov=2.64.0&pl=' + playlistId
                    xbmc.log('- url%s' % url)

                    self.playVideo(url)




#### some functions ####

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
    elif ('subitem' in PARAMS):
        deluxe.showSubtitem(PARAMS['subitem'][0])
    elif ('playmedia' in PARAMS):
        deluxe.playMedia(PARAMS['playmedia'][0], PARAMS['post'][0])
    else:
        deluxe.showSelector()
#except Exception as e:
#   xbmc.log('DELUXE MUSIC Exception: ' + str(e))