#!/usr/bin/python
# -*- coding: utf-8 -*-

#  Deluxe Music Addon
#
#      Copyright (C) 2017 Mark König
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
import urlparse

import re
import requests

from BeautifulSoup import BeautifulSoup

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
        # add VideoOfWeek
        pic = os.path.join(ADDON.getAddonInfo('path'), 'icon_week.png')
        self.addPicture2Item('Deluxe Music Video of the Week', PATH + '?categories=%s' % 'week', pic, BACKG)

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

            link = 'https://www.deluxemusic.tv/radio/music.html'

            data = self.getHTML(link)
            soup = BeautifulSoup(data)

            tables = soup.findAll('span' , {'class' : 'csc-uploads-fileName'})

            for one in tables:
                href = one.find('a')
                if(href is not None):

                    txt = href.text
                    name = os.path.splitext(txt)[0]
                    ext = os.path.splitext(txt)[1]

                    if('.m3u' in ext):
                        link = 'https://www.deluxemusic.tv' + href.get('href')
                        self.addMediaItem(name, link,'')

            xbmcplugin.endOfDirectory(HANDLE)

        elif (url == 'media'):

            # show mediathek content

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

                        header = intro.find('h1' , {'class' : 'csc-firstHeader'})
                        if header is not None:
                            title = header.text

                element = one.find('div' , {'class' : 'egodeluxeelement'})
                if element is not None:

                    script = element.find('script')
                    if(script is not None):

                        s1 = 'playlistId:(.*?),'
                        match = re.search(s1, script.string, re.DOTALL)
                        if match is not None:
                            playID = match.group(1)

                            s1 = 'applicationId:(.*?),'
                            match = re.search(s1, script.string, re.DOTALL)
                            if match is not None:
                                appID = match.group(1)

                                url = urllib.quote_plus('https://player.cdn.tv1.eu/pservices/player/_x_s-' + appID + '/playlist?playout=hls&noflash=true&theov=2.64.0&pl=' + playID)
                                self.addPictureItem(title, PATH + '?categories=%s' % url, thumb)

            xbmcplugin.endOfDirectory(HANDLE)

        elif (url == 'week'):

            #  play video of the week
            url = 'https://deluxemusic.de/mediathek/?v=unser-musikvideo-der-woche'

            r = requests.get(url)
            if r.status_code == requests.codes.ok:
                result = r.text

                # find playlistID
                s1 = 'playlistId:(.*?),'
                match = re.search(s1,result, re.DOTALL)
                if match is not None:
                    playlistID = match.group(1).strip()
                    xbmc.log('- playlist ID %s' % playlistID)

                    # find applicationId
                    s1 = 'applicationId:(.*?),'
                    match = re.search(s1,result, re.DOTALL)
                    if match is not None:
                        appID = match.group(1).strip()
                        xbmc.log('- app ID %s' % appID)

                        url = 'https://player.cdn.tv1.eu/pservices/player/_x_s-' + appID + '/playlist?playout=hls&noflash=true&theov=2.64.0&pl=' + playlistID
                        self.playVideo(url)
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

try:
        deluxe = DeluxeMusic()

        if PARAMS.has_key('categories'):
            deluxe.showCategory(PARAMS['categories'][0])
        elif PARAMS.has_key('subitem'):
            deluxe.showSubtitem(PARAMS['subitem'][0])
        else:
            deluxe.showSelector()
except Exception, e:
    xbmc.log('DELUXE MUSIC Exception: ' + str(e))