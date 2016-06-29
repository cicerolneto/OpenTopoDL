#OpenTopo Downloader
#Python script to download data from OpenTopography (http://opentopo.sdsc.edu/)
#
#Author: Matt Oakley
#Date of Creation: 06/08/2016

# Imports #
from bs4 import BeautifulSoup
import urllib2
import sys
import wget
import numpy as np
import os
import re

# Globals #
lidar_name_list = []
lidar_ID_list = []
lidar_private_bit_list = []

raster_name_list = []
raster_ID_list = []
raster_private_bit_list = []



def get_data_type():
	"""What kind of data does user want?

	Args:
		None

	Returns:
		string indicating whether user wants Lidar (PC_Bulk) or Raster data
	"""
	user_input = raw_input("Download [L]idar Point Cloud or [R]aster data: ")
	if user_input == "L" or user_input == "l":
		desired_data = "PC_Bulk"
	elif user_input == "R" or user_input == "r":
		desired_data = "Raster"
	else:
		print "Invalid input."
		main("OpenTopoDL.py")
	return desired_data



def get_short_name(data_type, requested_id, user_request):
	"""Find the short name of requested data

	Args:
		data_type: (string) whether the user wants lidar or raster data
		requested_id: ID number associated with the data the user wants
		user_request: Listing number associated with the data the user wants

	Returns:
		The short name of a datatset
	"""
	global lidar_private_bit_list
	global raster_private_bit_list

	short_name_line = 9
	short_name_shear = 29

	if data_type == "PC_Bulk":
		private_bit_list = lidar_private_bit_list
	elif data_type == "Raster":
		private_bit_list = raster_private_bit_list

	URL = "http://opentopo.sdsc.edu/datasetMetadata?otCollectionID=OT." + requested_id
	if private_bit_list[user_request] == 0:
		page = urllib2.urlopen(URL)
		soup = BeautifulSoup(page, "lxml")
		div = str(soup.find('div', class_ = 'well'))
		log = open("log.txt", "w")
		log.write(div)
		log.close()
		f = open("log.txt")
		lines = f.readlines()
		line = lines[short_name_line]
		short_name = line[short_name_shear:]
		f.close()
		os.remove("log.txt")
		short_name = short_name.rstrip()
		return short_name
	else:
		print "Dataset is private and unavailable for download"
		exit()



def private_bits(data_type):
	"""Determine whether data are public or private

	Args:
		data_type: string indicating Lidar or Raster data

	Returns:
		a list of bits (0 for public, 1 for private)
	"""
	# Globals #
	global lidar_name_list
	global lidar_private_bit_list
	global raster_name_list
	global raster_private_bit_list

	name_list = []
	private_bit_list = []

	#Determine which lists to use
	if data_type == "PC_Bulk":
		name_list = lidar_name_list
		private_bit_list = lidar_private_bit_list
	elif data_type == "Raster":
		name_list = raster_name_list
		private_bit_list = raster_private_bit_list

	#Construct the private_bit_list for the specified data format
	for i in range(0, len(name_list)):
		if name_list[i] == " PRIVATE DATASET":
			private_bit_list.append(1)
		else:
			private_bit_list.append(0)



def create_URL(data_type):
	"""Create URLs to data

	Creates a proper URL string and href regex,
		assigns the global name and ID lists

	Args:
		data_type: string indicating lidar or raster data

	Returns:
		A tuple containing the URL, name list, id list, and href
	"""
	global lidar_name_list
	global lidar_ID_list
	global raster_name_list
	global raster_ID_list

	if data_type == "PC_Bulk":
		URL = "http://opentopo.sdsc.edu/lidar"
		name_list = lidar_name_list
		ID_list = lidar_ID_list
		href = '^/lidarDataset*'
	elif data_type == "Raster":
		URL = "http://opentopo.sdsc.edu/lidar?format=sd"
		name_list = raster_name_list
		ID_list = raster_ID_list
		href = '^/raster*'
	else:
		raise Exception('Invalid dataset type')
	return URL, name_list, ID_list, href



def append_lists(cells, data_type, name_list, ID_list):
	"""Append long names and ID #'s to name & ID lists

	Create lists of long names and ID numbers from the acquired HTML

	Args:
		cells: HTML 'a' tags
		data_type: string indicating lidar or raster data
		name_list: List of dataset long names
		ID_list: List of dataset ID numbers

	Returns:
		None
	"""
	for i in range(0, len(cells)):
		long_name = cells[i].string
		if long_name == None:
			name_list.append(" PRIVATE DATASET")
		else:
			name_list.append(long_name)

		if data_type == "PC_Bulk":
			ID = str(cells[i]['href'])[31:]
		elif data_type == "Raster":
			ID = str(cells[i]['href'])[26:]
		ID_list.append(ID)



