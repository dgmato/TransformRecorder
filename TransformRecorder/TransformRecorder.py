import os
import unittest
import vtk, qt, ctk, slicer
from slicer.ScriptedLoadableModule import *
import logging
import time
import numpy
import csv

#
# TransformRecorder
#

class TransformRecorder(ScriptedLoadableModule):
  """Uses ScriptedLoadableModule base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def __init__(self, parent):
    ScriptedLoadableModule.__init__(self, parent)
    self.parent.title = "Transform Recorder" # TODO make this more human readable by adding spaces
    self.parent.categories = ["Tracking"]
    self.parent.dependencies = []
    self.parent.contributors = ["David Garcia-Mato (UC3M)"] # replace with "Firstname Lastname (Organization)"
    self.parent.helpText = """
    This module records transformation nodes into .mha sequence metafiles for simulations without trackers.
    """
    self.parent.acknowledgementText = """
    This file was originally developed by David Garcia-Mato (UC3M).
    """ # replace with organization, grant and thanks.

#
# TransformRecorderWidget
#

class TransformRecorderWidget(ScriptedLoadableModuleWidget):
  
  def setup(self):
    ScriptedLoadableModuleWidget.setup(self)

    # Instantiate and connect widgets ...

    self.logic = TransformRecorderLogic()

    # Defining style sheets for GUI buttons
    self.defaultStyleSheet = "QLabel { color : #000000; \
                                       font: bold 14px}"
    
    #
    # Select Transformation Area
    #
    transformCollapsibleButton = ctk.ctkCollapsibleButton()
    transformCollapsibleButton.text = "TRANFORM SELECTION"
    self.layout.addWidget(transformCollapsibleButton)
    transformFormLayout = qt.QFormLayout(transformCollapsibleButton)

    # Active Transform selector
    self.firstTransformSelector = slicer.qMRMLNodeComboBox()
    self.firstTransformSelector.nodeTypes = ( ("vtkMRMLLinearTransformNode"), "" )
    self.firstTransformSelector.selectNodeUponCreation = True
    self.firstTransformSelector.removeEnabled = False
    self.firstTransformSelector.noneEnabled = True
    self.firstTransformSelector.showHidden = False
    self.firstTransformSelector.showChildNodeTypes = False
    self.firstTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.firstTransformSelector.setToolTip( "Pick the transform node to be updated." )
    transformFormLayout.addRow("Transform 1: ", self.firstTransformSelector)

    # Active Transform selector
    self.secondTransformSelector = slicer.qMRMLNodeComboBox()
    self.secondTransformSelector.nodeTypes = ( ("vtkMRMLLinearTransformNode"), "" )
    self.secondTransformSelector.selectNodeUponCreation = True
    self.secondTransformSelector.removeEnabled = False
    self.secondTransformSelector.noneEnabled = True
    self.secondTransformSelector.showHidden = False
    self.secondTransformSelector.showChildNodeTypes = False
    self.secondTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.secondTransformSelector.setToolTip( "Pick the transform node to be updated." )
    transformFormLayout.addRow("Transform 2: ", self.secondTransformSelector)

    # Active Transform selector
    self.thirdTransformSelector = slicer.qMRMLNodeComboBox()
    self.thirdTransformSelector.nodeTypes = ( ("vtkMRMLLinearTransformNode"), "" )
    self.thirdTransformSelector.selectNodeUponCreation = True
    self.thirdTransformSelector.removeEnabled = False
    self.thirdTransformSelector.noneEnabled = True
    self.thirdTransformSelector.showHidden = False
    self.thirdTransformSelector.showChildNodeTypes = False
    self.thirdTransformSelector.setMRMLScene( slicer.mrmlScene )
    self.thirdTransformSelector.setToolTip( "Pick the transform node to be updated." )
    transformFormLayout.addRow("Transform 3: ", self.thirdTransformSelector)

    #
    # Recording Area
    #
    recordingCollapsibleButton = ctk.ctkCollapsibleButton()
    recordingCollapsibleButton.text = "RECORDING"
    self.layout.addWidget(recordingCollapsibleButton)
    recordingFormLayout = qt.QFormLayout(recordingCollapsibleButton)

    # Record Button
    self.recordButton = qt.QPushButton("RECORD")
    self.recordButton.toolTip = "Run the algorithm."
    self.recordButton.setMinimumWidth(200)
    self.recordButton.setMinimumHeight(30)
    self.recordButton.enabled = True
    
    # Stop Button
    self.stopButton = qt.QPushButton("STOP")
    self.stopButton.toolTip = "Run the algorithm."
    self.stopButton.setMinimumHeight(30)
    self.stopButton.enabled = False
    recordingFormLayout.addRow(self.recordButton, self.stopButton)

    self.recordingStatusTextLabel = qt.QLabel(' - ')
    self.recordingStatusTextLabel.setStyleSheet(self.defaultStyleSheet)
    recordingFormLayout.addRow('Status: ', self.recordingStatusTextLabel)  

    #
    # Record Data Stream To MHA File Button
    #
    self.recordDataStreamToMhaFileCheckBox = qt.QCheckBox('Record Data Stream to .mha file')
    self.recordDataStreamToMhaFileCheckBox.checked = False
    self.recordDataStreamToMhaFileCheckBox.enabled = True
    recordingFormLayout.addRow(self.recordDataStreamToMhaFileCheckBox) 

    # connections
    self.firstTransformSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onFirstTransform)
    self.secondTransformSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onSecondTransform)
    self.thirdTransformSelector.connect('currentNodeChanged(vtkMRMLNode*)', self.onThirdTransform)
    self.recordButton.connect('clicked(bool)', self.onRecord)
    self.stopButton.connect('clicked(bool)', self.onStop)
    self.recordDataStreamToMhaFileCheckBox.connect('stateChanged(int)', self.onRecordDataStreamToMhaFileChecked)
    
    # Add vertical spacer
    self.layout.addStretch(1)

  def onFirstTransform(self):

    self.logic.setFirstTransform(self.firstTransformSelector.currentNode())  


  def onSecondTransform(self):

    self.logic.setSecondTransform(self.secondTransformSelector.currentNode())  


  def onThirdTransform(self):

    self.logic.setThirdTransform(self.thirdTransformSelector.currentNode())  
      

  def onRecord(self):
    
    # Determine active transform 
    if self.logic.firstTransform is not None:
      self.logic.activeTransform = self.logic.firstTransform
    elif self.logic.secondTransform is not None:
      self.logic.activeTransform = self.logic.secondTransform
    elif self.logic.thirdTransform is not None:
      self.logic.activeTransform = self.logic.thirdTransform
    else: 
      self.logic.activeTransform = None

    # Add observer
    if self.logic.activeTransform is not None:
      self.logic.addUpdateObserver(self.logic.activeTransform)
      self.recordingStatusTextLabel.setText('Recording...')

      # Update Buttons
      self.recordButton.enabled = False
      self.stopButton.enabled = True
      self.firstTransformSelector.enabled = False
      self.secondTransformSelector.enabled = False
      self.thirdTransformSelector.enabled = False

    else:
      self.recordingStatusTextLabel.setText('Failed. No active transform has been selected.')
   
  
  def onStop(self):
    
    # Remove Observer
    self.logic.removeUpdateObserver()

    # Update Buttons
    self.stopButton.enabled = False
    self.recordButton.enabled = True
    self.recordingStatusTextLabel.setText('Recording finished.')
    self.firstTransformSelector.enabled = True
    self.secondTransformSelector.enabled = True
    self.thirdTransformSelector.enabled = True

    # Save Data Stream to File
    if self.logic.recordToMhaFile_flag:
      self.logic.saveDataStreamToMhaFile()
      print("Data Saved to Mha File")
    
    # Reset Variables
    self.logic.resetScene()
    

  def onRecordDataStreamToMhaFileChecked(self, checked):

    if checked:      
      self.logic.recordToMhaFile_flag = True
    else:      
      self.logic.recordToMhaFile_flag = False
  
  
# TransformRecorderLogic
#

class TransformRecorderLogic(ScriptedLoadableModuleLogic):
  """
  """

  def __init__(self): 

    self.activeTransform = None
    self.observedNode = None
    self.outputObserverTag = -1
    self.matrix = vtk.vtkMatrix4x4() # 4x4 VTK matrix to save the transformation matrix sent through Plus.
    
    # Timer
    self.myTimer = Timer()
    self.timerActive = False

    # Recording Data Stream To File/table
    self.recordToCsvFile_flag = False
    self.timeStamp = list()
    self.firstTransform_matrices = list()
    self.secondTransform_matrices = list()
    self.thirdTransform_matrices = list()
    self.transform=numpy.zeros((4,4), dtype=numpy.float64) # Numpy matrix used as input for the transformation decomposition.
        
    # Active transform matrices
    self.firstTransform = None
    self.secondTransform = None
    self.thirdTransform = None
    self.firstTransform_name = ' '
    self.secondTransform_name = ' '
    self.thirdTransform_name = ' '


  def resetScene(self):

    self.activeTransform = None
    self.observedNode = None
    self.outputObserverTag = -1
    self.matrix = vtk.vtkMatrix4x4() # 4x4 VTK matrix to save the transformation matrix sent through Plus.
    
    # Timer
    self.myTimer.resetTimer()
    self.timerActive = False

    # Recording Data Stream To File/table
    self.timeStamp = list()
    self.gazePosition3D = list()
    self.gazePosition2D = list()
    self.gazeDirection = list()
    self.markerID = list()
    self.counterMarkers = -1
    self.currentMarker = -1
          

  def setFirstTransform(self, firstTransform):
    self.firstTransform = firstTransform
    self.firstTransform_name = firstTransform.GetName()
  

  def setSecondTransform(self, secondTransform):
    self.secondTransform = secondTransform
    self.secondTransform_name = secondTransform.GetName()
   

  def setThirdTransform(self, thirdTransform):
    self.thirdTransform = thirdTransform
    self.thirdTransform_name = thirdTransform.GetName()
  

  def addUpdateObserver(self, inputNode):
    """
    Summary: Add update observer to inputNode.
    """
    print('adding observer')
    self.observedNode = inputNode
    if self.outputObserverTag == -1:
      self.outputObserverTag = inputNode.AddObserver(slicer.vtkMRMLTransformableNode.TransformModifiedEvent, self.updateSceneCallback)


  def removeUpdateObserver(self):
    """
    Summary: Remove update observer.
    """
    print('removing observer')
    if self.outputObserverTag != -1:
      self.observedNode.RemoveObserver(self.outputObserverTag)
      self.outputObserverTag = -1
      self.observedNode = None

    if self.timerActive == True:
      self.myTimer.stopTimer()


  def updateSceneCallback(self, modifiedNode, event=None): 
    """
    Summary: This functions is called when the observed node (to which an observer has been added) is modified.
    """           
    if self.timerActive == False:
      self.myTimer.startTimer()
      self.timerActive=True

    if self.recordToMhaFile_flag:
      self.storeData()


  def storeData(self):

    # Store time stamp
    t = self.myTimer.getElapsedTime()
    self.timeStamp.append(t)

    ############## First #############
    if self.firstTransform is not None:

      # Store translation info of transformation matrix
      self.firstTransform.GetMatrixTransformToParent(self.matrix)
      self.transform[0,0] = self.matrix.GetElement(0, 0)
      self.transform[0,1] = self.matrix.GetElement(0, 1)
      self.transform[0,2] = self.matrix.GetElement(0, 2) 
      self.transform[0,3] = self.matrix.GetElement(0, 3) 
      self.transform[1,0] = self.matrix.GetElement(1, 0)
      self.transform[1,1] = self.matrix.GetElement(1, 1) 
      self.transform[1,2] = self.matrix.GetElement(1, 2)
      self.transform[1,3] = self.matrix.GetElement(1, 3)
      self.transform[2,0] = self.matrix.GetElement(2, 0)  
      self.transform[2,1] = self.matrix.GetElement(2, 1)
      self.transform[2,2] = self.matrix.GetElement(2, 2)
      self.transform[2,3] = self.matrix.GetElement(2, 3)
      self.transform[3,0] = self.matrix.GetElement(3, 0)  
      self.transform[3,1] = self.matrix.GetElement(3, 1)
      self.transform[3,2] = self.matrix.GetElement(3, 2)
      self.transform[3,3] = self.matrix.GetElement(3, 3)
      self.firstTransform_matrices.append(self.transform.copy()) 

    ############## Second #############
    if self.secondTransform is not None:

      self.secondTransform.GetMatrixTransformToParent(self.matrix)
      self.transform[0,0] = self.matrix.GetElement(0, 0)
      self.transform[0,1] = self.matrix.GetElement(0, 1)
      self.transform[0,2] = self.matrix.GetElement(0, 2) 
      self.transform[0,3] = self.matrix.GetElement(0, 3) 
      self.transform[1,0] = self.matrix.GetElement(1, 0)
      self.transform[1,1] = self.matrix.GetElement(1, 1) 
      self.transform[1,2] = self.matrix.GetElement(1, 2)
      self.transform[1,3] = self.matrix.GetElement(1, 3)
      self.transform[2,0] = self.matrix.GetElement(2, 0)  
      self.transform[2,1] = self.matrix.GetElement(2, 1)
      self.transform[2,2] = self.matrix.GetElement(2, 2)
      self.transform[2,3] = self.matrix.GetElement(2, 3)
      self.transform[3,0] = self.matrix.GetElement(3, 0)  
      self.transform[3,1] = self.matrix.GetElement(3, 1)
      self.transform[3,2] = self.matrix.GetElement(3, 2)
      self.transform[3,3] = self.matrix.GetElement(3, 3)
      self.secondTransform_matrices.append(self.transform.copy()) 
    
    ############## Third #############
    if self.thirdTransform is not None:

      self.thirdTransform.GetMatrixTransformToParent(self.matrix)
      self.transform[0,0] = self.matrix.GetElement(0, 0)
      self.transform[0,1] = self.matrix.GetElement(0, 1)
      self.transform[0,2] = self.matrix.GetElement(0, 2) 
      self.transform[0,3] = self.matrix.GetElement(0, 3) 
      self.transform[1,0] = self.matrix.GetElement(1, 0)
      self.transform[1,1] = self.matrix.GetElement(1, 1) 
      self.transform[1,2] = self.matrix.GetElement(1, 2)
      self.transform[1,3] = self.matrix.GetElement(1, 3)
      self.transform[2,0] = self.matrix.GetElement(2, 0)  
      self.transform[2,1] = self.matrix.GetElement(2, 1)
      self.transform[2,2] = self.matrix.GetElement(2, 2)
      self.transform[2,3] = self.matrix.GetElement(2, 3)
      self.transform[3,0] = self.matrix.GetElement(3, 0)  
      self.transform[3,1] = self.matrix.GetElement(3, 1)
      self.transform[3,2] = self.matrix.GetElement(3, 2)
      self.transform[3,3] = self.matrix.GetElement(3, 3)
      self.thirdTransform_matrices.append(self.transform.copy()) 

  #######################################################################
  ###################### SAVE DATA TO FILE ##############################
  #######################################################################

  def saveDataStreamToMhaFile(self): 

    if self.firstTransform is not None:
    
      # Create path
      dateAndTime = time.strftime("_%Y-%m-%d_%H-%M-%S")
      mhaFilePath = slicer.modules.transformrecorder.path.replace("TransformRecorder.py","") + 'SavedData/' + 'TransformRecorder_1_' + self.firstTransform_name + '_' + dateAndTime + '.mha'
      
      # Create File
      mha_file = open(mhaFilePath, "w")    
      
      # Write Header
      mha_file.write('ObjectType = Image\n')
      mha_file.write('NDims = 3\n')
      mha_file.write('BinaryData = True\n')
      mha_file.write('BinaryDataByteOrderMSB = False\n')
      mha_file.write('CompressedData = False\n')
      mha_file.write('TransformMatrix = 1 0 0 0 1 0 0 0 1\n')
      mha_file.write('Offset = 0 0 0\n')
      mha_file.write('CenterOfRotation = 0 0 0\n')
      mha_file.write('AnatomicalOrientation = RAI\n')
      mha_file.write('ElementSpacing = 1 1 1\n')
      mha_file.write('CustomFieldNames = DefaultFrameTransformName UltrasoundImageOrientation\n')
      mha_file.write('CustomFrameFieldNames = ' + self.firstTransform_name + 'Transform Timestamp FrameNumber ' + self.firstTransform_name + 'TransformStatus\n')
      mha_file.write('DefaultFrameTransformName = ' + self.firstTransform_name + 'Transform\n')

      # Prepare Data
      timeStamp = numpy.array(self.timeStamp)
     
      firstTransform_matrices = numpy.array(self.firstTransform_matrices)

      # Write Data to MHA File
      frameCounter = 0
      for i in range(timeStamp.shape[0]):
        # Convert frame counter to string of length 4
        numZerosToAdd = 4 - len(str(frameCounter))
        frameCounter_string = ''
        for j in range(numZerosToAdd):
          frameCounter_string = '0' + frameCounter_string
        frameCounter_string = frameCounter_string + str(frameCounter)

        mha_file.write('Seq_Frame' + frameCounter_string + '_FrameNumber = ' + str(frameCounter) + '\n')
        mha_file.write('Seq_Frame' + frameCounter_string + '_' + self.firstTransform_name + 'TransformStatus = OK\n')
        mha_file.write('Seq_Frame' + frameCounter_string + '_' + self.firstTransform_name + 'Transform = ' + str(firstTransform_matrices[i, 0, 0]) + ' ' + str(firstTransform_matrices[i, 0, 1]) + ' ' + str(firstTransform_matrices[i, 0, 2]) + ' ' + str(firstTransform_matrices[i, 0, 3]) + ' ' + str(firstTransform_matrices[i, 1, 0]) + ' ' + str(firstTransform_matrices[i, 1, 1]) + ' ' + str(firstTransform_matrices[i, 1, 2]) + ' ' + str(firstTransform_matrices[i, 1, 3]) + ' ' + str(firstTransform_matrices[i, 2, 0]) + ' ' + str(firstTransform_matrices[i, 2, 1]) + ' ' + str(firstTransform_matrices[i, 2, 2]) + ' ' + str(firstTransform_matrices[i, 2, 3]) + ' ' +'0.0 0.0 0.0 1.0 \n')
        mha_file.write('Seq_Frame' + frameCounter_string + '_Timestamp = ' + str(timeStamp[i]) + '\n')
        
        frameCounter = frameCounter + 1
                        
      mha_file.write('UltrasoundImageOrientation = MFA\n')
      mha_file.write('DimSize = 1 1 500\n')
      mha_file.write('Kinds = domain domain list\n')
      mha_file.write('ElementType = MET_UCHAR\n')
      mha_file.write('ElementDataFile = LOCAL\n')
      
      mha_file.close()

    if self.secondTransform is not None:
    
      # Create path
      dateAndTime = time.strftime("_%Y-%m-%d_%H-%M-%S")
      mhaFilePath = slicer.modules.transformrecorder.path.replace("TransformRecorder.py","") + 'SavedData/' + 'TransformRecorder_2_' + self.secondTransform_name + '_' + dateAndTime + '.mha'
      
      # Create File
      mha_file = open(mhaFilePath, "w")    
      
      # Write Header
      mha_file.write('ObjectType = Image\n')
      mha_file.write('NDims = 3\n')
      mha_file.write('BinaryData = True\n')
      mha_file.write('BinaryDataByteOrderMSB = False\n')
      mha_file.write('CompressedData = False\n')
      mha_file.write('TransformMatrix = 1 0 0 0 1 0 0 0 1\n')
      mha_file.write('Offset = 0 0 0\n')
      mha_file.write('CenterOfRotation = 0 0 0\n')
      mha_file.write('AnatomicalOrientation = RAI\n')
      mha_file.write('ElementSpacing = 1 1 1\n')
      mha_file.write('CustomFieldNames = DefaultFrameTransformName UltrasoundImageOrientation\n')
      mha_file.write('CustomFrameFieldNames = ' + self.secondTransform_name + 'Transform Timestamp FrameNumber ' + self.secondTransform_name + 'TransformStatus\n')
      mha_file.write('DefaultFrameTransformName = ' + self.secondTransform_name + 'Transform\n')

      # Prepare Data
      timeStamp = numpy.array(self.timeStamp)
     
      secondTransform_matrices = numpy.array(self.secondTransform_matrices)

      # Write Data to MHA File
      frameCounter = 0
      for i in range(timeStamp.shape[0]):
        # Convert frame counter to string of length 4
        numZerosToAdd = 4 - len(str(frameCounter))
        frameCounter_string = ''
        for j in range(numZerosToAdd):
          frameCounter_string = '0' + frameCounter_string
        frameCounter_string = frameCounter_string + str(frameCounter)

        mha_file.write('Seq_Frame' + frameCounter_string + '_FrameNumber = ' + str(frameCounter) + '\n')
        mha_file.write('Seq_Frame' + frameCounter_string + '_' + self.secondTransform_name + 'TransformStatus = OK\n')
        mha_file.write('Seq_Frame' + frameCounter_string + '_' + self.secondTransform_name + 'Transform = ' + str(secondTransform_matrices[i, 0, 0]) + ' ' + str(secondTransform_matrices[i, 0, 1]) + ' ' + str(secondTransform_matrices[i, 0, 2]) + ' ' + str(secondTransform_matrices[i, 0, 3]) + ' ' + str(secondTransform_matrices[i, 1, 0]) + ' ' + str(secondTransform_matrices[i, 1, 1]) + ' ' + str(secondTransform_matrices[i, 1, 2]) + ' ' + str(secondTransform_matrices[i, 1, 3]) + ' ' + str(secondTransform_matrices[i, 2, 0]) + ' ' + str(secondTransform_matrices[i, 2, 1]) + ' ' + str(secondTransform_matrices[i, 2, 2]) + ' ' + str(secondTransform_matrices[i, 2, 3]) + ' ' +'0.0 0.0 0.0 1.0 \n')
        mha_file.write('Seq_Frame' + frameCounter_string + '_Timestamp = ' + str(timeStamp[i]) + '\n')
        
        frameCounter = frameCounter + 1
                        
      mha_file.write('UltrasoundImageOrientation = MFA\n')
      mha_file.write('DimSize = 1 1 500\n')
      mha_file.write('Kinds = domain domain list\n')
      mha_file.write('ElementType = MET_UCHAR\n')
      mha_file.write('ElementDataFile = LOCAL\n')
      
      mha_file.close()

    if self.thirdTransform is not None:
    
      # Create path
      dateAndTime = time.strftime("_%Y-%m-%d_%H-%M-%S")
      mhaFilePath = slicer.modules.transformrecorder.path.replace("TransformRecorder.py","") + 'SavedData/' + 'TransformRecorder_3_' + self.thirdTransform_name + '_' + dateAndTime + '.mha'
      
      # Create File
      mha_file = open(mhaFilePath, "w")    
      
      # Write Header
      mha_file.write('ObjectType = Image\n')
      mha_file.write('NDims = 3\n')
      mha_file.write('BinaryData = True\n')
      mha_file.write('BinaryDataByteOrderMSB = False\n')
      mha_file.write('CompressedData = False\n')
      mha_file.write('TransformMatrix = 1 0 0 0 1 0 0 0 1\n')
      mha_file.write('Offset = 0 0 0\n')
      mha_file.write('CenterOfRotation = 0 0 0\n')
      mha_file.write('AnatomicalOrientation = RAI\n')
      mha_file.write('ElementSpacing = 1 1 1\n')
      mha_file.write('CustomFieldNames = DefaultFrameTransformName UltrasoundImageOrientation\n')
      mha_file.write('CustomFrameFieldNames = ' + self.thirdTransform_name + 'Transform Timestamp FrameNumber ' + self.thirdTransform_name + 'TransformStatus\n')
      mha_file.write('DefaultFrameTransformName = ' + self.thirdTransform_name + 'Transform\n')

      # Prepare Data
      timeStamp = numpy.array(self.timeStamp)
     
      thirdTransform_matrices = numpy.array(self.thirdTransform_matrices)

      # Write Data to MHA File
      frameCounter = 0
      for i in range(timeStamp.shape[0]):
        # Convert frame counter to string of length 4
        numZerosToAdd = 4 - len(str(frameCounter))
        frameCounter_string = ''
        for j in range(numZerosToAdd):
          frameCounter_string = '0' + frameCounter_string
        frameCounter_string = frameCounter_string + str(frameCounter)

        mha_file.write('Seq_Frame' + frameCounter_string + '_FrameNumber = ' + str(frameCounter) + '\n')
        mha_file.write('Seq_Frame' + frameCounter_string + '_' + self.thirdTransform_name + 'TransformStatus = OK\n')
        mha_file.write('Seq_Frame' + frameCounter_string + '_' + self.thirdTransform_name + 'Transform = ' + str(thirdTransform_matrices[i, 0, 0]) + ' ' + str(thirdTransform_matrices[i, 0, 1]) + ' ' + str(thirdTransform_matrices[i, 0, 2]) + ' ' + str(thirdTransform_matrices[i, 0, 3]) + ' ' + str(thirdTransform_matrices[i, 1, 0]) + ' ' + str(thirdTransform_matrices[i, 1, 1]) + ' ' + str(thirdTransform_matrices[i, 1, 2]) + ' ' + str(thirdTransform_matrices[i, 1, 3]) + ' ' + str(thirdTransform_matrices[i, 2, 0]) + ' ' + str(thirdTransform_matrices[i, 2, 1]) + ' ' + str(thirdTransform_matrices[i, 2, 2]) + ' ' + str(thirdTransform_matrices[i, 2, 3]) + ' ' +'0.0 0.0 0.0 1.0 \n')
        mha_file.write('Seq_Frame' + frameCounter_string + '_Timestamp = ' + str(timeStamp[i]) + '\n')
        
        frameCounter = frameCounter + 1
                        
      mha_file.write('UltrasoundImageOrientation = MFA\n')
      mha_file.write('DimSize = 1 1 500\n')
      mha_file.write('Kinds = domain domain list\n')
      mha_file.write('ElementType = MET_UCHAR\n')
      mha_file.write('ElementDataFile = LOCAL\n')
      
      mha_file.close()


    


class TransformRecorderTest(ScriptedLoadableModuleTest):
  """
  This is the test case for your scripted module.
  Uses ScriptedLoadableModuleTest base class, available at:
  https://github.com/Slicer/Slicer/blob/master/Base/Python/slicer/ScriptedLoadableModule.py
  """

  def setUp(self):
    """ Do whatever is needed to reset the state - typically a scene clear will be enough.
    """
    slicer.mrmlScene.Clear(0)

  def runTest(self):
    """Run as few or as many tests as needed here.
    """
    self.setUp()
    self.test_TransformRecorder1()

  def test_TransformRecorder1(self):
    """ Ideally you should have several levels of tests.  At the lowest level
    tests should exercise the functionality of the logic with different inputs
    (both valid and invalid).  At higher levels your tests should emulate the
    way the user would interact with your code and confirm that it still works
    the way you intended.
    One of the most important features of the tests is that it should alert other
    developers when their changes will have an impact on the behavior of your
    module.  For example, if a developer removes a feature that you depend on,
    your test should break so they know that the feature is needed.
    """

    self.delayDisplay("Starting the test")
    #
    # first, get some data
    #
    import urllib
    downloads = (
        ('http://slicer.kitware.com/midas3/download?items=5767', 'FA.nrrd', slicer.util.loadVolume),
        )

    for url,name,loader in downloads:
      filePath = slicer.app.temporaryPath + '/' + name
      if not os.path.exists(filePath) or os.stat(filePath).st_size == 0:
        logging.info('Requesting download %s from %s...\n' % (name, url))
        urllib.urlretrieve(url, filePath)
      if loader:
        logging.info('Loading %s...' % (name,))
        loader(filePath)
    self.delayDisplay('Finished with download and loading')

    volumeNode = slicer.util.getNode(pattern="FA")
    logic = TransformRecorderLogic()
    self.assertIsNotNone( logic.hasImageData(volumeNode) )
    self.delayDisplay('Test passed!')

class Timer(object):

  def __init__(self):
    self.startTime = 0.0
    self.stopTime = 0.0
    self.timerStarted = False
    
  def startTimer(self):
    if not self.timerStarted:      
      self.startTime = time.clock()
      if self.stopTime != 0.0:
        self.stopTime = time.clock() - self.stopTime
      self.timerStarted = True
    else:
      logging.warning('Timer already running')
      
  def stopTimer(self):
    if self.timerStarted:
      self.stopTime = time.clock()
      self.timerStarted = False
    else:
      logging.warning('Timer not running')
      
  def getElapsedTime(self):
    if self.startTime == 0.0:
      return 0.0
    elif self.stopTime == 0.0:
      return time.clock() - self.startTime
    else:
      return time.clock() - (self.stopTime - self.startTime)
        
  def resetTimer(self):
    if self.startTime != 0.0:
      self.startTime = time.clock()    
      self.stopTime = 0.0
