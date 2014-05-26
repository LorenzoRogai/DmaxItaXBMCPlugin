import xbmcplugin
import xbmcgui
import urllib, urllib2, urlparse
import json
import httplib
from pyamf import AMF0, AMF3
from pyamf import remoting
from pyamf.remoting.client import RemotingService

thisPlugin = int(sys.argv[1])
apiUrl = "http://www.lorenzorogai.it/dmax/api.php"

height = 1080;#268|356|360|400|572|576
const = "ef59d16acbb13614346264dfe58844284718fb7b"
playerID = 1752666798001;
publisherID = 1265527910001;
playerKey = "AQ~~,AAABJqdXbnE~,swSdm6mQzrEWC8U2s8_PyL570J6HePbQ"

def mainPage():       
    json = getJson(apiUrl)
    for letter in sorted(json):
        addDirectoryItem(letter, {"action" : "letter", "link": letter})     
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showLetter(letter):       
    json = getJson(apiUrl + "?letter=" + letter)
    for showname, showlink in sorted(json.iteritems()):
        addDirectoryItem(showname, {"action" : "show", "link": showlink})     
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showPage(show):       
    json = getJson(apiUrl + "?seasons=" + show)   
    if ("Stagione" in str(json.items()[0][0])):        
        for seasonname, seasonlink in sorted(json.iteritems()):
            addDirectoryItem(seasonname, {"action" : "season", "link": seasonlink})     
    else:
        for episode in sorted(json):
            title = episode
            eplink = json[episode][0]
            img = json[episode][1]      
            desc = json[episode][2] 
            duration = json[episode][3]
            addDirectoryItem(title, {"action" : "episode", "link": eplink}, img, False, desc, duration)
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showPageSeason(link):       
    json = getJson(apiUrl + "?episodes=" + link)
    for episode in sorted(json):
        title = episode
        eplink = json[episode][0]
        img = json[episode][1]    
        desc = json[episode][2] 
        duration = json[episode][3]
        addDirectoryItem(title, {"action" : "episode", "link": eplink}, img, False, desc, duration)
    xbmcplugin.endOfDirectory(thisPlugin)
    
def showEpisode(link):
    json = getJson(apiUrl + "?episode=" + link)
    
    videoId = json[0];
    
    playlistContent = []
    video = play(const, playerID, videoId, publisherID);
    playlistContent.append(video)
  
    return playPlaylist(playlistContent)

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

def playPlaylist(playlistContent):    
    item = xbmcgui.ListItem(path=playlistContent[0][1])    
    xbmcplugin.setResolvedUrl(handle=thisPlugin, succeeded=True, listitem=item)
    xbmc.sleep(4000) 
    xbmc.executebuiltin('Notification(Informazione!,Aspetta 10 secondi per caricare il buffer)') 
    xbmc.sleep(10000)    
    xbmc.executebuiltin('XBMC.PlayerControl(Play)')   
    
def getJson(link):
    response = urllib2.urlopen(link)
    return json.load(response) 
    
def addDirectoryItem(name, parameters={}, pic="", isFolder=True, desc = "", duration = ""):
    li = xbmcgui.ListItem(name, iconImage="DefaultFolder.png", thumbnailImage=pic)
    if duration and desc:
        li.setInfo(type="Video", infoLabels={"title": name, "plot": desc, "duration": duration})
    if duration:
        li.addStreamInfo("video", {"duration": duration})
    if not isFolder:
        li.setProperty('IsPlayable', 'true')
    url = sys.argv[0] + '?' + urllib.urlencode(parameters)
    return xbmcplugin.addDirectoryItem(handle=int(sys.argv[1]), url=url, listitem=li, isFolder=isFolder)

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
    
