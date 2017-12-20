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
	
	#calc costs
	total_costs, avg_costs, raw_kilo_bytes_costs, avg_cost_per_kilo_byte, total_kilo_bytes = calcCosts(outputdir)
	print calcCosts(outputdir)

	#calc cache stats
	cache_hits, cache_misses, cache_hit_ratio = calcCacheStats(outputdir)
	print cache_hit_ratio

	output_file = open(outputdir+"../0.8_video2.txt", "w")
	output_file.write("Video_Representation:" +str(video_res["Avg.Representation"]) + "\n")
	output_file.write("Video_StallingMS:" +str(video_res["Avg.StallingMS"]) + "\n")
	output_file.write("Video_SegmentBitrate:" +str(video_res["Avg.SegmentBitrate"]) + "\n")
	output_file.write("Video_Switches:" +str(video_res["Avg.Switches"]) + "\n")
	output_file.write("Avg.QoE.VideoQuality:" +str(video_res["Avg.QoE.VideoQuality"]) + "\n")
	output_file.write("Avg.QoE.QualityVariations:" +str(video_res["Avg.QoE.QualityVariations"]) + "\n")
	output_file.write("Avg.QoE.StallingTime:" +str(video_res["Avg.QoE.StallingTime"]) + "\n")
	output_file.write("\n")

	output_file.write("Total_Costs:" + str(total_costs) + "\n")
	output_file.write("Avg_Costs:" + str(avg_costs) + "\n")
	output_file.write("Raw_Kilobytes_Costs:" + str(raw_kilo_bytes_costs) + "\n")
	output_file.write("AVG_Cost_Per_Kilobyte:" + str(avg_cost_per_kilo_byte) + "\n")
	output_file.write("Total_Transmitted_Kilobytes:" + str(total_kilo_bytes) + "\n")
	output_file.write("\n")
	
	output_file.write("Total_Cache_Hits:" + str(cache_hits) + "\n")
	output_file.write("Total_Cache_Misses:" + str(cache_misses) + "\n")
	output_file.write("Total_Cache_Hit_Ratio:" + str(cache_hit_ratio) + "\n")
	
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

	for root, dirs, files in os.walk(outputdir):
		for f in files:
			if "rate-trace" in f:
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

def calcCacheStats(outputdir):
	
	cache_hits = 0.0
	cache_misses = 0.0
	cache_hit_ratio =0.0
	routers = 0

	for root, dirs, files in os.walk(outputdir):
		for f in files:
			if "cs-trace" in f:
				routers += 1
				cs_stats = ds.process_cs_trace(outputdir+"/"+f)
	
	for key in cs_stats:
		cache_hits += cs_stats[key]['CacheHits']
		cache_misses += cs_stats[key]['CacheMisses']
	cache_hit_ratio = cache_hits / (cache_hits+cache_misses)

	return cache_hits, cache_misses, cache_hit_ratio


print "Start"
SIMULATION_DIR=os.getcwd()
SIMULATION_OUTPUT = SIMULATION_DIR
SIMULATION_OUTPUT += "/output/prob/0.8/video2"
print SIMULATION_OUTPUT
generateStats(SIMULATION_OUTPUT) 
print "Finished."

