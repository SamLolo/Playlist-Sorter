
#!--------------------------------IMPORT MODULES-----------------------------------# 


import requests
from time import sleep
from Spotify import Spotify
from datetime import datetime


#!------------------------------------USER-----------------------------------#


class User(Spotify):
    
    def __init__(self, code=None, refresh=None):
        
        #** Stop both a code and refresh being passed through **
        if code is not None and refresh is not None:
            raise ValueError
        
        super().__init__()

        #** Get A User Token For API Calls **
        if code is not None:
            data = {'grant_type': "authorization_code", 'code': str(code), 'redirect_uri': 'http://localhost:5000/select', 'client_id': self.ID, 'client_secret': self.secret}
            authData = requests.post("https://accounts.spotify.com/api/token", data, self.authHead).json()
            token = authData['access_token']
            self.userRefresh = authData['refresh_token']
            self.userHead = {'Accept': "application/json", 'Content-Type': "application/json", 'Authorization': f"Bearer {token}"}
            self.getUserDetails()
        
        #** Setup using refresh token, for when user has recently authenticated with the system **
        elif refresh is not None:
            self.userRefresh = refresh
            self.refreshUserToken()
            self.getUserDetails()
        else:
            raise ValueError
        
    
    def getUserDetails(self):
        #** Request user details from Spotify Web API, and set key values as class variables **
        userData = requests.get("https://api.spotify.com/v1/me", headers = self.userHead).json()
        self.name = userData['display_name']
        self.userID = userData['id']
        self.profile = userData['images'][0]['url']
        self.URL = userData['external_urls']['spotify']


    def refreshUserToken(self):

        #** Request New User Token From Spotify **
        data = {'grant_type': "refresh_token", 'refresh_token': self.userRefresh, 'client_id': self.ID, 'client_secret': self.secret}
        authData = requests.post("https://accounts.spotify.com/api/token", data, self.authHead).json()

        #** Update Token and User Header **
        token = authData['access_token']
        self.userHead = {'Accept': "application/json", 'Content-Type': "application/json", 'Authorization': f"Bearer {token}"}


    def getUserPlaylists(self):

        #** Iterate Through Requests For User Playlists (50 per Request) **
        playlists = {}
        next = "https://api.spotify.com/v1/me/playlists?limit=50"
        while str(next) != "None":
            response = requests.get(str(next), headers = self.userHead)

            #** Check If Request Was A Success **
            while response.status_code != 200:
            
                #** Check if Bot Credentials Have Expired **
                if 401 == response.status_code:
                    self.refreshUserToken()
                    response = requests.get(str(next), headers = self.userHead)
                    
                #** Check If Rate Limit Has Been Applied **
                elif 429 == response.status_code:
                    print("\n----------------------RATE LIMIT REACHED--------------------")
                    print("Location: Users -> GetUserPlaylists")
                    print(f"Time: {datetime.now().strftime('%H:%M - %d/%m/%Y')}")
                    time = response.headers['Retry-After']
                    sleep(time)
                    response = requests.get(str(next), headers = self.userHead)
                
                #** If Other Error Occurs, Raise Error **
                else:
                    print("\n----------------------UNEXPECTED ERROR--------------------")
                    print("Location: Users -> GetUserPlaylists")
                    print(f"Time: {datetime.now().strftime('%H:%M - %d/%m/%Y')}")
                    print(f"Error: Spotify Request Code {response.status_code}")
                    return "UnexpectedError"

            #** Sort User Playlists into a dictionary **
            playlistData = response.json()
            next = playlistData['next']
            for playlist in playlistData['items']:
                if playlist['owner']['id'] == self.userID:
                    playlists[playlist['id']] = playlist['name']
        
        #** Return Filled Dict Of Playlists **
        return playlists
    
    
    def getPlaylist(self, playlistID):

        #** Get A Playlists Songs **
        response = requests.get(f'https://api.spotify.com/v1/playlists/{playlistID}', headers = self.userHead)

        #** Check If Request Was A Success **
        while response.status_code != 200:
            
            #** Check if User Credentials Have Expired **
            if 401 == response.status_code:
                self.refreshUserToken()
                response = requests.get(f'https://api.spotify.com/v1/playlists/{playlistID}', headers = self.userHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == response.status_code:
                print("\n----------------------RATE LIMIT REACHED--------------------")
                print("Location: Users -> GetPlaylist")
                print(f"Time: {datetime.now().strftime('%H:%M - %d/%m/%Y')}")
                time = response.headers['Retry-After']
                sleep(time)
                response = requests.get(f'https://api.spotify.com/v1/playlists/{playlistID}', headers = self.userHead)
                
            #** Check If Playlist Not Found, and Return "PlaylistNotFound" **
            elif 404 == response.status_code:
                return "PlaylistNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("\n----------------------UNEXPECTED ERROR--------------------")
                print("Location: Users -> GetPlaylist")
                print(f"Time: {datetime.now().strftime('%H:%M - %d/%m/%Y')}")
                print(f"Error: Spotify Request Code {response.status_code}")
                return "UnexpectedError"
        
        #** Itterate Through Each Song And Ignore If Data Empty **
        playlist = response.json()
        songs = {}
        for song in playlist['tracks']['items']:
            if song != []:
            
                #** Get Formatted Data For Each Song **
                songs.update(self.formatSong(song['track']))
        
        #** Return Filled Dictionary Of Songs **
        playlistInfo = {'playlistInfo': {'name': playlist['name'],
                                         'public': playlist['public'],
                                         'collaborative': playlist['collaborative'],
                                         'length': playlist['tracks']['total'],
                                         'description': playlist['description']}, 
                        'tracks': songs}
        if playlist['description'] == "":
            playlistInfo['playlistInfo']['description'] = None
        return playlistInfo
        
    
    def createPlaylist(self, name, public=True, collaborative=False, description=None):
        #** Create a playlist with given data **
        if collaborative:
            public = False
        body = {'name': name, 'public': public, 'collaborative': collaborative}
        if description is not None:
            body['description'] = description
        print(body)
        response = requests.post(f'https://api.spotify.com/v1/users/{self.userID}/playlists', headers = self.userHead, json=body)

        #** Check If Request Was A Success **
        while response.status_code != 201:
            
            #** Check if User Credentials Have Expired **
            if 401 == response.status_code:
                self.refreshUserToken()
                response = requests.post(f'https://api.spotify.com/v1/users/{self.userID}/playlists', headers = self.userHead, json=body)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == response.status_code:
                print("\n----------------------RATE LIMIT REACHED--------------------")
                print("Location: Users -> CreatePlaylist")
                print(f"Time: {datetime.now().strftime('%H:%M - %d/%m/%Y')}")
                time = response.headers['Retry-After']
                sleep(time)
                response = requests.post(f'https://api.spotify.com/v1/users/{self.userID}/playlists', headers = self.userHead, json=body)
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("\n----------------------UNEXPECTED ERROR--------------------")
                print("Location: Users -> CreatePlaylist")
                print(f"Time: {datetime.now().strftime('%H:%M - %d/%m/%Y')}")
                print(f"Error: Spotify Request Code {response.status_code}")
                return "UnexpectedError"
        
        return response.json()['id']
            
    
    def addSongs(self, playlist, songs, position=0):
        #** Add songs to playlist **
        songlist = ",".join(songs)
        body = {'uris': songs, 'position': position}
        response = requests.post(f'https://api.spotify.com/v1/playlists/{playlist}/tracks', headers = self.userHead, json=body)

        #** Check If Request Was A Success **
        while response.status_code != 201:
            
            #** Check if User Credentials Have Expired **
            if 401 == response.status_code:
                self.refreshUserToken()
                response = requests.post(f'https://api.spotify.com/v1/playlists/{playlist}/tracks', headers = self.userHead, json=body)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == response.status_code:
                print("\n----------------------RATE LIMIT REACHED--------------------")
                print("Location: Users -> AddSongs")
                print(f"Time: {datetime.now().strftime('%H:%M - %d/%m/%Y')}")
                time = response.headers['Retry-After']
                sleep(time)
                response = requests.post(f'https://api.spotify.com/v1/playlists/{playlist}/tracks', headers = self.userHead, json=body)
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("\n----------------------UNEXPECTED ERROR--------------------")
                print("Location: Users -> AddSongs")
                print(f"Time: {datetime.now().strftime('%H:%M - %d/%m/%Y')}")
                print(f"Error: Spotify Request Code {response.status_code}")
                return "UnexpectedError"