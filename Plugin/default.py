import xbmcplugin
import xbmcgui
import urllib, urllib2, urlparse
import re
import httplib
import json
from bs4 import BeautifulSoup as Soup
from pyamf import AMF0, AMF3
from pyamf import remoting
from pyamf.remoting.client import RemotingService

thisPlugin = int(sys.argv[1])
baseLink = "http://www.dmax.it"
urlShows = baseLink + "/video/programmi"

_regex_extractVideoIds = re.compile("<li data-number=\"[0-9]*\" data-guid=\"([0-9]*)\"");
_regex_extractVideoIdsSingleVideo = re.compile("<param name=\"@videoPlayer\" value=\"(.*?)\" />");

height = 1080;#268|356|360|400|572|576
const = "ef59d16acbb13614346264dfe58844284718fb7b"
playerID = 1752666798001;
publisherID = 1265527910001;
playerKey = "AQ~~,AAABJqdXbnE~,swSdm6mQzrEWC8U2s8_PyL570J6HePbQ"

def mainPage():   
    global thisPlugin
    json = getJson("http://www.lorenzorogai.it/dmax/api.php?action=index")
    for key,var in json.iteritems():
        addDirectoryItem(key, {"action" : "letter", "link": key}) 
    '''page = getPage(urlShows)
    soup = Soup(page)
    for section in soup.findAll("h3", { "class" : "section-title" }):
        letter = section.findChildren()[0].text
        addDirectoryItem(letter, {"action" : "letter", "link": letter}) 
    '''
    xbmcplugin.endOfDirectory(thisPlugin)
    
def getJson(link):
    response = urllib2.urlopen(link)
    return json.load(response) 
    
def showLetter(link):    
    global thisPlugin 
    json = getJson("http://www.lorenzorogai.it/dmax/api.php?action=index")
    for var in json[link]:
        addDirectoryItem(var, {"action" : "letter", "link": var}) 
    '''page = getPage(urlShows)
    soup = Soup(page)
    for program in soup.find("ol", { "class" : "letter-" + link.lower() }).findAll("li"):
        obj = program.findChildren()[0]
        name = obj.text
        showlink = obj['href']           
        addDirectoryItem(name, {"action" : "show", "link": showlink}) '''
    xbmcplugin.endOfDirectory(thisPlugin)

def showPage(link):
    global thisPlugin
    url = urlShows + "/" + link
    page = getPage(url)
    soup = Soup(page)
    obj = soup.find("div", { "id" : "seasons"})
    if (obj != None):
        for season in obj.findAll("li"):
            season = season.findChildren()[0].findChildren()[0].text
            seasonnumber = season[9]       
            addDirectoryItem(season, {"action" : "season", "link": url + "stagioni/" + seasonnumber}) 
    else:
        showPageSeason(urlShows + "/" + link, 1)
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showPageSeason(link, type = None):
    global thisPlugin
    page = getPage(link)
    soup = Soup(page)
    for episode in soup.find("ol", { "class" : ("list medium episodes", "list medium")[type != None]}).findAll("li"):
        obj = episode.findChildren()[0]        
        link = obj['href']
        img = obj.findChildren()[0]['src']
        title = obj['title']
        addDirectoryItem(title, {"action" : "episode", "link": link}, img, isFolder=False)
    xbmcplugin.endOfDirectory(thisPlugin)
        
def showEpisode(link):    
    page = getPage(baseLink + link)
    
    videoIds = list(_regex_extractVideoIds.finditer(page));
    
    if len(videoIds) == 0:
         videoIds = list(_regex_extractVideoIdsSingleVideo.finditer(page));
    
    playlistContent = []
 
    x = 0
    for videoId in videoIds:
        video = play(const, playerID, videoId.group(1), publisherID);
        playlistContent.append(video)
        x = x + 1
        
    return playPlaylist(link, playlistContent)

