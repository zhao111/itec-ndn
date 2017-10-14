#! /usr/bin/python

import time
import numpy
import os
import glob
import collections
import shutil
import re

import consumer_stats as cs
import dashplayer_stats as ds

def generateStats(outputdir):
	#calc video stats
	video_res = calcVideoStats(outputdir)
	print video_res
	
	output_file = open(outputdir+"/STATS.txt", "w")
	output_file.write("Video_Representation:" +str(video_res["Avg.Representation"]) + "\n")
	output_file.write("Video_StallingMS:" +str(video_res["Avg.StallingMS"]) + "\n")
	output_file.write("Video_SegmentBitrate:" +str(video_res["Avg.SegmentBitrate"]) + "\n")
	output_file.write("Video_Switches:" +str(video_res["Avg.Switches"]) + "\n")
	output_file.write("Avg.QoE.VideoQuality:" +str(video_res["Avg.QoE.VideoQuality"]) + "\n")
	output_file.write("Avg.QoE.QualityVariations:" +str(video_res["Avg.QoE.QualityVariations"]) + "\n")
	output_file.write("Avg.QoE.StallingTime:" +str(video_res["Avg.QoE.StallingTime"]) + "\n")
	output_file.write("\n")
	
	output_file.close()


def calcVideoStats(outputdir):

	avg_number_switches = 0.0
	avg_stalling_duration = 0.0
	avg_segment_bitrate = 0.0
	avg_representation = 0.0
	clients = 0

	avg_qoe_variations = 0.0
	avg_qoe_bitrate_sum = 0.0
	
	for root, dirs, files in os.walk(outputdir):
		for f in files:
			if "consumer_dash" in f:			
				clients += 1
				ds_stats = ds.process_dash_trace(outputdir+"/"+f,0)
				print ds_stats

				#see dashplayer_stats for magic numbers
				parsed_segments = ds_stats[96]

				avg_number_switches += ds_stats[99]
				avg_stalling_duration += ds_stats[6]
				avg_segment_bitrate += ds_stats[5]
				avg_representation += ds_stats[4]
		
				avg_qoe_variations += ds_stats[98]	#sum of quality variations per client
				avg_qoe_bitrate_sum += ds_stats[95] #sum of received segment bitrates
					
	#no calculate the average over the clients
	avg_number_switches /= clients
	avg_stalling_duration /= clients
	avg_segment_bitrate /= clients
	avg_representation /= clients
	avg_qoe_variations /= clients
	avg_qoe_bitrate_sum /= clients

	result = {}
	result["Avg.Switches"] = avg_number_switches
	result["Avg.StallingMS"] = avg_stalling_duration
	result["Avg.SegmentBitrate"] = avg_segment_bitrate
	result["Avg.Representation"] = avg_representation

	#QoE values according to: A Control-Theoretic Approach for Dynamic Adaptive Video Streaming over HTTP
	result["Avg.QoE.VideoQuality"] = avg_qoe_bitrate_sum
	result["Avg.QoE.QualityVariations"] = avg_qoe_variations
	result["Avg.QoE.StallingTime"] = avg_stalling_duration / 1000.0 #convert to seconds
	
	return result

print "Start"
SIMULATION_DIR=os.getcwd()
SIMULATION_OUTPUT = SIMULATION_DIR
SIMULATION_OUTPUT += "/output/testCaching"
print SIMULATION_OUTPUT
generateStats(SIMULATION_OUTPUT) 
print "Finished."
