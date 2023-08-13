
#!--------------------------------IMPORT MODULES-----------------------------------# 


import os
from Users import User
from flask import Flask, request, render_template, session


#!--------------------------------FLASK WEB APP------------------------------------#


Web = Flask(__name__)

@Web.route("/")
def home():
    return render_template('index.html')


@Web.route("/select")
def select():
    #** Get authentication code from Spotify redirect **
    code = request.args.get('code')
    
    #** Setup User class by completing Spotify auth process **
    try:
        user = User(code=code)
    except ValueError as e:
        return render_template('error.html')
    
    #** Save refresh as session variable, and render selection page using list of users playlists **
    session['user'] = user.userRefresh
    playlists = user.getUserPlaylists()
    return render_template('select.html', options=list(playlists.items()))


@Web.route("/finished", methods=["POST"])
def finished():
    #** Get selected playlist name **
    playlist = request.form.get("playlist")
    print(playlist)
    
    #** Setup User Object & get info for selected playlist **
    user = User(refresh=session.get('user'))
    playlistInfo = user.getPlaylist(playlist)
    
    #** Get pandas dataframe of audio features for songs in playlist **
    dataFrame = user.getAudioFeatures(list(playlistInfo['tracks'].keys()))
    ordered = user.sortSongs(dataFrame)
    
    #** Create copy of existing playlist **
    details = playlistInfo['playlistInfo']
    playlist = user.createPlaylist(f"{details['name']} [Sorted]", details['public'], details['collaborative'], details['description'])
    
    #** Get list of song uris and add them to playlist just created **
    uris = []
    for id in ordered:
        uris.append(playlistInfo['tracks'][id]['uri'])
    user.addSongs(playlist, uris)
    
    return render_template('success.html', name=f"{playlistInfo['playlistInfo']['name']} [Sorted]")
   
 
if __name__ == "__main__":
    Web.secret_key = os.environ("FLASK_SECRET")
    Web.run(host='0.0.0.0', debug=True)