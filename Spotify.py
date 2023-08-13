
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
import base64
import requests
import pandas as pd
from time import sleep
from datetime import datetime


#!--------------------------------SPOTIFY-----------------------------------#


class Spotify():
    
    def __init__(self):

        #** Get Spotify Details **
        self.ID = os.environ["PLAYLIST_CLIENT"]
        self.secret = os.environ["PLAYLIST_SECRET"]

        #** Setup Header For Authentication **
        clientStr = f"{self.ID}:{self.secret}"
        authStr =  base64.urlsafe_b64encode(clientStr.encode()).decode()
        self.authHead = {"Content-Type": "application/x-www-form-urlencoded", 'Authorization': 'Basic {0}'.format(authStr)}

        #** Get A Bot Token For API Calls **
        self.refreshBotToken()


    def refreshBotToken(self):

        #** Request a Token From Spotify Using Client Credentials **
        data = {'grant_type': 'client_credentials', 'redirect_uri': 'http://localhost:5000/select', 'client_id': self.ID, 'client_secret': self.secret}
        authData = requests.post("https://accounts.spotify.com/api/token", data, headers = {'Content-Type': 'application/x-www-form-urlencoded'}).json()
        token = authData['access_token']

        #** Setup Header For Requests Using Client Credentials  **
        self.botHead = {'Accept': "application/json", 'Content-Type': "application/json", 'Authorization': f"Bearer {token}"}
        

    def formatSong(self, song):
        
        #** Add All Artists To A List **
        artists = []
        artistID = []
        for artist in song['artists']:
            if artist['name'] != None:
                artists.append(artist['name'])
                artistID.append(artist['id'])

        #** Format Album Name **
        if song['album']['album_type'] == "single":
            if "feat" in song['name']:
                song['album']['name'] = f"{song['name'].split('feat.')[0]} - Single"
            else:
                song['album']['name'] = f"{song['name']} - Single"

        #** Format Album Release Date **
        months = {'01': 'Jan', '02': 'Feb', '03': 'Mar', '04': 'Apr', '05': 'May', '06': 'Jun', '07': 'Jul', '08': 'Aug', '09': 'Sep', '10': 'Oct', '11': 'Nov', '12': 'Dec'}
        if song['album'] != {}:
            if song['album']['release_date'] != None:
                if "-" in song['album']['release_date']:
                    if len(song['album']['release_date']) > 7:
                        if song['album']['release_date'][0] == 0:
                            song['album']['release_date'] = song['album']['release_date'][8].replace("0", "")
                        date = song['album']['release_date'].split("-")
                        date = f"{date[2]}th {months[date[1]]} {date[0]}"
                    else:
                        date = song['album']['release_date'].split("-")
                        date = f"{months[date[1]]} {date[0]}"
                else:
                    date = song['album']['release_date']
            else:
                date = "N/A"

        #** Fill in Empty Values if Album Information Missing **
        else:
            song['album']['name'] = "N/A"
            song['album']['id'] = None
            song['album']['images'][0]['url'] = None
            date = "N/A"
            
        #** Make Sure No Empty Values Are Left **
        for key in ['popularity', 'explicit']:
            if song[key] == None or song[key] == 0:
                song[key] = "N/A"

        #** Return Dictionary (songs) With Key: <songID> and Value: <dict containing song infomation> **
        songData = {song['id']: {'name': song['name'], 
                                 'artists': artists, 
                                 'artistID': artistID, 
                                 'album': song['album']['name'], 
                                 'albumID': song['album']['id'], 
                                 'art': song['album']['images'][0]['url'], 
                                 'release': date, 
                                 'popularity': song['popularity'], 
                                 'explicit': song['explicit'], 
                                 'preview': song['preview_url'],
                                 'uri': song['uri']}}
        return songData


    def getAudioFeatures(self, songIDs):

        #** Request Audio Features For a List of Spotify IDs **
        songIDs = ",".join(songIDs)
        response = requests.get(f"https://api.spotify.com/v1/audio-features?ids={songIDs}", headers = self.botHead)

        #** Check If Request Was A Success **
        while response.status_code != 200:
            
            #** Check if Bot Credentials Have Expired **
            if 401 == response.status_code:
                self.refreshBotToken()
                response = requests.get(f"https://api.spotify.com/v1/audio-features?ids={songIDs}", headers = self.botHead)
                
            #** Check If Rate Limit Has Been Applied **
            elif 429 == response.status_code:
                print("\n----------------------RATE LIMIT REACHED--------------------")
                print("Location: Spotify -> GetAudioFeatures")
                print(f"Time: {datetime.now().strftime('%H:%M - %d/%m/%Y')}")
                time = response.headers['Retry-After']
                sleep(time)
                response = requests.get(f"https://api.spotify.com/v1/audio-features?ids={songIDs}", headers = self.botHead)
                
            #** Check If Features Not Found, and Return "FeaturesNotFound" **
            elif 404 == response.status_code:
                return "FeaturesNotFound"
            
            #** If Other Error Occurs, Raise Error **
            else:
                print("\n----------------------UNEXPECTED ERROR--------------------")
                print("Location: Spotify -> GetAudioFeatures")
                print(f"Time: {datetime.now().strftime('%H:%M - %d/%m/%Y')}")
                print(f"Error: Spotify Request Code {response.status_code}")
                return "UnexpectedError"
        
        #** Get response content **
        features = response.json()
        features = features['audio_features']
        
        #** Format into pandas dataframe **
        dataFrame = pd.DataFrame(data=features, columns=['id', 'tempo', 'key', 'mode', 'time_signature', 'acousticness', 'danceability', 'energy', 'instrumentalness', 'speechiness', 'valence', 'loudness', 'liveness', 'duration_ms'])
        return dataFrame

   
    def sortSongs(self, dataFrame):
        #** Sort values by tempo within Pandas dataframe **
        dataFrame.sort_values("tempo", inplace=True)
        rows = dataFrame.shape[0]
        
        #** Set pivot as song with lowest tempo & add id as first in ordered list **
        pivot = dataFrame.iloc[0]
        ordered = [pivot.id]
        options = dataFrame
        
        #** Drop pivot and then for each remaining row in the dataframe, find the closest statistical match  **
        while len(ordered) < rows:
            options.drop(pivot.name, inplace=True)
            matches = {}
            for row in options.itertuples():
                matches[row.Index] = self.checkMatch(pivot, row, dataFrame)
            
            #** Set best match as new pivot and append to ordered list. Repeat until all songs ids have been ordered **
            best = max(matches.items(), key=lambda x: x[1])
            pivot = options.loc[best[0]]
            ordered.append(pivot.id)
        return ordered
    
    
    def checkMatch(self, song1, song2, dataFrame):
        #** Get tempo and volume ranges across the dataset **
        tempoRange = abs(dataFrame.iloc[0].tempo - dataFrame.iloc[-1].tempo)
        volumeDf = dataFrame.sort_values("loudness")
        volumeRange = abs(volumeDf.iloc[0].loudness - volumeDf.iloc[-1].loudness)
        
        #** Add 2 times difference between the songs for the columns listed below **
        values = []
        for column in ["acousticness", "energy", "valence", "danceability"]:
            values.append(abs(song1[column] - getattr(song2, column)) * 2)
        
        #** Append combined difference in instrumentalness and liveness as less impactful values **
        values.append(abs(song1.instrumentalness - song2.instrumentalness) + abs(song1.liveness - song2.liveness))
        values.append(abs(song1.speechiness - song2.speechiness))
        
        #** Append value based on difference in key of song between 1 and 11 **
        if song1.key != -1 and song2.key != -1:
            values.append(abs(song1.key - song2.key) / 11)
        
        #** Append 2.5 times different in tempo and 1.5 times difference in volume **
        values.append((abs(song1.tempo - song2.tempo) / tempoRange) * 2.5)
        values.append((abs(song1.loudness - song2.loudness) / volumeRange) * 1.5)
        
        #** Calculate and inverse percentage so higher values before becomes worse match overall **
        percent = 1 - (sum(values) / len(values))
        if song1.mode != song2.mode:
            percent -= 0.05
        
        #** Return percent or 0 if percent is less than 1 **
        if percent > 0:
            return percent
        else:
            return 0
        