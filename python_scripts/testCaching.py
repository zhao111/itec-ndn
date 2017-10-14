#! /usr/bin/python

import time
import numpy
import os
import glob
import collections
import shutil
import re
import subprocess
from subprocess import call
import threading
import time
import operator
import random

import consumer_stats as cs
import dashplayer_stats as ds

curActiveThreads = 0
invalid_runs = 0

def generateStats(rootdir):
	#calc video stats
	video_res = calcVideoStats(rootdir)
	print video_res
	
	output_file.write("Video_Representation:" +str(video_res["Avg.Representation"]) + "\n")
	output_file.write("Video_StallingMS:" +str(video_res["Avg.StallingMS"]) + "\n")
	output_file.write("Video_SegmentBitrate:" +str(video_res["Avg.SegmentBitrate"]) + "\n")
	output_file.write("Video_Switches:" +str(video_res["Avg.Switches"]) + "\n")
	output_file.write("Avg.QoE.VideoQuality:" +str(video_res["Avg.QoE.VideoQuality"]) + "\n")
	output_file.write("Avg.QoE.QualityVariations:" +str(video_res["Avg.QoE.QualityVariations"]) + "\n")
	output_file.write("Avg.QoE.StallingTime:" +str(video_res["Avg.QoE.StallingTime"]) + "\n")
	output_file.write("\n")
	
	output_file.close()


def calcVideoStats(rootdir):

	avg_number_switches = 0.0
	avg_stalling_duration = 0.0
	avg_segment_bitrate = 0.0
	avg_representation = 0.0
	clients = 0

	avg_qoe_variations = 0.0
	avg_qoe_bitrate_sum = 0.0
	
	for root, dirs, files in os.walk(rootdir):
		for f in files:
			if "consumer_dash" in f:			
				clients += 1
				ds_stats = ds.process_dash_trace(rootdir+"/"+f,0)
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

class Thread(threading.Thread):
    # init
  def __init__(self,job_number, sys_cal, callback_method, src ,dst):
		super(Thread,self).__init__()
		self.sysCall = sys_cal
		self.jobNumber = job_number
		self.callback = callback_method
		self.src = src
		self.dst = dst

  # overwriting run method of threading.Thread (do not call this method, call thread.start() )
  def run(self):

		if not os.path.exists(self.src+"/traces"):
			os.makedirs(self.src+"/traces")

		fpOut = open("t_" + str(self.jobNumber) + ".stdout.txt", "w")

		# start subprocess
		proc = subprocess.Popen(self.sysCall,stdout=fpOut, cwd=self.src)
		proc.communicate() # wait until finished

		# sleep 0.5 seconds to be sure the OS really has finished the process
		time.sleep(0.5)

		fpOut.close()
		os.remove("t_" + str(self.jobNumber) + ".stdout.txt")

		# callback
		print "threadFinished(job_" + str(self.jobNumber) + ")"
		self.callback(self.jobNumber,self.src,self.dst, proc.returncode)

def threadFinished(job_number,src,dst,returncode):
	#compute statistics

	global curActiveThreads, invalid_runs

	if(returncode != 0):
		invalid_runs += 1
		print "Error in job_" + str(job_number) +". Simulation incomplete!"
	else:
		print "computeStats(job_" + str(job_number) + ")"
		try:
			print src
			generateStats(src+"/traces/")
		except Exception:
			invalid_runs += 1
			pass

	#copy results
	#files = glob.glob(src + "/traces/*STATS*.txt")
    #files.extend(glob.glob(src + "/traces/*cs-trace*.txt"))
	#files.extend(glob.glob(src + "/traces/*aggregate*.txt"))
	files = glob.glob(src + "/traces/*.txt")

	if not os.path.exists(dst):
		os.makedirs(dst)

	#for f in files:
	#	shutil.move(f, dst+"/"+os.path.basename(f))

	#print "DELTE FOLDER " + src
	#shutil.rmtree(src)

	print "statsCollected(job_" + str(job_number) + ")"

	curActiveThreads -= 1

SIMULATION_DIR=os.getcwd()

THREADS = 1

SIMULATION_OUTPUT = SIMULATION_DIR 
SIMULATION_OUTPUT += "/output/testCaching/"

scenario="testCaching"
topology = "--topology="+SIMULATION_DIR+"/topologies/3-consumer.top"

singleRoute="--route=single"
allRoute="--route=all"
bestRoute="--fw-strategy=bestRoute " + allRoute
forwardingStrategies = [bestRoute]

SCENARIOS = {}

for strategy in forwardingStrategies:
	name = ""
	if("fw-strategy=bestRoute" in strategy):
		name += "BestRoute"
	else:
		name += "UnknownStrategy"

	SCENARIOS.update({name: {"executeable": scenario,"params": [strategy]}})

call([SIMULATION_DIR + "/waf"])

###script start
print "\nCurring working dir = " + SIMULATION_DIR + "\n"

time.sleep(5)

###script start
job_number = 0

for scenarioName in SCENARIOS.keys():
	executeable = SCENARIOS[scenarioName]['executeable']
	executeable = "build/" + executeable
	print "------------------------------------------------------------------------"
	sysCall = [SIMULATION_DIR+"/" + executeable] +  SCENARIOS[scenarioName]['params']
	print sysCall

	dst = SIMULATION_OUTPUT+scenarioName + "/output_run"
	src = SIMULATION_OUTPUT+"../ramdisk/tmp_folder_"+ str(job_number)

	thread = Thread(job_number, sysCall, threadFinished, src, dst)
	thread.start()
# end for

print ""
print "We had " + str(invalid_runs) + " invalid runs"
print "Finished."
