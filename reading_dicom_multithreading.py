# -*- coding: utf-8 -*-
"""
Created on Fri Jun 16 15:43:51 2017

@author: bsilski
"""

# -*- coding: utf-8 -*-
"""
Created on Wed Jun 14 11:28:07 2017

@author: bsilski
"""

import sys
from PyQt5 import QtGui, QtWidgets, QtCore

class DicomConverterMain(QtWidgets.QMainWindow):
    
    def __init__(self,*args,**kwargs):
        
        self.folderPath = ""
        self.noDICOMS = 0
        self.pictureFormat = ""
        self.dicoms = []
        
        self.textBrowser = QtWidgets.QTextBrowser();
        
        super(DicomConverterMain, self).__init__()
        self.setGeometry(300,300,900,300)
        self.setWindowTitle("Dicom Converter")
        self.home()
    
    def home(self):
        
        self.toolbar = self.addToolBar("Extraction")
        
        extractAction1 = QtWidgets.QAction("Add path to DICOM files folder",self)
        extractAction1.triggered.connect(self.setFolderPath)
        self.toolbar.addAction(extractAction1)
        
        extractAction2 = QtWidgets.QAction("Convert DICOMs",self)
        
        extractAction2.triggered.connect(self.startThread)

        self.toolbar.addAction(extractAction2)
        
        extractAction3 = QtWidgets.QAction("Clear log and data",self)
        extractAction3.triggered.connect(self.clearLog)
        self.toolbar.addAction(extractAction3)
        
        extractAction4 = QtWidgets.QAction("Quit",self)
        extractAction4.triggered.connect(self.close_app)
        self.toolbar.addAction(extractAction4)
        
        self.toolbar.addSeparator()
               
        comboBox = QtWidgets.QComboBox(self)
        comboBox.addItem("Choose picture format")
        comboBox.addItem("JPG")
        comboBox.addItem("PNG")
        comboBox.activated[str].connect(self.setFormat)
        self.toolbar.addWidget(comboBox)
        
        self.setCentralWidget(self.textBrowser)

        self.show()
        
    def close_app(self):
        sys.exit()
        
    def setFormat(self,text):
        self.pictureFormat = text

    def clearLog(self):
        self.folderPath = ""
        self.noDICOMS = 0
        self.pictureFormat = ""
        self.dicoms = []
        self.textBrowser.clear()
    
    def setFolderPath(self,folderPath):
        
        self.textBrowser.clear()
        
        self.folderPath = str(QtWidgets.QFileDialog.getExistingDirectory(
                self, 
                "Select Directory",
                "C:/",
                QtWidgets.QFileDialog.ShowDirsOnly
                ))
        
        loginfo = "Folder " + self.folderPath
        self.textBrowser.append(loginfo)
                
        self.dicoms = self.find_dicoms(self.folderPath)
        
       
        if (len(self.dicoms)) == 0:
            self.textBrowser.append("No DICOM files found in this folder. If you are sure DICOM files are in this folder maybe this particular format is not supported. Please contact developer.")
        else:
            self.noDICOMS = len(self.dicoms)
            loginfo = "Number of DICOM files found " + str(len(self.dicoms)) + ". Click convert button to convert files."
            self.textBrowser.append(loginfo)
            
            
    def startThread(self):
        self.get_thread = convertThread(self.dicoms,self.noDICOMS,self.pictureFormat, self.textBrowser)
        self.get_thread.start()
    
    def getFolderPath(self):
        return self.folderPath
      
    def find_dicoms(self, path):
        
        import binascii
        import os
        
        folder_contents = os.listdir(path)
        
        if path[-1] == "/":
            path = path[0:len(path)-1]
        
        dicom_files = []
        
        for i in range(len(folder_contents)):
           full_path = path + "/" + folder_contents[i]
           
           if (os.path.isfile(full_path)):
        
                w = open(full_path,"rb")
                data = w.read()
                w.close()
                
                if (b'DICM' in binascii.rlecode_hqx(data[0:1000])):
                    dicom_files.append(full_path)
        
        return dicom_files
    
        
