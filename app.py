from flask import Flask,render_template,request,redirect
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from googletrans import Translator
import pyttsx3
import numpy as np
import keras
from tensorflow.keras.preprocessing.sequence import pad_sequences
from keras.preprocessing.text import Tokenizer
import pandas as pd
from pydub import AudioSegment
from pydub.playback import play
from playsound import playsound


tokenizer = pd.read_pickle(r'tokenizer.pickle')
app = Flask(__name__)
app.config["SECRET_KEY"]= 'secret_key'
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///translatorwebsite.db'
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False  
db = SQLAlchemy(app)


# Initialize the pyttsx3 engine
engine = pyttsx3.init()

# Set the voice to use
voices = engine.getProperty('voices')
engine.setProperty('voice', voices[1].id) # use a female voice
sentiment = ['Neutral','Negative','Positive']
best_model = keras.models.load_model("best_model2.hdf5")
max_len = 200

class Contacts(db.Model):
    Slno = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(40), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    msg = db.Column(db.String(500),nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    
@app.route('/')
def index():
    return render_template('home.html')
    
@app.route("/submit",methods=["POST"])
def submit():
    route = request.form['route']
    t_sentence = request.form["sentence"]
    if route == 'translate':
     language = request.form['inputvalue']
     o = Translator().translate(t_sentence, dest=language)
     output=o.text
     return render_template('home.html',output=output,sentence=t_sentence)
    elif route == 'audio':
        t_sentence = request.form["sentence"]
        lines = t_sentence.split(".")
        for line in lines:
            # Analyze the sentiment of the text
            sequence = tokenizer.texts_to_sequences([line])
            test = pad_sequences(sequence, maxlen=max_len)
            s=sentiment[np.around(best_model.predict(test), decimals=0).argmax(axis=1)[0]]

                # Modify the speech parameters based on the sentiment
            if s=='Positive':
                    # Positive sentiment
                engine.setProperty('rate', 175) # increase the speed
                engine.setProperty('pitch', 215) # increase the pitch
            elif s=='Negative':
                    # Negative sentiment
                engine.setProperty('rate', 100) # decrease the speed
                engine.setProperty('pitch', 20) # lower the pitch
            else:
                    # Neutral sentiment
                engine.setProperty('rate', 125) # default settings
                engine.setProperty('pitch', 100)

            engine.say(line)
            s = t_sentence.split(" ")
            for i in s:
                if i=='barking':
                    playsound("dog.wav")
                elif i=='thundering':
                    playsound("cloud.wav")
                elif i=='chirping':
                    playsound(" bird.wav")
            engine.runAndWait()
            #engine.stop()
    else:
         return render_template('home.html')

@app.route('/contact', methods=["GET","POST"])
def contactdetailspage():
    if request.method=="POST":

      name = request.form['name']
      email = request.form['email']
      subject = request.form['subject']
      message  = request.form['message']

      entry = Contacts(name= name, email= email, subject= subject, msg= message)
      
      db.session.add(entry)
      db.session.commit()

    return render_template("home.html")  


@app.route("/admin", methods=["GET", "POST"])
def admin_post():
    if request.method == 'GET':
     post = Contacts.query.all()    
    return render_template('admin.html',post=post)

@app.route("/admin/delete/<int:Slno>")
def admin_post_delete(Slno):
    
    post = Contacts.query.filter_by(Slno=Slno).first()
    db.session.delete(post)
    db.session.commit()
    return redirect('/admin')



if __name__ == '__main__':
    app.run(debug=True)