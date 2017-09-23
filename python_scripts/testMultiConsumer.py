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

import consumer_stats as consumer_stats

curActiveThreads = 0
invalid_runs = 0

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
			#calculate_average.computeStats(src+"/traces/")
			consumer_stats.generateStatsPerSimulation(src)
		except Exception:
			invalid_runs += 1
			pass

	#copy results
	files = glob.glob(src + "/traces/*STATS*.txt")
        files.extend(glob.glob(src + "/traces/*cs-trace*.txt"))
	files.extend(glob.glob(src + "/traces/*aggregate*.txt"))
	#iles = glob.glob(src + "/traces/*.txt")

	if not os.path.exists(dst):
		os.makedirs(dst)

	for f in files:
		shutil.move(f, dst+"/"+os.path.basename(f))

	#print "DELTE FOLDER " + src
	shutil.rmtree(src)

	print "statsCollected(job_" + str(job_number) + ")"

	curActiveThreads -= 1

def	order_results(path):
	results = {}

	for root, dirs, files in os.walk(path):
		for subdir in dirs:
		
			if "output_run" in subdir:
				continue

			#print root+subdir

			files = glob.glob(root+subdir + "/*/*STATS*.txt" )
		
			avg_ratio = 0.0
			file_count = 0
			cache_hit_ratio = 0.0

			for file in files:

				#print file
				f = open(file, "r")
				for line in f:
					if(line.startswith("Ratio:")):
						avg_ratio += float(line[len("Ratio:"):])
						
					if(line.startswith("Cache_Hit_Ratio:")):
						cache_hit_ratio += float(line[len("Cache_Hit_Ratio:"):])
					
				file_count +=1
			

			if(file_count > 0):
	 			avg_ratio /= file_count
				cache_hit_ratio /= file_count
	
			#print avg_ratio
			results.update({"AVG_RATIO:"+ subdir : avg_ratio})
			results.update({"CACHE_HIT_RATIO:"+ subdir : cache_hit_ratio})

	sorted_results = reversed(sorted(results.items(), key=operator.itemgetter(1)))
	f = open(path + "result.txt", "w+")
	for entry in sorted_results:
		f.write(entry[0] + ":" + str(entry[1]) + "\n")
		
###NOTE Start this script FROM itec-scenarios MAIN-FOLDER!!!

SIMULATION_DIR=os.getcwd()

THREADS = 1

SIMULATION_OUTPUT = SIMULATION_DIR 
SIMULATION_OUTPUT += "/output/testMultiConsumer/"

#brite config file
scenario="testMultiConsumer"

#configFolder = "/home/ndnSIM/zhaoxixi-ndn/matlab/LP/jasc_top.csv"
#topFiles = glob.glob(configFolder+"/*.top")

#top = "/home/ndnSIM/zhaoxixi-ndn/topologies/jsac.top"
#top = "comsoc_tops/LowBW_LowCon_0.top"

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
	sysCall = [SIMULATION_DIR+"/" + executeable] +  SCENARIOS[scenarioName]['params']+["--outputFolder=traces"]
	print sysCall

	dst = SIMULATION_OUTPUT+scenarioName + "/output_run"
	src = SIMULATION_OUTPUT+"../ramdisk/tmp_folder_"+ str(job_number)

	thread = Thread(job_number, sysCall, threadFinished, src, dst)
	thread.start()
# end for
order_results(SIMULATION_OUTPUT)

print ""
print "We had " + str(invalid_runs) + " invalid runs"
print "Finished."