def area_listing(data_type, cmd_line):
	"""List available data

	List the available Lidar or Raster datasets on OpenTopography's website and
	create lists of data's long names, ID numbers, and private bits

	Args:
		data_type: string indicating lidar or raster data

	Returns:
		Integer indicating the desired dataset if not using command line,
			otherwise returns nothing.
	"""
	# Globals #
	global lidar_name_list
	global raster_name_list
	global lidar_ID_list
	global raster_ID_list

	#Obtain the proper URL, name_list, ID_list, and href regex depending on what data format the user wants
	URL, name_list, ID_list, href = create_URL(data_type)

	#Find all the datasets listed on OpenTopography's website
	page = urllib2.urlopen(URL)
	soup = BeautifulSoup(page, "lxml")
	table = soup.find("table", class_= "table table-hover table-condensed table-striped table-nospace")
	for row in table.findAll("tr"):
		cells = row.findAll('a', href = re.compile(href))
		append_lists(cells, data_type, name_list, ID_list)

	#Determine whether the dataset is public or private
	private_bits(data_type)

	if cmd_line == 0:
		#Print to the user the available datasets
		print "\n"
		for i in range(0, len(name_list)):
			print str(i + 1) + ":" + name_list[i]

		#Obtain and return the user's requested dataset's number
		print "\n"
		user_request = raw_input("Requested dataset's number entry: ")

		return int(user_request) - 1



def download_data(data_type, URL, short_name):
	"""Download files from OpenTopo

	Downloads all files immediately present and within subdirectories on
		OpenTopography's servers to the local machine with an identical file
		and subdirectory hierarchy

	Args:
		data_type: string indicating lidar or raster data
		URL: URL to the HTTP directory storing files/sub-directories
		short_name: short name corresponding to specific data files

	Returns:
		nothing
	"""
	#Obtain the proper, initial URL
	if data_type == "PC_Bulk" and URL == 0:
		URL = "https://cloud.sdsc.edu/v1/AUTH_opentopography/PC_Bulk/" + short_name + "/"
	elif data_type == "Raster" and URL == 0:
		URL = "https://cloud.sdsc.edu/v1/AUTH_opentopography/Raster/" + short_name + "/"

	#Find all files and sub-directories within the HTML of the page
	page = urllib2.urlopen(URL)
	soup = BeautifulSoup(page, "lxml")
	entries = soup.findAll('tr', class_ = "item type-application type-octet-stream")
	sub_dirs = soup.findAll('tr', class_= "item subdir")
	num_sub_dirs = len(sub_dirs)

	#Obtain/create local directories to save files to
	source_directory = os.getcwd()
	data_directory = os.path.join(source_directory, short_name)

	#Check and see if the local directory currently exists or not
	if os.path.exists(data_directory):
		os.chdir(data_directory)
	else:
		os.makedirs(short_name)
		os.chdir(data_directory)

	#Download all available files
	for i in range(0, len(entries)):
		file = entries[i].a["href"]
		URL_with_file = URL + file
		if file != "log":
			print URL_with_file
			wget.download(URL_with_file)
		print "\n"

	os.chdir(source_directory)

	#If sub-directories are present, recurse into them
	for i in range(0, num_sub_dirs):
		sub_dir_name = sub_dirs[i].a["href"]
		sub_dir_URL = URL + sub_dir_name
		os.chdir(data_directory)
		download_data(data_type, sub_dir_URL, sub_dir_name)



def main(argv):

	# Globals #
	global lidar_name_list
	global lidar_ID_list
	global lidar_private_bit_list
	global raster_name_list
	global raster_ID_list
	global raster_private_bit_list

	data_type = 0	# Boolean to check if user wants lidar or raster data "PC_Bulk" = lidar. "Raster" = raster
	user_request = 0	# number corresponding to dataset user wants to download
	cmd_line = 0		# Boolean does user want to run script with 1 command

	if len(argv) > 1: 	# arguments were supplied at command line
		cmd_line = 1
		if argv[1] == "l":
			data_type = "PC_Bulk"
		elif argv[1] == "r":
			data_type = "Raster"
		else:
			print "Invalid input"
		user_request = int(argv[2]) - 1
		area_listing(data_type, cmd_line)

	else:				# arguments were not supplied, running interactively
		print "\n"
		print "OpenTopo Downloader - Python script to download data from OpenTopography"
		print "When asked for user input, please enter the corresponding letter/number in the square brackets, []\n"
		data_type = get_data_type()
		user_request = area_listing(data_type, cmd_line)

	if data_type == "PC_Bulk":
		requested_id = lidar_ID_list[user_request]
	else:
		requested_id = raster_ID_list[user_request]

	short_name = get_short_name(data_type, requested_id, user_request)
	download_data(data_type, 0, short_name)


if __name__ == "__main__":
	main(sys.argv)
