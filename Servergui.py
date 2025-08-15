#import pygame for playing sound files
import pygame
#import tkinter for the server-side gui
import tkinter as tk
#import ttk for additionally tkinter functionality
from tkinter import ttk
#import sqlite3 for database functionality
import sqlite3
#import webbrowser for creating hyperlinks
import webbrowser
#import os for creating hyperlinks
import os
#import datetime for deleting expired entries
import datetime
#import timedelta for adding times together
from datetime import timedelta

#define the MessageLogApp class
class MessageLogApp:
    def __init__(self, root):
        #initialise the main window
        self.root = root
        self.root.title("Secure Message Log")
        self.root.state("zoomed")
        self.root.geometry("+0+0")

        #set the initial padding (white border) in pixels
        self.padding = 10

        #create a ttk Frame with rounded border style
        self.frame = ttk.Frame(root, style="RoundedFrame", padding=10)
        self.frame.pack(expand=True, fill=tk.BOTH)

        #create a Text widget to display messages, hyperlinks, and buttons
        self.textwidget = tk.Text(self.frame, wrap=tk.WORD, bd=0)  #remove border
        self.textwidget.pack(expand=True, fill=tk.BOTH)
        self.textwidget.config(state="disabled")

        #set window size to maximum screen size
        self.root.geometry(f"{root.winfo_screenwidth()}x{root.winfo_screenheight()}")

        #bind the Resizeimage method to the Configure event
        root.bind("<Configure>", self.Resizetextwidget)

        #define the last database update long ago
        self.lastupdate = "2000-01-01 00:00:00"
        
        #initialise the pygame audio mixer
        pygame.mixer.init()
        
        #call the addentry function after 1 second
        self.root.after(1000, self.Addentry)
        self.root.mainloop()

    def Resizetextwidget(self, event):
        #resize the text widget to fit the window
        self.textwidget.configure(width=event.width - 2 * self.padding,
                                  height=event.height - 2 * self.padding)

    def Addentry(self):
        #open a connection to the database
        conn = sqlite3.connect("Server.db")
        cursor = conn.cursor()

        #define the command to be executed
        retrievedata = """
            SELECT userid, content, timetolive, datatype, timestamp FROM messagelog WHERE timestamp > ?
        """
        #execute the command
        cursor.execute(retrievedata, (self.lastupdate,))
        #store the result of the operation and close the database
        data = cursor.fetchall()
        conn.close()

        #define the path to write entries in that have a set timetolive
        folder = "uploads"
        filepath = os.path.join(folder, "timetolivetracker.txt")
        #ensure the data is only written once
        written = False
        for row in data:
            #define necessary variables
            userid, content, timetolive, self.datatype, timestamp = row

            #define the prefix for all messages which includes the user that sent the data and the time at which they sent it
            prefix = "".join((userid, " @ ", str(timestamp[11:]), " -->"))
            
            #add the entry to the gui depending on the datatype
            if self.datatype == "text":
                self.Addtextentry(prefix, content)
            elif self.datatype == "png":
                self.Addimageentry(prefix, content)
            elif self.datatype == "wav":
                self.Addsoundentry(prefix, content)
            #redefine lastupdate so that it matches the last time the database was checked so that duplicate entries are not added
            self.lastupdate = timestamp
    
            #if there is a set timetolive and the entry hasn't already been written to the file
            if(timetolive != 0 and written == False):
                #write the timestamp of the entry and its timetolive to a file
                f = open(filepath, "a")
                f.write(f"{timestamp}%{timetolive}\n")
                f.close()
                written = True
        
        
        #read the timetolivetracker file for all entries with a timetolive
        f = open(filepath, "r")
        lines = f.readlines()
        f.close()
        #define the current time
        currenttime = str(datetime.datetime.now())[:19]
        currenttime = datetime.datetime.strptime(currenttime, "%Y-%m-%d %H:%M:%S")
        
        #for each entry in the timetolivetracker
        for line in lines:
            #get the timestamp and timetolive of each entry
            timestamp, timetolive = line.strip().split("%")
            timestamp = datetime.datetime.strptime(timestamp, "%Y-%m-%d %H:%M:%S")
            timetolive = int(timetolive)
            #if the current time is past the entry's timetolive
            if currenttime > timestamp + timedelta(seconds=timetolive):
                #entry has expired
                self.Deleteentry(timestamp, self.datatype, filepath)
        
        #call itself after 1 second for regular checks of new database updates
        self.root.after(1000, self.Addentry)

    def Deleteentry(self, timestamp, datatype, filepath):
        #open a connection to the database
        conn = sqlite3.connect("Server.db")
        cursor = conn.cursor()
        
        #define the command to be executed
        delete = """
            DELETE FROM messagelog WHERE timestamp = ?
        """
        
        #execute the command
        cursor.execute(delete, (timestamp,))
        #save changes and close the database
        conn.commit()
        conn.close()

        #get all the lines currently displayed by the gui
        lines = self.textwidget.get("1.0", tk.END).split("\n")
        linenum = None
        
        #for each line
        for i, line in enumerate(lines):
            #if the timestamp that is being looked for (to be deleted) is in the line it is the correct line to delete
            if str(timestamp)[-8:] in line:
                linenum = i
                break
        
        #if the line was found
        if linenum is not None:
            #remove line from tkinter text widget (including hyperlink if there is one)
            self.textwidget.config(state="normal")
            self.textwidget.delete(f"{linenum + 1}.0", f"{linenum + 2}.0")
            self.textwidget.config(state="disabled")
            if datatype == "wav":
                #remove the play button
                playbuttonlinenum = linenum + 1
                self.textwidget.config(state="normal")
                self.textwidget.delete(f"{playbuttonlinenum}.0", f"{playbuttonlinenum}.end")
            
                #remove the pause button
                pausebuttonlinenum = linenum + 2
                self.textwidget.delete(f"{pausebuttonlinenum}.0", f"{pausebuttonlinenum}.end")
                self.textwidget.config(state="disabled")                
        
        else:
            print("Error occured when attempting to delete entry: Line to delete could not be found in GUI")
        
        #open timetolivetracker
        f = open(filepath, "r")
        lines = f.readlines()
        #read and store every line except from the once we just deleted
        lines = [line for line in lines if not line.startswith(str(timestamp))]
        f.close()
        #write the new data to the file (the same excluding the deleted line)
        f = open(filepath, "w")
        f.writelines(lines)
        f.close()
        

    def Addtextentry(self, prefix, content):
        #define the message to be added
        message = f"{prefix} {content}\n"
        #insert the message into the text widget
        self.textwidget.config(state="normal")
        self.textwidget.insert(tk.END, message)
        self.textwidget.see(tk.END)
        self.textwidget.config(state="disabled")
        
    def OpenImage(event, content):
        #define the image to open
        filename = content.split('/')[-1]
        url = "file:///" + os.path.realpath(filename)
        #open the image in the default app
        webbrowser.open(url)
        
    def Addimageentry(self, prefix, content):
        #define the message to be added
        message = f"{prefix} Image: "
        #insert the message into the text widget
        self.textwidget.config(state="normal")
        self.textwidget.insert(tk.END, message)
        
        #define the label for the hyperlink
        hyperlink = prefix.split("@")
        hyperlink = hyperlink[0].strip()
        hyperlink = "PNG sent by " + hyperlink
        
        #insert the hyperlink into the text widget
        self.textwidget.insert(tk.END, hyperlink, "link")
        self.textwidget.tag_configure("link", foreground="blue", underline=1)
        self.textwidget.tag_bind("link", "<Button-1>", lambda event: self.OpenImage(content))
        
        #add a new line
        self.textwidget.insert(tk.END, "\n")

        self.textwidget.see(tk.END)
        self.textwidget.config(state="disabled")

        
    def Addsoundentry(self, prefix, content):
        #get the length of the sound file
        sound = pygame.mixer.Sound(content)
        length = round(sound.get_length())
        #define the message to be addded
        message = f"{prefix} Sound file ({length}s):\n"
        #insert the message into the text widget
        self.textwidget.config(state="normal")
        self.textwidget.insert(tk.END, message)

        #create the play button
        playbutton = ttk.Button(self.textwidget, text="Play", command=lambda: self.Playaudio(content))
        self.textwidget.window_create(tk.END, window=playbutton)
        
        #create the pause button
        pausebutton = ttk.Button(self.textwidget, text="Pause", command=self.Pauseaudio)
        self.textwidget.window_create(tk.END, window=pausebutton)

        #add new line
        self.textwidget.insert(tk.END, "\n")

        self.textwidget.see(tk.END)
        self.textwidget.config(state="disabled")
        
    def Playaudio(self, content):
        #play the audio
        pygame.mixer.music.load(content)
        pygame.mixer.music.play()

    def Pauseaudio(self):
        #pause the audio
        pygame.mixer.music.pause()