def build_amf_request(const, playerID, videoPlayer, publisherID):
    env = remoting.Envelope(amfVersion=3)
    env.bodies.append(
        (
            "/1",
            remoting.Request(
                target="com.brightcove.player.runtime.PlayerMediaFacade.findMediaById",
                body=[const, playerID, videoPlayer, publisherID],
                envelope=env
            )
        )
    )
    return env

def get_clip_info(const, playerID, videoPlayer, publisherID):
    conn = httplib.HTTPConnection("c.brightcove.com")
    envelope = build_amf_request(const, playerID, videoPlayer, publisherID)
    conn.request("POST", "/services/messagebroker/amf?playerKey=" + playerKey, str(remoting.encode(envelope).read()), {'content-type': 'application/x-amf'})
    response = conn.getresponse().read()
    response = remoting.decode(response).bodies[0][1].body
    
    return response  

def play(const, playerID, videoPlayer, publisherID):
    rtmpdata = get_clip_info(const, playerID, videoPlayer, publisherID)
    streamName = ""
    default = 'skip'
    streamUrl = rtmpdata.get('FLVFullLengthURL', default);
    
    for item in sorted(rtmpdata['renditions'], key=lambda item:item['frameHeight'], reverse=False):
        streamHeight = item['frameHeight']
        
        if streamHeight <= height:
            streamUrl = item['defaultURL']
    
    streamName = streamName + rtmpdata['displayName'] 
    return [streamName, streamUrl];

def playPlaylist(playlistLink, playlistContent):    
    global thisPlugin
    playlist = "stack://";
    for i in range(len(playlistContent)):
        playlist += playlistContent[i][1];
        if(i!=len(playlistContent)-1):
            playlist += " , ";

    listitem = xbmcgui.ListItem(path=playlist)
    return xbmcplugin.setResolvedUrl(thisPlugin, True, listitem)

def playPlaylistOff(playlistLink, playlistContent):    
    player = xbmc.Player();
    
    playerItem = xbmcgui.ListItem(playlistLink);
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO);
    playlist.clear();
    print "playPlaylist";
    
    for link in playlistContent:
        listItem = xbmcgui.ListItem(link[0]);
        listItem.setProperty("PlayPath", link[1]);
        listItem.addStreamInfo('video',{})
        playlist.add(url=link[1], listitem=listItem);
    
    player.pause()
    xbmc.sleep(100)
    player.play(playlist, playerItem)
    #xbmc.sleep(100) #Wait for Player to open
    
    #xbmc.sleep(100)
    #player.play() #Start playing  
    
def addDirectoryItem(name, parameters={}, pic="", isFolder=True):
    li = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=pic)
    if not isFolder:
        li.setProperty('IsPlayable', 'true')
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=isFolder)

def getPage(url):
    response = urllib2.urlopen(url)
    return response.read()

def get_params():
    param = []
    paramstring = sys.argv[2]
    if len(paramstring) >= 2:
        params = sys.argv[2]
        cleanedparams = params.replace('?', '')
        if (params[len(params) - 1] == '/'):
            params = params[0:len(params) - 2]
        pairsofparams = cleanedparams.split('&')
        param = {}
        for i in range(len(pairsofparams)):
            splitparams = {}
            splitparams = pairsofparams[i].split('=')
            if (len(splitparams)) == 2:
                param[splitparams[0]] = splitparams[1]
                                
        return param

if not sys.argv[2]:
    mainPage()
else:
    params = get_params()
    print params['action']    
    value = urllib.unquote(params['link'])
    print value
    if params['action'] == "letter":
        showLetter(urllib.unquote(params['link']))
    elif params['action'] == "show":
        showPage(urllib.unquote(params['link']))
    elif params['action'] == "season":
        showPageSeason(urllib.unquote(params['link']))    
    elif params['action'] == "episode":
        showEpisode(urllib.unquote(params['link']))
    else:
        mainPage()
        
                
if __name__ == "__main__":
    reload(sys)
    sys.setdefaultencoding("utf-8")
    
