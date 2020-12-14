# -*- coding: utf-8 -*-
"""
Created on Fri Dec  4 14:04:49 2020

@author: Chanil
"""

################################# DICOM RT Dose Slice Resize 0.0.1 #################################

import pydicom
import numpy as np
from scipy.ndimage import zoom
from pydicom import dcmread
from pydicom.dataset import FileDataset, FileMetaDataset

import os
import datetime

## Road original files ##

# get original file name from user
originalFileName = input("Type original file name : ")

# read FileDataset from file
originalRTDoseFile = dcmread(originalFileName)

# read FileMetaDataset from file
originalRTDoseMeta = pydicom.filereader.read_file_meta_info(originalFileName)

print("Data reading succeeded!")

## Resizing dimension (Dose grid in RT dose file) ##

# Get resizing information from user
sliceThicknessSetting = int(input("Set slice thickness of new file : "))
numberOfFramesSetting = int(input("Set Z scale (Slice amount) : "))

# Caculate dose grid from pixel array and dose grid scaling factor in original file
originalRTDoseFile.x_axis = np.arange(originalRTDoseFile.Columns) * originalRTDoseFile.PixelSpacing[0]
originalRTDoseFile.y_axis = np.arange(originalRTDoseFile.Rows) * originalRTDoseFile.PixelSpacing[1]
originalRTDoseFile.z_axis = np.array(originalRTDoseFile.GridFrameOffsetVector) + originalRTDoseFile.ImagePositionPatient[2]

# caculate dose grid with multiplying dose grid scaling
pixel_array_initial = originalRTDoseFile.pixel_array * originalRTDoseFile.DoseGridScaling
dose_grid_initial = np.swapaxes(pixel_array_initial, 0, 2)

# ratio from original to results
zAxisScale = float(numberOfFramesSetting)/originalRTDoseFile.NumberOfFrames

# dose grid modification about z axis
# scipy basic mode is 'constant', there are reflect, nearest, mirror, wrap interpolation.
# order 0 => nearest interpolation, order 1 => bilinear interpolaton, order 3 => cubic interpolation
modifiedDoseGrid = zoom(dose_grid_initial, output=None, zoom=(1, 1, zAxisScale), order=1 , mode='constant')

# make modified dose grid to pixel data and grid scaling factor in new dicom file
# based on uint 16 dicom file. if dicom file has uint32 attribute, need to change. 
DoseGridScalingFactor = np.max(modifiedDoseGrid) / np.iinfo(np.uint16).max
pixelData_temp = np.swapaxes(modifiedDoseGrid, 0, 2) / DoseGridScalingFactor
pixelDataModified = np.uint16(pixelData_temp).tobytes()

## dicom data specification  ##

filename_little_endian = os.getcwd() + '\\' + 'energylayersum_resized.dcm'

# Writing meta-data information ----------------------------------------------------------
print("Setting file meta information...")

# Populate required values for file meta information
file_meta = FileMetaDataset()

# This means 'RT Dose Storage' in DICOM
file_meta.MediaStorageSOPClassUID = '1.2.840.10008.5.1.4.1.1.481.2'
file_meta.MediaStorageSOPInstanceUID = originalRTDoseMeta.MediaStorageSOPInstanceUID

# This means 'Implicit VR little endian'
file_meta.TransferSyntaxUID = '1.2.840.10008.1.2'
file_meta.ImplementationClassUID = originalRTDoseMeta.ImplementationClassUID
file_meta.ImplementationVersionName = 'SMC_RTDoseSliceResize 0.0.1'
file_meta.SourceApplicationEntityTitle = 'SMC_RTDoseSliceResize'

# Writing dataset information ------------------------------------------------------------
print("Setting dataset values...")

# Create the FileDataset instance (initially no data elements, but file_meta supplied)
ds = FileDataset(filename_little_endian, {},
                  file_meta=file_meta, preamble=b"\0" * 128)

# get current time information
dt = datetime.datetime.now()
timeStr_ymd = dt.strftime('%Y%m%d')
timeStr_short = dt.strftime('%H%M%S') # short format 
timeStr_long = dt.strftime('%H%M%S.%f')  # long format with micro seconds

# Add the data elements
ds.ImageType = 'DERIVED' # image is derived from one or more image's pixel value
ds.InstanceCreationDate = timeStr_ymd
ds.InstanceCreationTime = timeStr_short

# This means 'RT Dose Storage' in DICOM
ds.SOPClassUID = '1.2.840.10008.5.1.4.1.1.481.2'
ds.SOPInstanceUID = originalRTDoseFile.SOPInstanceUID

ds.StudyDate = timeStr_ymd
ds.SeriesDate = timeStr_ymd
ds.ContentDate = timeStr_ymd
ds.StudyTime = timeStr_long
ds.SeriesTime = timeStr_short
ds.ContentTime = timeStr_short
ds.AccessionNumber = ''
ds.Modality = 'RTDOSE'
ds.Manufacturer = 'SMC_RTDoseSliceResize'
ds.ReferringPhysicianName = ''
ds.SeriesDescription = 'Dosemap [Gy]'
ds.ManufacturerModelName = 'SMC_RTDoseSliceResize 0.0.1'
ds.PatientName = originalRTDoseFile.PatientName
ds.PatientID = originalRTDoseFile.PatientID
ds.PatientBirthDate = originalRTDoseFile.PatientBirthDate
ds.PatientSex = originalRTDoseFile.PatientSex

# Modified SlickThickness in this program sequence
ds.SliceThickness = sliceThicknessSetting

ds.StudyInstanceUID = originalRTDoseFile.StudyInstanceUID
ds.SeriesInstanceUID = originalRTDoseFile.SeriesInstanceUID

ds.StudyID = originalRTDoseFile.StudyID
ds.SeriesNumber = originalRTDoseFile.SeriesNumber
ds.InstanceNumber = originalRTDoseFile.InstanceNumber
ds.ImagePositionPatient = originalRTDoseFile.ImagePositionPatient
ds.ImageOrientationPatient = originalRTDoseFile.ImageOrientationPatient

ds.FrameOfReferenceUID = originalRTDoseFile.FrameOfReferenceUID
ds.SamplesPerPixel = originalRTDoseFile.SamplesPerPixel
ds.PhotometricInterpretation = originalRTDoseFile.PhotometricInterpretation

# Modified NumberOfFrames in this program sequence
ds.NumberOfFrames = numberOfFramesSetting

ds.FrameIncrementPointer = originalRTDoseFile.FrameIncrementPointer
ds.Rows = originalRTDoseFile.Rows
ds.Columns = originalRTDoseFile.Columns
ds.PixelSpacing = originalRTDoseFile.PixelSpacing
ds.BitsAllocated = originalRTDoseFile.BitsAllocated
ds.BitsStored = originalRTDoseFile.BitsStored
ds.HighBit = originalRTDoseFile.HighBit
ds.PixelRepresentation = originalRTDoseFile.PixelRepresentation
ds.GridFrameOffsetVector = originalRTDoseFile.GridFrameOffsetVector
ds.DoseUnits = originalRTDoseFile.DoseUnits
ds.DoseType = originalRTDoseFile.DoseType
ds.DoseSummationType = originalRTDoseFile.DoseSummationType

# Modified Pixel Data and scaling factor
ds.DoseGridScaling = DoseGridScalingFactor
ds.PixelData = pixelDataModified

# # Set the transfer syntax
ds.is_little_endian = True
ds.is_implicit_VR = True

## save as dcm ##

ds.save_as(filename_little_endian)
print("File saved successfully!")