try:
    #define the rounded border style
    focusBorderImageData = ''' 
        R0lGODlhQABAAPcAAHx+fMTCxKSipOTi5JSSlNTS1LSytPTy9IyKjMzKzKyq
        rOzq7JyanNza3Ly6vPz6/ISChMTGxKSmpOTm5JSWlNTW1LS2tPT29IyOjMzO
        zKyurOzu7JyenNze3Ly+vPz+/OkAKOUA5IEAEnwAAACuQACUAAFBAAB+AFYd
        QAC0AABBAAB+AIjMAuEEABINAAAAAHMgAQAAAAAAAAAAAKjSxOIEJBIIpQAA
        sRgBMO4AAJAAAHwCAHAAAAUAAJEAAHwAAP+eEP8CZ/8Aif8AAG0BDAUAAJEA
        AHwAAIXYAOfxAIESAHwAAABAMQAbMBZGMAAAIEggJQMAIAAAAAAAfqgaXESI
        5BdBEgB+AGgALGEAABYAAAAAAACsNwAEAAAMLwAAAH61MQBIAABCM8B+AAAU
        AAAAAAAApQAAsf8Brv8AlP8AQf8Afv8AzP8A1P8AQf8AfgAArAAABAAADAAA
        AACQDADjAAASAAAAAACAAADVABZBAAB+ALjMwOIEhxINUAAAANIgAOYAAIEA
        AHwAAGjSAGEEABYIAAAAAEoBB+MAAIEAAHwCACABAJsAAFAAAAAAAGjJAGGL
        AAFBFgB+AGmIAAAQAABHAAB+APQoAOE/ABIAAAAAAADQAADjAAASAAAAAPiF
        APcrABKDAAB8ABgAGO4AAJAAqXwAAHAAAAUAAJEAAHwAAP8AAP8AAP8AAP8A
        AG0pIwW3AJGSAHx8AEocI/QAAICpAHwAAAA0SABk6xaDEgB8AAD//wD//wD/
        /wD//2gAAGEAABYAAAAAAAC0/AHj5AASEgAAAAA01gBkWACDTAB8AFf43PT3
        5IASEnwAAOAYd+PuMBKQTwB8AGgAEGG35RaSEgB8AOj/NOL/ZBL/gwD/fMkc
        q4sA5UGpEn4AAIg02xBk/0eD/358fx/4iADk5QASEgAAAALnHABkAACDqQB8
        AMyINARkZA2DgwB8fBABHL0AAEUAqQAAAIAxKOMAPxIwAAAAAIScAOPxABIS
        AAAAAIIAnQwA/0IAR3cAACwAAAAAQABAAAAI/wA/CBxIsKDBgwgTKlzIsKFD
        gxceNnxAsaLFixgzUrzAsWPFCw8kDgy5EeQDkBxPolypsmXKlx1hXnS48UEH
        CwooMCDAgIJOCjx99gz6k+jQnkWR9lRgYYDJkAk/DlAgIMICZlizat3KtatX
        rAsiCNDgtCJClQkoFMgqsu3ArBkoZDgA8uDJAwk4bGDmtm9BZgcYzK078m4D
        Cgf4+l0skNkGCg3oUhR4d4GCDIoZM2ZWQMECyZQvLMggIbPmzQIyfCZ5YcME
        AwFMn/bLLIKBCRtMHljQQcDV2ZqZTRDQYfWFAwMqUJANvC8zBhUWbDi5YUAB
        Bsybt2VGoUKH3AcmdP+Im127xOcJih+oXsEDdvOLuQfIMGBD9QwBlsOnzcBD
        hfrsuVfefgzJR599A+CnH4Hb9fcfgu29x6BIBgKYYH4DTojQc/5ZGGGGGhpU
        IYIKghgiQRw+GKCEJxZIwXwWlthiQyl6KOCMLsJIIoY4LlQjhDf2mNCI9/Eo
        5IYO2sjikX+9eGCRCzL5V5JALillY07GaOSVb1G5ookzEnlhlFx+8OOXZb6V
        5Y5kcnlmckGmKaaMaZrpJZxWXjnnlmW++WGdZq5ZXQEetKmnlxPgl6eUYhJq
        KKOI0imnoNbF2ScFHQJJwW99TsBAAAVYWEAAHEQAZoi1cQDqAAeEV0EACpT/
        JqcACgRQAW6uNWCbYKcyyEwGDBgQwa2tTlBBAhYIQMFejC5AgQAWJNDABK3y
        loEDEjCgV6/aOcYBAwp4kIF6rVkXgAEc8IQZVifCBRQHGqya23HGIpsTBgSU
        OsFX/PbrVVjpYsCABA4kQCxHu11ogAQUIOAwATpBLDFQFE9sccUYS0wAxD5h
        4DACFEggbAHk3jVBA/gtTIHHEADg8sswxyzzzDQDAAEECGAQsgHiTisZResN
        gLIHBijwLQEYePzx0kw37fTSSjuMr7ZMzfcgYZUZi58DGsTKwbdgayt22GSP
        bXbYY3MggQIaONDzAJ8R9kFlQheQQAAOWGCAARrwdt23Bn8H7vfggBMueOEG
        WOBBAAkU0EB9oBGUdXIFZJBABAEEsPjmmnfO+eeeh/55BBEk0Ph/E8Q9meQq
        bbDABAN00EADFRRQ++2254777rr3jrvjFTTQwQCpz7u6QRut5/oEzA/g/PPQ
        Ry/99NIz//oGrZpUUEAAOw==
    '''
    borderImageData = ''' 
        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
    '''
    #create the main tkinter window
    root = tk.Tk()
    
    #define the border style to be applied to the window
    style = ttk.Style()
    borderimage = tk.PhotoImage("borderImage", data=borderImageData)
    focusborderimage = tk.PhotoImage("focusBorderImage", data=focusBorderImageData)
    style.element_create("RoundedFrame",
                         "image", borderimage,
                         ("focus", focusborderimage),
                         border=16, sticky="nsew")
    style.layout("RoundedFrame",
                 [("RoundedFrame", {"sticky": "nsew"})])
    
    #apply the custom style to the frame
    root.option_add('*TFrame*background', 'white')  
    frame = ttk.Frame(root, style="RoundedFrame", padding=10)
    frame.pack(expand=True, fill=tk.BOTH)    
    
    #create an instance of the MessageLogApp class
    app = MessageLogApp(root)
    #start the tkinter event loop
    root.mainloop()
except Exception as e:
    print("Error occured", e)