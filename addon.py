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

from xml.dom.minidom import parse, parseString

CommonRootView = 50
FullWidthList = 51
ThumbnailView = 500
PictureWrapView = 510
PictureThumbView = 514

#place holder for error message
ERROR_MESSAGE1 = 'line 1'
ERROR_MESSAGE2 = 'line 2'
ERROR_MESSAGE3 = 'line 3'

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
    
        xbmc.log('- main selector -')

        # add live channel
        self.addPicture2Item('Deluxe Music LIVE', PATH + '?categories=%s' % 'live', ICON, BACKG)
        # add audio channel
        self.addPicture2Item('Deluxe Music Audio', PATH + '?categories=%s' % 'audio', ICON, BACKG)

        # get mediathek channels
        
        link = 'https://www.deluxemusic.tv/mediathek.html'
        data = self.getHTML(link)    
        soup = BeautifulSoup(data)

        # search pictures etc
        table = soup.find('div' , {'class' : 'background-wrapper'} ) 
        tables = table.findAll('div' , {'class' : 'csc-default'})

        title = ''
        link = ''
        fanart = ''
        thumb = ''

        for one in tables:
            intro = one.find('div' , {'class' : 'egodeluxeelement egodeluxeelement-intro'})
            if intro is not None:
                # we found a new element
                link = ''
                fanart = ''
                title = ''
                thumb = ''

                style = intro['style']
                if style is not None:
                    match = re.search('background:url.\'(?P<fanart>.*?)\'', style)
                    if(match != None):
                        fanart = 'https://www.deluxemusic.tv' + match.group('fanart')

                header = intro.find('h1')
                if header is not None:
                    # we found a headline
                    title = header.text

                    image = intro.find('img')
                    if image is not None:
                        thumb = 'https://www.deluxemusic.tv' + image['src']

            iframe = one.find('iframe')
            if iframe is not None:
                if(link is ''):
                    link = iframe['src']

                    p = link.find('playlist_id=')
                    if(p>0):
                        id = link[p+12:]
                        
                        #self.addPictureItem(title, PATH + '?categories=%s' % id, thumb)
                        self.addPicture2Item(title, PATH + '?categories=%s' % id, thumb, fanart)
        
        #xbmc.executebuiltin('Container.SetViewMode(%d)' % ThumbnailView)
        xbmcplugin.endOfDirectory(HANDLE)

    def showCategory(self, url):

        xbmc.log('- show category %s -' % url)
        
        if(url == 'live'):
        
            xbmc.executebuiltin('Notification(Deluxe Music,Getting live channel, 2000)') 
            
            link = 'https://www.deluxemusic.tv/tv.html'
            data = self.getHTML(link)    
            soup = BeautifulSoup(data)

            # search for highlights
            iframe = soup.find('iframe') 
            if iframe is not None:
                page = iframe['src']

                data = self.getHTML(page)
                soup = BeautifulSoup(data)

                source = soup.find('source') 
                if source is not None:
                    play = source['src']

                    xbmc.log('- file - ' + play)       
                    xbmc.Player().play(play)
        elif (url == 'audio'):

            link = 'https://www.deluxemusic.tv/radio/music.html'

            data = self.getHTML(link)    
            soup = BeautifulSoup(data)

            table = soup.find('div' , {'class' : 'audioplayer'} ) 
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

            #xbmc.executebuiltin('Container.SetViewMode(%d)' % ThumbnailView)
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

            #xbmc.executebuiltin('Container.SetViewMode(%d)' % ThumbnailView)
            xbmcplugin.endOfDirectory(HANDLE)

    def showSubtitem(self, url):

        xbmc.log('- show subitem %s -' % url)

        link = 'https://deluxetv-vimp.mivitec.net/getMedium/' + url + ".mp4"
            
        xbmc.log('- file - ' + link)       
        xbmc.Player().play(link)

    def playAudio(self, audio):

        xbmc.log('- show playAudio %s -' % audio)

        link = 'https://www.deluxemusic.tv/radio/' + audio + ".html"

        data = self.getHTML(link)    
        soup = BeautifulSoup(data)

        table = soup.find('audio')
        if table is not None:
            link = table['src']
            
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
   
    DEBUG_PLUGIN = True
    DEBUG_HTML = False
    USE_THUMBS = True
    
    ERROR_MESSAGE1 = ADDON.getLocalizedString(30150)
    ERROR_MESSAGE2 = ADDON.getLocalizedString(30151)
    ERROR_MESSAGE3 = ADDON.getLocalizedString(30152)
    
    if(str(xbmcplugin.getSetting(HANDLE, 'debug')) == 'true'):
        DEBUG_PLUGIN = True
    if(str(xbmcplugin.getSetting(HANDLE, 'debugHTML')) == 'true'):
        DEBUG_HTML = True
       
    SITE = xbmcplugin.getSetting(HANDLE, 'siteVersion')    

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