// import forge for decryption and general utilities
const forge = require('./node_modules/node-forge')
// import fs for file management
const fs = require('fs')

// get arguments from python file
args = process.argv

// define constants
arg2 = args[2]
arg3 = args[3]

// convert base64 encoded strings into their binary data
symmetrickey = atob(arg2)
iv = atob(arg3)

// async function to return the contents of a file, read as text
function ReturnFileContents(filepath, callback) {
	fs.readFile(filepath, 'utf-8', (err, data) => {
	if (err) {
	  throw err
	}
	callback(data)
	})
}

// async function to write data to a file
function WriteToFile(filepath, data, callback) {
    // write the data to the specified file
    fs.writeFile(filepath, data, (err) => {
      if (err) {
        throw err
      }
      callback(true)
    })
}

const filepath = "temp.txt"
// read the contents of the encryptedfile
ReturnFileContents(filepath, (encryptedfiledata) => {
    // convert the encryptedfile's contents to its binary form
    encryptedfile = atob(encryptedfiledata)
	
	// create a decipher object using the same algorithm used during encryption
	decipher = forge.cipher.createDecipher('AES-CBC', symmetrickey)

    // specify the initialisation vector and complete the encryption process
	decipher.start({ iv: iv })
	decipher.update(forge.util.createBuffer(encryptedfile, 'raw'))
	decipher.finish()

    // get the decrypted binary data
	decryptedfile = decipher.output.getBytes()

    // remove the unnecessary information at the start of the data which specifies data type etc.
	decryptedfilesplit = decryptedfile.indexOf(',')
	decryptedfiledata = decryptedfile.substring(decryptedfilesplit + 1)

	const outputfilepath = "temp2.txt"
	// write the decrypted data to the output file
    WriteToFile(outputfilepath, decryptedfiledata, (success) => {
        // return whether the process was successful or not
        if(success == true) {
            console.log("Success!")
        }
        else {
            console.log("Fail!")
        }
    })
})