from PyQt5.QtCore import QThread
class convertThread(QtCore.QThread):
    
    def __init__(self, dicom_files, noDICOMS, pictureFormat, textBrowser):
        print("inits")
        QThread.__init__(self)
        self.dicom_files = dicom_files
        self.noDICOMS = noDICOMS
        self.pictureFormat = pictureFormat
        self.textBrowser = textBrowser
        

    def __del__(self):
        self.wait()
        

    def start(self):

        if self.noDICOMS == 0:
            loginfo = "Choose DICOM data first."
            self.textBrowser.append(loginfo)
            return               
        
        if self.pictureFormat not in ["JPG","PNG"]:
            loginfo = "Choose picture format first."
            self.textBrowser.append(loginfo)
            return        
    
        self.textBrowser.clear()
        self.textBrowser.append("Processing...")

        for i in range(len(self.dicom_files)):
            self.convert(self.dicom_files[i])


    def convert(self, full_path):
                
        import numpy as np
        from cv2 import normalize, NORM_MINMAX, CV_32F
        import binascii
        
        loginfo = full_path
        
        w = open(full_path,"rb")
        data = w.read()
        w.close()
        
        header = data[0:20000]
        header_to_hex = binascii.b2a_hex(header)
        rows_tag_pos = header_to_hex.find(b'28001000')
        cols_tag_pos = header_to_hex.find(b'28001100')
        bits_allocated_tag_pos = header_to_hex.find(b'28000001')
        bits_stored_tag_pos = header_to_hex.find(b'28000101')
        
        if rows_tag_pos<-1:
            loginfo = loginfo + " ERROR: Can't find image size tags."
            self.textBrowser.append(loginfo)
            return
        
        rows_tag_bytes = header_to_hex[rows_tag_pos+8:rows_tag_pos+20]
        cols_tag_bytes = header_to_hex[cols_tag_pos+8:cols_tag_pos+20]
        bits_allocated_tag_bytes = header_to_hex[bits_allocated_tag_pos+8:bits_allocated_tag_pos+20]
        bits_stored_tag_bytes = header_to_hex[bits_stored_tag_pos+8:bits_stored_tag_pos+20]
        
        rows_unhex = binascii.unhexlify(rows_tag_bytes)
        cols_unhex = binascii.unhexlify(cols_tag_bytes)
        bits_allocated_unhex = binascii.unhexlify(bits_allocated_tag_bytes)
        bits_stored_unhex = binascii.unhexlify(bits_stored_tag_bytes)
        
        rows = np.frombuffer(rows_unhex,np.uint16)[2]
        cols = np.frombuffer(cols_unhex,np.uint16)[2]
        bits_allocated = np.frombuffer(bits_allocated_unhex,np.uint16)[2]
        bits_stored = np.frombuffer(bits_stored_unhex,np.uint16)[2]

        rows = int(rows)
        cols = int(cols)
        bits_allocated = int(bits_allocated)
        bits_stored = int(bits_stored)
        
        loginfo = loginfo + " Image size: " + str(rows) + "x" + str(cols)
        image_data = data[len(data)-rows*cols*2:len(data)]
            
        if bits_allocated != 16:
            loginfo = loginfo + " ERROR: Image is " + str(bits_allocated) + " bit. Currently app supports only 16 bit images."
            self.textBrowser.append(loginfo)
            return
            
        image_data_numpy = np.fromstring(image_data,np.uint16)
        image_data_reshaped = image_data_numpy.reshape((rows,cols))
                
        copy = image_data_reshaped
        
        norm_image = normalize(image_data_reshaped, copy, alpha=0, beta=1, norm_type=NORM_MINMAX, dtype=CV_32F)
        
        
        import scipy.misc
        if self.pictureFormat == "JPG":
            scipy.misc.imsave(full_path + ".jpg", norm_image)
        if self.pictureFormat == "PNG":
            scipy.misc.imsave(full_path + ".png", norm_image)
            
        self.textBrowser.append(loginfo)
        
        


def run():  
    if QtWidgets.QApplication.instance():
        app = QtWidgets.QApplication.instance()
    else:
        app = QtWidgets.QApplication(sys.argv)
    GUI = DicomConverterMain()
    sys.exit(app.exec_())
            

run()