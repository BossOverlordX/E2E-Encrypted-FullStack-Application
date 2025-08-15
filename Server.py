# E2E Encrypted Flask Server with Tkinter GUI

#import shutil for deleting directory trees
import shutil
#import sys to open servergui.py as a subprocess
import sys
#import subprocess to run the tkinter file at the same time
import subprocess
#import sqlite3 to use SQL
import sqlite3
#import os to manipulate file paths
import os
#import flask library
from flask import Flask, render_template, request, send_file
#import datetime for timestamps
import datetime
#import wave (used for audio file steganography)
import wave
#import PIL (Pillow) library for image processing (used for image file steganography)
from PIL import Image
#import cryptography modules for asymmetric encryption
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding
#import base64 to be used when decrypting transmitted data
import base64

#function to do steganography on the given file using the given message
def Steganography(filepath, message):
    #convert the message to binary so that it can be hidden
    binarymessage = ''.join(format(ord(char), '08b') for char in message)
    #if file is an image
    if filepath[-3:].lower() == "png":
        try:
            #open the image file
            image = Image.open(filepath)
            
            #assign the tuple returned by image.size to the variables width and height respectively
            width, height = image.size
            
            #check length of message isn't longer than can possibly be embedded
            if len(binarymessage) > width * height:
                print("Error occured during steganography: Message length exceeded maximum size")
                return
            
            #embed the length of the message into the first pixel's red and green channels
            #putpixel allows us to set the colour of a specific pixel (0,0 being the first pixel)
            #seperates the higher 8 bits into the red channel, lower 8 bits into the green channel and keeps the blue channel the same
            image.putpixel((0,0), (len(binarymessage) >> 8, len(binarymessage) & 0xFF, image.getpixel((0,0))[2]))
            #iterate through all the pixels and embed the message starting from pixel 2
            pixelindex = 1
            messageindex = 0
            #while there are still characters to be embedded
            while messageindex < len(binarymessage):
                #retrieve the RGB values of the current pixel being worked with
                #the coordinate is found using MOD to find the width and DIV to find the height
                pixel = list(image.getpixel((pixelindex % width, pixelindex // width)))
                #modify the least significant bit of each colour channel with the current message index (3 times because RGB is 3 colour channels)
                for i in range(0,3):
                    #if there are still characters to be embedded
                    if messageindex < len(binarymessage):
                        #replace the current pixel's colour channel (red green or blue) by clearing the LSB of the current channel and replacing it with the LSB of the message character
                        pixel[i] = (pixel[i] & 0xFE) | (int(binarymessage[messageindex]) & 1)
                        messageindex += 1
                #replace the pixel being worked with with the new pixel defined by the list
                image.putpixel((pixelindex % width, pixelindex // width), tuple(pixel))
                pixelindex += 1
            
            #save the new image and replace the old one
            image.save(filepath)
            print("Steganography successful")
        except Exception as e:
            print("Error occured during steganography:", str(e))
    #if file is a sound file
    else:
        try:
            #open the WAV audio file
            waveaudio = wave.open(filepath, mode="rb")
            #read all the frames in the audio file and convert it into a byte list
            framebytes = bytearray(list(waveaudio.readframes(waveaudio.getnframes())))
    
            #check length of message isnt longer than can possibly be embedded
            if len(binarymessage) + 8 > len(framebytes):
                print("Error occured during steganography: Message length exceeded maximum size")
    
            #calculate the number of bits needed to represent the length of the secret message
            messagelength = len(message)
            #convert the length of the message to binary
            messagelength = bin(messagelength)[2:].rjust(8, "0")
    
            #embed the message length in the audio file
            for i, bit in enumerate(messagelength):
                framebytes[i] = (framebytes[i] & 254) | int(bit)
    
            #embed the secret message by converting it into binary
            bits = list(map(int, "".join([bin(ord(char))[2:].rjust(8, "0") for char in message])))
            for i, bit in enumerate(bits):
                #embed the current bit in the LSB
                framebytes[i + 8] = (framebytes[i + 8] & 254) | bit
    
            #create a new modified frame with the secret message embedded
            frame_modified = bytes(framebytes)
    
            #write the new WAV file over the old one
            with wave.open(filepath, "wb") as f:
                f.setparams(waveaudio.getparams())
                f.writeframes(frame_modified)
            waveaudio.close()
            print("Steganography successful")
        except Exception as e:
            print("Error occured during steganography:", str(e))
    
    
def Revsteganography(filepath):
    #if file is an image
    if filepath[-3:] == "png":
        try:
            #open the image file
            image = Image.open(filepath)
            
            #assign the tuple returned by image.size to the variables width and height respectively
            width, height = image.size
            
            #get the length of the message from the first pixel's red and green channels
            messagelength = (image.getpixel((0,0))[0] << 8) + image.getpixel((0,0))[1]
            
            binarymessage = ""
            #iterate through all the pixels starting from pixel 2 decoding the message until reaching messagelength
            pixelindex = 1
            while len(binarymessage) < messagelength:
                #get currennt pixel RGB values
                pixel = image.getpixel((pixelindex % width, pixelindex // width))

                #extract the least significant bit from each colour channel
                for i in range(0,3):
                    #append each LSB to the binary message
                    binarymessage += str(pixel[i] & 1)

                pixelindex += 1
            
            #convert the message from binary to a string
            secretmessage = ""
            #loop through the binary message in increments of 8
            for i in range(0, len(binarymessage), 8):
                #create byte variable which defines the current 8 bits of binary to be converted to a character
                byte = binarymessage[i:i+8]
                #convert the 8-bit binary value into a character and add to the message
                secretmessage += chr(int(byte, 2))
            return(secretmessage)
        
        except Exception as e:
            print("Error occured during reverse steganography:", str(e))
    #if file is a sound file
    else:
        try:
            #open the WAV audio file
            waveaudio = wave.open(filepath, mode="rb")
            #read all the frames in the audio file and convert it into a byte list
            framebytes = bytearray(list(waveaudio.readframes(waveaudio.getnframes())))

            #extract the embedded message length
            messagelength = [str(framebytes[i] & 1) for i in range(8)]
            #convert the value from binary to an integer
            messagelength = int("".join(messagelength), 2)
    
            #extract the secret message by iterating through framebytes and extracting the LSB of each byte and storing it in textbits
            textbits = [str(framebytes[i] & 1) for i in range(8, len(framebytes))]
            textbits = textbits[:messagelength * 8]
            #group the binary into 8-bit segments and convert each segment to a character
            text = [chr(int("".join(textbits[i:i+8]), 2)) for i in range(0, len(textbits), 8)]
            #join the characters together to form the whole message
            secretmessage = ''.join(text)
            waveaudio.close()
            return(secretmessage)
        except Exception as e:
            print("Error occured during reverse steganography:", str(e))

def Updatelog(userid, content, timetolive, datatype, timestamp):
    try:
        #open a connection to the database
        conn = sqlite3.connect("Server.db")
        #define cursor (will be used to execute SQL commands)
        cursor = conn.cursor()
        #command to update table
        insertrow = "INSERT INTO messagelog (userid, content, timetolive, datatype, timestamp) VALUES (?, ?, ?, ?, ?)"
        #execute the command
        cursor.execute(insertrow, (userid, content, timetolive, datatype, timestamp))
        #save changes and close the database
        conn.commit()
        conn.close()
        #now update what is shown on the server-side gui returning whether it is successfully inserted (true/false)
        return(True)
    except Exception as e:
        print("error:", e)
        return(False)

#generate a private key before the server is started using RSA with a key size of 2048 bits
privatekey = rsa.generate_private_key(
    public_exponent = 65537, #common value for the public exponent
    key_size = 4096
)
    
#serialise the private key to a PEM format as it is more portable and not encrypted    
privatepem = privatekey.private_bytes(
    encoding = serialization.Encoding.PEM, #format as PEM
    format = serialization.PrivateFormat.PKCS8, #PKCS8 format
    encryption_algorithm = serialization.NoEncryption() #No encryption
)

#create public key
publickey = privatekey.public_key()

#serialize the public key to a PEM format, this will be sent to the client on the webpage and is already created as not encrypted
publicpem = publickey.public_bytes(
    encoding = serialization.Encoding.PEM, #format as PEM
    format = serialization.PublicFormat.SubjectPublicKeyInfo #SubjectPublicKeyInfo format
)

#write the private key to a file to be used for decryption
f = open("privatekey.pem", "wb")
f.write(privatepem)
#write public key to a file to be sent to the clients
f = open("publickey.pem", "wb")
f.write(publicpem)
f.close()

#open a connection to the database
conn = sqlite3.connect("Server.db")
#define cursor (will be used to execute SQL commands)
cursor = conn.cursor()
#delete the table from the last session if there is one
cursor.execute("DROP TABLE IF EXISTS messagelog")
#define the command to be executed
createtable = """
CREATE TABLE messagelog (
    userid,
    content TEXT,
    timetolive INTEGER,
    datatype TEXT,
    timestamp TIMESTAMP
    )
"""
#execute the command
cursor.execute(createtable)
#save changes and close the database
conn.commit()
conn.close()


#refresh the uploads folder by deleting it and recreating it
folder = "uploads"
if os.path.exists(folder):
    shutil.rmtree(folder)
os.makedirs(folder)
#make timetolivetracker file in uploads folder
filepath = os.path.join(folder, "timetolivetracker.txt")
f = open(filepath, "w")
f.close()

#run the tkinter file
proc = subprocess.Popen([sys.executable, "Servergui.py"])

app = Flask(__name__)

#create new route
#this route will be for the root of the website
@app.route("/")
#name the route in the function
def Index():
    #contents of the webpage
    return render_template("index.html")

#add a new route to be used for steganography, the webpage will submit a POST request here
@app.route("/steganography", methods=["POST"])
def Stegendpoint():
    #define the filepath
    filepath = request.files["filepath"].filename
    #get the uploaded file as 'file'
    file = request.files["filepath"]
    #define folder for steganography file to be temporarily saved to
    uploadfolder = "uploads"
    #temporarily save the file
    filename = os.path.join(uploadfolder, "tempsteg" + filepath[-4:])
    file.save(filename)
    #defines the message as the message included in the request
    message = request.form["message"]
    #calls the steganography function to add the message to the file and this will save the file at the location 'filename'
    Steganography(filename, message)
    #return the file back to the webpage as an attachment
    return send_file(filename, as_attachment=True)

#add a new route for requests when the webpage is ready to send data which will request the public key
@app.route("/ready", methods=["GET"])
def Sendpem():
    #return response as PEM file using the correct mimetype as it allows the browser to interpret the file correctly
    return send_file("publickey.pem", mimetype="application/x-pem-file")

#add a new route for data to be sent to
@app.route("/send", methods=["POST"])
def Receivedata():
    try:        
        #get the current time and put it in the correct syntax for the TIMESTAMP datatype used in SQL
        timestamp = str(datetime.datetime.now())[:19]
        
        #load the private key
        f = open("privatekey.pem", "rb")
        privatekey = serialization.load_pem_private_key(f.read(), password=None)
        
        #get encrypteddata from the formdata object and decode from base64
        encryptedtextdata = request.form.get("encryptedtextdata")
        ciphertext = base64.b64decode(encryptedtextdata)
        
        #decrypt the text data with the private key
        textdata = privatekey.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
        #convert it back to a string
        textdata = textdata.decode("utf-8")
        #split the text data into its two sections (timetolive and userid)
        textdata = textdata.split("%")
        #if file has had steganography done to it
        steg = False
        if len(textdata) == 3:
            steg = True
            #get the steganography file extension
            extension = textdata[2]
        #define important variables
        timetolive = textdata[0]
        userid = textdata[1]
        
        #if a file was included in the request
        if "encryptedfile" in request.form:
            #get encryptedfile, encryptedsymmetrickey, and iv from the formdata object
            encryptedfile = request.form["encryptedfile"]
            encryptedsymmetrickey = request.form["encryptedsymmetrickey"]
            iv = request.form["iv"]
            
            #decode the encrypted symmetric key
            encryptedsymmetrickey = base64.b64decode(encryptedsymmetrickey)
            
            #decrypt the encrypted symmetric key with the private key
            symmetrickey = privatekey.decrypt(
                encryptedsymmetrickey,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )

            #convert the initialisation vector into the correct form for decryption
            iv = ''.join([f'\\x{ord(char):02x}' for char in iv])
            iv = iv.replace("\\x", "")
            iv = bytes.fromhex((iv))
            
            #decode the symmetric key and iv from base64
            symmetrickey = base64.b64encode(symmetrickey)
            iv = base64.b64encode(iv)
            #turn the symmetric key and iv from bytes objects to strings so that they can be parsed to the javascript file
            symmetrickey = symmetrickey.decode("utf-8")
            iv = iv.decode("utf-8")
            
            #write the encrypted file data to a text file so that it can be accessed by the javascript file
            f = open("temp.txt", "w")
            f.write(encryptedfile)
            f.close()

            #define the environment, file, and variables to be used/parsed
            command = ["node", "decryption.js", symmetrickey, iv]
            #run decryption.js as a subprocess
            result = subprocess.run(command, capture_output=True, text=True)
            #capture the output
            success = result.stdout

            #if the decryption process was unsuccessful
            if not success:
                print("Decryption failed")
                result = {"status": "error", "data": "File failed to be decrypted. Ensure no file corruption and try again."}
                return(result)
            
            #open the text file that the decrypted data was written to
            f = open("temp2.txt", "r")
            decrypteddata = f.read()
            f.close()
            
            #decode the decrypted data from base64
            decrypteddata = base64.b64decode(decrypteddata)
            
            #if the file had steganography done to it
            if steg == True:
                filepath = userid + "stegfile." + extension
                #write the decrypted data to the filepath
                f = open(filepath, "wb")
                f.write(decrypteddata)
                f.close()
                #call the reverse steganography function and store the resulting message in content
                content = Revsteganography(filepath)
                #remove any accidental control characters that may have appended to the end
                if content and ord(content[-1]) < 32:
                    content = content.rstrip(content[-1])
                content = "(From Steg): " + content
                #delete the steganography file once it is no longer needed
                os.remove(filepath)
                datatype = "text"
            else:
                #check file signature to determine its filetype
                if decrypteddata.startswith(b"RIFF"):
                    datatype = "wav"
                elif decrypteddata.startswith(b"\x89PNG\r\n\x1a\n"):
                    datatype = "png"
                else:
                    result = {"status": "error", "data": "File signature did not match PNG or WAV. Ensure no file corruption and try again."}
                    return("File signature was not present/did not match a supported file type")
                #define the name for the file to be stored under (using the current time to make it unique)
                filepath = os.path.join("uploads", timestamp[-8:].replace(":", "") + userid + "file." + datatype)
                content = filepath
                
                #save the decrypted file
                f = open(filepath, "wb")
                f.write(decrypteddata)
                f.close()
            
        #else no file and only a message was included
        else:
            #get the encrypted message from the formdata object
            encryptedmessage = request.form.get("encryptedmessage")
            
            #decode the encrypted message from base64
            ciphertext = base64.b64decode(encryptedmessage)
            
            #decrypt the message with the private key
            message = privatekey.decrypt(
                ciphertext,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None
                )
            )
            
            #convert it back to a string
            content = message.decode("utf-8")
            datatype = "text"

        #send the required values to the Updatelog function for them to be added to the database
        success = Updatelog(userid, content, timetolive, datatype, timestamp)
        #if the data was added and displayed successfully
        if success:
            result = {"status": "ok", "data": "Successfully sent!"}
            return(result)
        else:
            result = {"status": "result", "data": "Data failed to display. Ensure no file corruption and try again"}
            return(result)
    #if any uncaught errors occured while processing the received data
    except Exception as e:
        print(f"Error occurred: {str(e)}")
        #return code 500 (internal server error) to the client
        return("Internal Server Error", 500)


if __name__ == "__main__":
    #run the webserver and make it available to any device on the network
    app.run(debug=True, host="0.0.0.0")