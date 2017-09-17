#! /usr/bin/python

import time
import numpy
import os
import glob
import collections
import shutil
import re

def calcCosts(outputdir):

	cost_function = {}
	cost_function["257"] = 3
	cost_function["258"] = 2
	cost_function["259"] = 1

	costs = 0.0
	total_interests = 0.0
	raw_kilo_bytes_costs  = 0.0
	total_kilo_bytes = 0.0

	FACE_INDEX = 2 
	TYPE_INDEX = 4
	PACKET_NR_INDEX = 7
	KILOBYTES_RAW_INDEX = 8

	#for root, dirs, files in os.walk(rootdir):
	#	for f in files:
	#		if "saf-router" in f:			
	f = "rate-output.txt"
	fp = open(outputdir+"/"+f,"r")
	for line in fp:
					l = line.split('\t')

					if(len(l) < PACKET_NR_INDEX+1):
						continue

					if l[FACE_INDEX] in cost_function.keys():
						if "OutInterests" in l[TYPE_INDEX]:
							costs += cost_function[l[FACE_INDEX]] * float(l[PACKET_NR_INDEX])
							total_interests += float(l[PACKET_NR_INDEX])

						#gather raw bytes
						if "OutInterests" in l[TYPE_INDEX]:
							raw_kilo_bytes_costs  += cost_function[l[FACE_INDEX]] * float(l[KILOBYTES_RAW_INDEX])
							total_kilo_bytes += float(l[KILOBYTES_RAW_INDEX])
						if "InData" in l[TYPE_INDEX]:
							raw_kilo_bytes_costs  += cost_function[l[FACE_INDEX]] * float(l[KILOBYTES_RAW_INDEX])
							total_kilo_bytes += float(l[KILOBYTES_RAW_INDEX])

	#			break

	avg_costs = costs / total_interests	
	avg_cost_per_kilo_byte = raw_kilo_bytes_costs / total_kilo_bytes

	return costs, avg_costs, raw_kilo_bytes_costs , avg_cost_per_kilo_byte, total_kilo_bytes

print "Start"
SIMULATION_DIR=os.getcwd()
SIMULATION_OUTPUT = SIMULATION_DIR
SIMULATION_OUTPUT += "/output/test1"
print SIMULATION_OUTPUT 
#calc costs
total_costs, avg_costs, raw_kilo_bytes_costs, avg_cost_per_kilo_byte, total_kilo_bytes = calcCosts(SIMULATION_OUTPUT)
#print costs

#write file
output_file = open(SIMULATION_OUTPUT+"/calcCosts.txt", "w")
output_file.write("Total_Costs:" + str(total_costs) + "\n")
output_file.write("Avg_Costs:" + str(avg_costs) + "\n")
output_file.write("Raw_Kilobytes_Costs:" + str(raw_kilo_bytes_costs) + "\n")
output_file.write("AVG_Cost_Per_Kilobyte:" + str(avg_cost_per_kilo_byte) + "\n")
output_file.write("Total_Transmitted_Kilobytes:" + str(total_kilo_bytes) + "\n")

output_file.close()

print "Finished."
