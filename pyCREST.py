#    -*- coding: utf-8 -*-
#    Copyright (C) 2008, 2011 Ian Richardson*, Murray Thomson*, 2013 Lee Thomas**

#    *CREST (Centre for Renewable Energy Systems Technology),
#    Department of Electronic and Electrical Engineering
#    Loughborough University, Leicestershire LE11 3TU, UK
#    Tel. +44 1509 635326. Email address: I.W.Richardson@lboro.ac.uk

#    ** Institute of Energy, 
#    Cardiff School of Engineering
#    Cardiff University, CF24 3AA
#    Tel. +442920870674. Email address: ThomasL62@cf.ac.uk
#    http://energy.engineering.cf.ac.uk/

#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.

#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.

#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.



import numpy
import pprint
from random import random
import math
import csv
import time


def create_profiles(n=1,month=7,daytype='weekday'):

# check that day type is valid:
	if daytype in ['weekday', 'weekend']:
		pass
	else:
		print 'invalid day type, should be weekend or weekday'
		return 0

	if month in range(1,13):
		pass
	else:
		print 'invalid month type, should be int in range 1 to 12'
		return 0


		
	no_its = n


	appliances = numpy.genfromtxt('appliances.dat',skip_header=27,dtype=(None))
	sim_dataP_for_file = numpy.zeros([no_its,1440])
	sim_dataQ_for_file = numpy.zeros([no_its,1440])
	#appliances_in_dwelling_for_file = numpy.empty([no_its,33],dtpye='a18')
	appliances_in_dwelling_for_file = [[] for i in xrange(no_its)]
	occ_profile_for_file = numpy.zeros([no_its,144])
	
	idstring = str(no_its) + 'x_' + 'month-' + str(month) + '_' + 'daytype-' + str(daytype)
	

	
	oMonthlyRelativeTemperatureModifier = gettemperaturedata()
	

	
	for i in range (0,no_its):
		if i==0:
			time1 = time.time()
		appliances_in_dwelling = ConfigureAppliancesInDwelling(appliances)
		
		activity_stats = numpy.genfromtxt('activity_stats.dat',skip_header=11,dtype=(None))

		sim_dataP = numpy.zeros([len(appliances_in_dwelling[:]),1440])
		sim_dataQ = numpy.zeros([len(appliances_in_dwelling[:]),1440])
		

		occ_profile = get_occ_profile(daytype)
		occ_profile_for_file[i][:] = occ_profile
		lighting_demand_data = RunLightingSimulation(month,occ_profile)

		for appliance in range(0,len(appliances_in_dwelling[:])-1):

			sApplianceType = appliances_in_dwelling[appliance][15]
			iMeanCycleLength = appliances_in_dwelling[appliance][3]
			iCyclesPerYear = appliances_in_dwelling[appliance][2]
			iStandbyPower = appliances_in_dwelling[appliance][5]
			iRatedPower = appliances_in_dwelling[appliance][4]
			dCalibration = appliances_in_dwelling[appliance][18]
			dOwnership = appliances_in_dwelling[appliance][0]
			iTargetAveragekWhYear = appliances_in_dwelling[appliance][21]
			sUseProfile = appliances_in_dwelling[appliance][16]
			iRestartDelay = appliances_in_dwelling[appliance][6]
			
			# Initialisation
			iCycleTimeLeft = 0
			dActivityProbability = 0
			# Randomly delay the start of appliances that have a restart delay (e.g. cold appliances with more regular intervals)
			iRestartDelayTimeLeft = random() * iRestartDelay * 2 # Weighting is 2 just to provide some diversity
			
			# Make the rated power variable over a normal distribution to provide some variation
			iRatedPower = GetMonteCarloNormalDistGuess(iRatedPower,iRatedPower/10)
			
			for iMinute in range (-198,1441): #'Pre-runs' for 198 mins to allow for potential startup of washing machines
				if iMinute <=0:
					#print iMinute
					iMinute = 1440+iMinute
					#print iMinute
					#Get the ten minute period count
					iTenMinuteCount = ((iMinute - 1)/10)
					# Get the number of current active occupants for this minute (convert from 10 minute to 1 minute resolution)
					iActiveOccupants = occ_profile[iTenMinuteCount] 
			
					# If this appliance is off having completed a cycle (ie. a restart delay)
					if (iCycleTimeLeft <= 0) and (iRestartDelayTimeLeft > 0):
						#Decrement the cycle time left
						iRestartDelayTimeLeft = iRestartDelayTimeLeft - 1
										
					# Else if this appliance is off
					elif iCycleTimeLeft <= 0:
						# There must be active occupants, or the profile must not depend on occupancy for a start event to occur
						if (iActiveOccupants > 0 and sUseProfile != "CUSTOM") or (sUseProfile == "LEVEL"):
							# Variable to store the event probability (default to 1)
							dActivityProbability = 1
							# For appliances that depend on activity profiles and is not a custom profile ...
							if (sUseProfile != "LEVEL") and (sUseProfile != "ACTIVE_OCC") and (sUseProfile != "CUSTOM") and (sUseProfile != "ARRIVAL"):
								
								if daytype == 'weekday':
									dayflag = 0
								else:
									dayflag = 1
									
								[activity_days] = [activity_stats[:][x] for x in numpy.where(activity_stats['f0']==dayflag)]
								[activity_occs] = [activity_days[:][x] for x in numpy.where(activity_days['f1']==iActiveOccupants)]
								[activity_use_profile] = [activity_occs[:][x] for x in numpy.where(activity_occs['f2']==sUseProfile)] # sUseProfile = appliances[16] = activity type (string)
								dActivityProbability = activity_use_profile[0][iTenMinuteCount+3] # Get the probability for this activity profile for this time step
									 
									
								# For electric space heaters ... (excluding night storage heaters)
							elif sApplianceType == "ELEC_SPACE_HEATING":
								# If this appliance is an electric space heater, then activity probability is a function of the month of the year
								dActivityProbability = round(oMonthlyRelativeTemperatureModifier[month],4)
									
							# Check the probability of a start event
							if (random() < ((dCalibration) * dActivityProbability)):
								# This is a start event
								[iPower, iCycleTimeLeft,iRestartDelayTimeLeft] = StartAppliance(iRestartDelay, iMeanCycleLength, iCycleTimeLeft,iRatedPower, iStandbyPower, sApplianceType)
							
					
						# Custom appliance handler: storage heaters have a simple representation
						elif sUseProfile == "CUSTOM" and sApplianceType == "STORAGE_HEATER":
											
							# The number of cycles (one per day) set out in the calibration sheet
							# is used to determine whether the storage heater is used
							# This model does not account for the changes in the Economy 7 time
							# It assumes that the time starts at 00:30 each day
							if iTenMinuteCount == 4: 	# ie. 00:30 - 00:40
								#Assume January 14th is the coldest day of the year
								#Dim oDate, oDateOn, oDateOff As Date
								#Dim monthOn, monthOff As Integer
								#oDate = #1/14/1997#

								# Get the month and day when the storage heaters are turned on and off, using the number of cycles per year

								monthOff = (14+(iCyclesPerYear/2))/4.3
								monthOn = (365+14+(0-iCyclesPerYear/2))/4.3

								# If this is a month in which the appliance is turned on of off
								if month == monthOff or month == monthOn:
									# Pick a 50% chance since this month has only a month of year resolution
									dProbability = 0.5 / 10  # (since there are 10 minutes in this period)
								elif month > monthOff and month < monthOn:
									# The appliance is not used in summer
									dProbability = 0
								else:
									# The appliance is used in winter
									dProbability = 1

								# Determine if a start event occurs
								if random() <= dProbability:
									# This is a start event
									[iPower, iCycleTimeLeft,iRestartDelayTimeLeft] = StartAppliance(iRestartDelay, iMeanCycleLength, iCycleTimeLeft,iRatedPower, iStandbyPower, sApplianceType)
												
					else:
						# The appliance is on - if the occupants become inactive, switch off the appliance
						if iActiveOccupants == 0 and sUseProfile != "LEVEL" and sUseProfile != "ACT_LAUNDRY" and sUseProfile != "CUSTOM" and sUseProfile != "ARRIVAL":
							pass
							# Do nothing. The activity will be completed upon the return of the active occupancy.
							# Note that LEVEL means that the appliance use is not related to active occupancy.
							# Note also that laundry appliances do not switch off upon a transition to inactive occupancy.
						else:
							# Set the power
							#do nothing here as pre 0 mins (working out what is on from previous night) #iPower = GetPowerUsage(iCycleTimeLeft,iRatedPower, iStandbyPower, sApplianceType)
							# Decrement the cycle time left
							iCycleTimeLeft = iCycleTimeLeft - 1

					# get lighting data and add to iPower
					# Set the appliance power at this time step

					
				
				else:
					sim_dataP[appliance,iMinute-1] = iStandbyPower
					
					#Get the ten minute period count
					iTenMinuteCount = ((iMinute - 1)/10)
					# Get the number of current active occupants for this minute (convert from 10 minute to 1 minute resolution)
					iActiveOccupants = occ_profile[iTenMinuteCount] 
			
					# If this appliance is off having completed a cycle (ie. a restart delay)
					if (iCycleTimeLeft <= 0) and (iRestartDelayTimeLeft > 0):
						#Decrement the cycle time left
						iRestartDelayTimeLeft = iRestartDelayTimeLeft - 1
										
					# Else if this appliance is off
					elif iCycleTimeLeft <= 0:
						# There must be active occupants, or the profile must not depend on occupancy for a start event to occur
						if (iActiveOccupants > 0 and sUseProfile != "CUSTOM") or (sUseProfile == "LEVEL"):
							# Variable to store the event probability (default to 1)
							dActivityProbability = 1
							# For appliances that depend on activity profiles and is not a custom profile ...
							if (sUseProfile != "LEVEL") and (sUseProfile != "ACTIVE_OCC") and (sUseProfile != "CUSTOM") and (sUseProfile != "ARRIVAL"):
								
								if daytype == 'weekday':
									dayflag = 0
								else:
									dayflag = 1
									
								[activity_days] = [activity_stats[:][x] for x in numpy.where(activity_stats['f0']==dayflag)]
								[activity_occs] = [activity_days[:][x] for x in numpy.where(activity_days['f1']==iActiveOccupants)]
								[activity_use_profile] = [activity_occs[:][x] for x in numpy.where(activity_occs['f2']==sUseProfile)] # sUseProfile = appliances[16] = activity type (string)
								dActivityProbability = activity_use_profile[0][iTenMinuteCount+3] # Get the probability for this activity profile for this time step
									 
									
								# For electric space heaters ... (excluding night storage heaters)
							elif sApplianceType == "ELEC_SPACE_HEATING":
								# If this appliance is an electric space heater, then activity probability is a function of the month of the year
								dActivityProbability = round(oMonthlyRelativeTemperatureModifier[month],4)
									
							# Check the probability of a start event
							if (random() < ((dCalibration) * dActivityProbability)):
								# This is a start event
								[iPower, iCycleTimeLeft,iRestartDelayTimeLeft] = StartAppliance(iRestartDelay, iMeanCycleLength, iCycleTimeLeft,iRatedPower, iStandbyPower, sApplianceType)
							
					
						# Custom appliance handler: storage heaters have a simple representation
						elif sUseProfile == "CUSTOM" and sApplianceType == "STORAGE_HEATER":
											
							# The number of cycles (one per day) set out in the calibration sheet
							# is used to determine whether the storage heater is used
							# This model does not account for the changes in the Economy 7 time
							# It assumes that the time starts at 00:30 each day
							if iTenMinuteCount == 4: 	# ie. 00:30 - 00:40
								#Assume January 14th is the coldest day of the year
								#Dim oDate, oDateOn, oDateOff As Date
								#Dim monthOn, monthOff As Integer
								#oDate = #1/14/1997#

								# Get the month and day when the storage heaters are turned on and off, using the number of cycles per year

								monthOff = (14+(iCyclesPerYear/2))/4.3
								monthOn = (365+14+(0-iCyclesPerYear/2))/4.3

								# If this is a month in which the appliance is turned on of off
								if month == monthOff or month == monthOn:
									# Pick a 50% chance since this month has only a month of year resolution
									dProbability = 0.5 / 10  # (since there are 10 minutes in this period)
								elif month > monthOff and month < monthOn:
									# The appliance is not used in summer
									dProbability = 0
								else:
									# The appliance is used in winter
									dProbability = 1

								# Determine if a start event occurs
								if random() <= dProbability:
									# This is a start event
									[iPower, iCycleTimeLeft,iRestartDelayTimeLeft] = StartAppliance(iRestartDelay, iMeanCycleLength, iCycleTimeLeft,iRatedPower, iStandbyPower, sApplianceType)
												

					else:
						# The appliance is on - if the occupants become inactive, switch off the appliance
						if iActiveOccupants == 0 and sUseProfile != "LEVEL" and sUseProfile != "ACT_LAUNDRY" and sUseProfile != "CUSTOM" and sUseProfile != "ARRIVAL":
							pass
							# Do nothing. The activity will be completed upon the return of the active occupancy.
							# Note that LEVEL means that the appliance use is not related to active occupancy.
							# Note also that laundry appliances do not switch off upon a transition to inactive occupancy.
						else:
							# Set the power
							iPower = GetPowerUsage(iCycleTimeLeft,iRatedPower, iStandbyPower, sApplianceType)
							# Decrement the cycle time left
							iCycleTimeLeft = iCycleTimeLeft - 1

					# get lighting data and add to iPower
					# Set the appliance power at this time step

						sim_dataP[appliance,iMinute-1] = round(iPower,1)
						#sim_dataP[appliance][iMinute-1] = iPower
						if round(appliances_in_dwelling[appliance][23],2) != 1:
							sim_dataQ[appliance][iMinute-1] = round(iPower * math.tan(math.acos(round(appliances_in_dwelling[appliance][23],2))),1)
						else:
							sim_dataQ[appliance][iMinute-1] = 0
					

		
		
			with open('AppProfiles'+idstring+'.dat', 'a') as f:
				writer = csv.writer(f, delimiter =' ',lineterminator='\n')
				writer.writerow([i] + ["P"] + [appliances_in_dwelling[appliance][15]] + sim_dataP[appliance][:].tolist())
				writer.writerow([i] + ["Q"] + [appliances_in_dwelling[appliance][15]] + sim_dataQ[appliance][:].tolist())
				
		sim_data_outputP = numpy.sum(sim_dataP, axis=0)
		sim_data_outputQ = numpy.sum(sim_dataQ, axis=0)

		with open('AppProfiles'+idstring+'.dat', 'a') as f:
			writer = csv.writer(f, delimiter =' ',lineterminator='')
			writer.writerow([i] + ["P"] + ["LIGHTING"] + lighting_demand_data.tolist())
				
		for k in range(1440):
			sim_data_outputP[k] = sim_data_outputP[k] + lighting_demand_data[k]
			sim_data_outputQ[k] = sim_data_outputQ[k] + lighting_demand_data[k]*0.75 
			# note 0.75 factor represents a mean power factor of 0.8 for lighting.
			
		#pprint.pprint("sim_dataP = ")
		#pprint.pprint(sim_data_outputP)
		
		sim_dataP_for_file[i][:] = sim_data_outputP
		sim_dataQ_for_file[i][:] = sim_data_outputQ
		
########################## Un-comment this section to see a plot of each generated profile ########################

		# import matplotlib.pyplot as plt
		# plt.plot(sim_data_outputP)
		# plt.savefig('out_'+idstring+'.png')

###################################################################################################################
		if i==0:
			timet = time.time()-time1
			print 'Approx time to completion = ' + str(timet*n) + ' seconds.'
	# save sim_data to file here
	Pfile = open('Pfile_'+idstring+'.dat', 'w')
	
	numpy.savetxt('Pfile_'+idstring+'.dat',sim_dataP_for_file,fmt="%d", delimiter='\t')
	Pfile.close
	Qfile = file('Qfile_'+idstring+'.dat', 'a')
	numpy.savetxt('Qfile_'+idstring+'.dat',sim_dataQ_for_file,fmt="%d", delimiter='\t')
	Qfile.close
	Occfile = file('Occfile_'+idstring+'.dat', 'a')
	numpy.savetxt('Occfile_'+idstring+'.dat',occ_profile_for_file,fmt="%d", delimiter='\t')
	Occfile.close
	Appliancesfile = file('Appliancesfile_'+idstring+'.dat', 'a')
	#ppliancesfile.writelines(["%s\n" % item for item in appliances_in_dwelling_for_file])
	for item in appliances_in_dwelling_for_file:
		for item in item:
			for item in item:
				Appliancesfile.writelines("%s\t" % item)
		Appliancesfile.write("\n")
	Appliancesfile.close
	timet = time.time()-time1
	print 'Actual time to completion = ' + str(timet) + ' seconds.'	
	

		
def GetPowerUsage(iCycleTimeLeft,iRatedPower, iStandbyPower, sApplianceType):


	# Some appliances have a custom (variable) power profile depending on the time left
	if sApplianceType == "WASHING_MACHINE" or sApplianceType == "WASHER_DRYER":

		# Calculate the washing cycle time
		if (sApplianceType == "WASHING_MACHINE"):
			iTotalCycleTime = 138
		else: # (sApplianceType = "WASHER_DRYER")
			iTotalCycleTime = 198

		# This is an example power profile for an example washing machine
		# This simplistic model is based upon data from personal communication with a major washing maching manufacturer
		if (iTotalCycleTime - iCycleTimeLeft + 1) >=0 and  (iTotalCycleTime - iCycleTimeLeft + 1) <=8:
			return 73         # Start-up and fill
		elif (iTotalCycleTime - iCycleTimeLeft + 1) >=9 and  (iTotalCycleTime - iCycleTimeLeft + 1) <=31:
			return 2056         # Heating
		elif (iTotalCycleTime - iCycleTimeLeft + 1) >=30 and  (iTotalCycleTime - iCycleTimeLeft + 1) <=92:
			return 73         # Wash and drain and spin
		elif (iTotalCycleTime - iCycleTimeLeft + 1) >=93 and  (iTotalCycleTime - iCycleTimeLeft + 1) <=94:
			return 250        # Rinse
		elif (iTotalCycleTime - iCycleTimeLeft + 1) >=95 and  (iTotalCycleTime - iCycleTimeLeft + 1) <=105:
			return 73         # Spin
		elif (iTotalCycleTime - iCycleTimeLeft + 1) >=106 and  (iTotalCycleTime - iCycleTimeLeft + 1) <=107:
			return 250         # Rinse
		elif (iTotalCycleTime - iCycleTimeLeft + 1) >= 108 and  (iTotalCycleTime - iCycleTimeLeft + 1) <= 118:
			return 73         # Spin
		elif (iTotalCycleTime - iCycleTimeLeft + 1) >= 119 and  (iTotalCycleTime - iCycleTimeLeft + 1) <= 120:
			return 250        # Rinse
		elif (iTotalCycleTime - iCycleTimeLeft + 1) >= 121 and  (iTotalCycleTime - iCycleTimeLeft + 1) <= 131:
			return 73         # Spin
		elif (iTotalCycleTime - iCycleTimeLeft + 1) >= 132 and  (iTotalCycleTime - iCycleTimeLeft + 1) <= 133:
			return 250        # Rinse
		elif (iTotalCycleTime - iCycleTimeLeft + 1) >= 134 and  (iTotalCycleTime - iCycleTimeLeft + 1) <= 138:
			return 568        # Fast spin
		elif (iTotalCycleTime - iCycleTimeLeft + 1) >=139 and  (iTotalCycleTime - iCycleTimeLeft + 1) <=198:
			return 2500         # Drying cycle
		else:
			return iStandbyPower
	else: #(appliance is not a washing machine
		# Set the return power to the rated power
		return iRatedPower



		
def StartAppliance(iRestartDelay, iMeanCycleLength, iCycleTimeLeft,iRatedPower, iStandbyPower, sApplianceType):
	
	iCycleTimeLeft = CycleLength(iMeanCycleLength,sApplianceType)
	iRestartDelayTimeLeft = iRestartDelay
	iPower = GetPowerUsage(iCycleTimeLeft,iRatedPower, iStandbyPower, sApplianceType)
	iCycleTimeLeft = iCycleTimeLeft - 1
	return [iPower, iCycleTimeLeft,iRestartDelayTimeLeft]

def CycleLength(iMeanCycleLength,sApplianceType):
	from math import log
	from random import random
	# Use the TV watching length data approximation, derived from the TUS data
	if sApplianceType == "TV1" or sApplianceType == "TV2" or sApplianceType == "TV3":
		# The cycle length is approximated by the following function
		# The avergage viewing time is approximately 73 minutes
		return int(70 * ((0 - log(1 - random()))**1.1))
	elif sApplianceType == "STORAGE_HEATER" or sApplianceType == "ELEC_SPACE_HEATING":
		# Provide some variation on the cycle length of heating appliances
		return GetMonteCarloNormalDistGuess(iMeanCycleLength, iMeanCycleLength/10)
	else:
		return iMeanCycleLength


		
def get_occ_profile(daytype):
	from random import random
	import numpy
	household_size = get_household_size()
	iCurrentState = get_start_state(daytype, household_size)
	# Step 3: Determine the active occupancy transitions for each ten minute period of the day
	tpm = get_transistion_probability_matrix(household_size, daytype)
	occ_sim_data = numpy.zeros([144])
	# work out the transition steps
	for iTimeStep in range(0,143):
		# Get a random number
		fRand = random()
		# Reset the cumulative probability count
		fCumulativeP = 0
		# Cycle through the probabilities for this state
		for i in range(0,7):
			# Add this probability
			fCumulativeP = fCumulativeP + tpm[iTimeStep*7+iCurrentState][i+2] 
			# See if this is a state transition
			if fRand < fCumulativeP:
				# Transition to another or same state
				iCurrentState = i
				# Store the next state
				occ_sim_data[iTimeStep] = iCurrentState
				break
	return occ_sim_data
        

def get_transistion_probability_matrix(household_size, daytype):
	import numpy
    #load tranistion probability matix
	if daytype == "weekday":
		if household_size == 1:
			return numpy.genfromtxt('tpm1_wd.dat',skip_header=22,dtype=(None))
		elif household_size == 2:
			return numpy.genfromtxt('tpm2_wd.dat',skip_header=22,dtype=(None))
		elif household_size == 3:
			return numpy.genfromtxt('tpm3_wd.dat',skip_header=22,dtype=(None))
		elif household_size == 4:
			return numpy.genfromtxt('tpm4_wd.dat',skip_header=22,dtype=(None))
		else:
			return numpy.genfromtxt('tpm5_wd.dat',skip_header=22,dtype=(None))
	else:
		if household_size == 1:
			return numpy.genfromtxt('tpm1_we.dat',skip_header=22,dtype=(None))
		elif household_size == 2:
			return numpy.genfromtxt('tpm2_we.dat',skip_header=22,dtype=(None))
		elif household_size == 3:
			return numpy.genfromtxt('tpm3_we.dat',skip_header=22,dtype=(None))
		elif household_size == 4:
			return numpy.genfromtxt('tpm4_we.dat',skip_header=22,dtype=(None))
		else:
			return numpy.genfromtxt('tpm5_we.dat',skip_header=22,dtype=(None))
 
	
def get_start_state(daytype,household_size):
	from random import random
	import numpy 

	
	if daytype == 'weekday':
		start_states = numpy.genfromtxt('weekday_start_states.dat',skip_header=21,dtype=(None))
	else:
		start_states = numpy.genfromtxt('weekend_start_states.dat',skip_header=21,dtype=(None))
		

	# Pick a random number to determine the start state
	fRand = random()
	iCurrentstate = 0
	# Reset the cumulative probability count
	fCumulativeP = 0
	# Determine the start state at time 00:00 by checking the random number against the distribution
	for iCurrentState in range(0,6):
		# Add the probability for this number of active occupants
		fCumulativeP = fCumulativeP + start_states[iCurrentstate][household_size-1] 
		if fRand <= fCumulativeP:
			# This is the start state
			return iCurrentState

			
def get_household_size():
	# # returns randomly generated household size based on ONS statistics
	# # Distribution of household sizes in the UK – based on data from Office National Statistics for 2011
	# # Ref - Office for National Statistics UK, “Families and households, 2001 to 2011 - Data Set - Table 5.” [Online]. Available: bit.ly/KQQB58. [Accessed: 27-Feb-2012].
	from random import random
	randno = random()
	if randno < 0.294:
		return 1
	elif randno < 0.640:
		return 2
	elif randno < 0.800:
		return 3
	elif randno < 0.932:
		return 4
	else:
		return 5
	
	
def gettemperaturedata():
	# Data derived from MetOffice temperature data for the Midlands in 2007 (http://www.metoffice.gov.uk/climate/uk/2007/) Crown Copyright
	return numpy.array([0, 1.63, 1.821, 1.595, 0.867, 0.763, 0.191, 0.156, 0.087, 0.399, 0.936, 1.561, 1.994])

def ConfigureAppliancesInDwelling(appliances):
	from random import random
	appliances_to_remove = []
	appliances_in_dwelling = appliances
	# For each appliance
	for i in range(0,33):
		# Get a random number
		dRan = random()
		# Get the proportion of houses with this appliance
		dProportion = round(appliances[i][0],3)
		# Determine if this simulated house has this appliance
		if dRan > dProportion:
			appliances_to_remove.append(i)
	appliances_in_dwelling = numpy.delete(appliances_in_dwelling,appliances_to_remove,0)
	return appliances_in_dwelling
	
	
def GetMonteCarloNormalDistGuess(dMean, dSD):
	from random import random
	from math import exp
    # Guess a value from a normal distribution for a given mean and standard deviation

	if dMean == 0:
		return 0
	while 1:
		# Guess a value
		iGuess = (random() * (dSD * 8)) - (dSD * 4) + dMean
		# See if this is likely
		px = (1 / (dSD * ((2 * 3.14159) ** 0.5))) * exp(-((iGuess - dMean) ** 2) / (2 * dSD * dSD))
		# End the loop if this value is okay
		if (px >= random()):
			return iGuess

def RunLightingSimulation(month,occ_profile):
	from random import randint 
	from random import random
	import math
	import numpy
	Ext_ext_glob_irr_threshold_mean = 60 # House external global irradiance threshold mean [W/m^2]
	Ext_ext_glob_irr_threshold_sd = 10 # House external global irradiance threshold standard deviation [W/m^2]
	# Determine the irradiance threshold of this house
	iIrradianceThreshold = GetMonteCarloNormalDistGuess(Ext_ext_glob_irr_threshold_mean, Ext_ext_glob_irr_threshold_sd)
	# Choose a random house from the list of 100 provided in the bulbs sheet
	iRandomHouse = randint(0,99)

	bulbs = numpy.genfromtxt('bulbs.dat',skip_header=14,delimiter='\t',missing_values="",filling_values="0",dtype=(None))
	# Get the bulb data
	vBulbArray = bulbs[iRandomHouse][:]
	# Get the number of bulbs
	iNumBulbs = vBulbArray[1]
	# Declare an array to store the simulation data
	lighting_demand_data = numpy.zeros([iNumBulbs,1440])
	
	# Load the irradiance array
	vIrradianceArray = numpy.genfromtxt('irradiance.dat',skip_header=25,usecols=month-1,dtype=(None))

	#This calibration scaler is used to calibrate the model to so that it provides a particular average output over a large number of runs.
	fCalibrationScalar = 0.00815368639667705
	
	# For each bulb
	for i in range(2,iNumBulbs):
		
		# Get the bulb rating
		iRating = vBulbArray[i]
	
		# Assign a random bulb use weighting to this bulb
		# Note that the calibration scalar is multiplied here to save processing time later
		fCalibratedRelativeUseWeighting = -fCalibrationScalar * math.log(random())
		#vSimulationArray(3, i) = fCalibratedRelativeUseWeighting
		
		# Calculate the bulb usage at each minute of the day
		iTime = 1
		while (iTime <= 1440):
		
			# Is this bulb switched on to start with?
			# This concept is not implemented in this example.
			# The simplified assumption is that all bulbs are off to start with.
			
			# Get the irradiance for this minute
			iIrradiance = vIrradianceArray[iTime-1]
			
			# Get the number of current active occupants for this minute
			# Convert from 10 minute to 1 minute resolution
			iActiveOccupants = occ_profile[((iTime)/10)-1]
			# Determine if the bulb switch-on condition is passed
			# ie. Insuffient irradiance and at least one active occupant
			# There is a 5% chance of switch on event if the irradiance is above the threshold
			bLowIrradiance = ((iIrradiance < iIrradianceThreshold) or (random() < 0.05))

			# Effective occupancy represents the sharing of light use.
			# Derived from; U.S. Department of Energy, Energy Information Administration, 1993 Residential Energy Consumption Survey,
			# Mean Annual Electricity Consumption for Lighting, by Family Income by Number of Household Members
			fEffectiveOccupancyArray = numpy.array([0.0,1.0,1.528,1.694,1.983,2.094])
			# Get the effective occupancy for this number of active occupants to allow for sharing
			fEffectiveOccupancy = fEffectiveOccupancyArray[iActiveOccupants]
			iLightDuration =0
			# Check the probability of a switch on at this time
			if (bLowIrradiance and (random() < (fEffectiveOccupancy * fCalibratedRelativeUseWeighting))):
				# This is a switch on event
				# Determine how long this bulb is on for
				r1 = random()
				
				# below taken from the lighting event duration model on the CREST model light_config tab
				# This model defines how long a bulb will stay on for, if a switch-on event occurs.
				# Original source: M. Stokes, M. Rylatt, K. Lomas, A simple model of domestic lighting demand, Energy and Buildings 36 (2004) 103-116
				event_duration_lower_values = numpy.array([1,2,3,5,9,17,28,50,92])	
				# taken from  CREST model light_config tab (cells C55:E63) 
				event_duration_upper_values = numpy.array([1,2,4,8,16,27,49,91,259])
				# taken from CREST model light_config tab (cells D55:E63) 
    
				for j in range(1,9):
				
					# Get the cumulative probability of this duration
					cml = j/9.0 # Note default settings in CREST model light_config tab (cells E55:E63) have this relation 
				
					# Check to see if this is the type of light
					if r1 < cml:
                    
						# Get the durations
						iLowerDuration = event_duration_lower_values[j-1]
						iUpperDuration = event_duration_upper_values[j-1]
						
						# Get another random number
						r2 = random()
						
						# Guess a duration in this range
						iLightDuration = int((r2 * (iUpperDuration - iLowerDuration)) + iLowerDuration)
												  
						# Exit the loop
						break
#
				for j in range(1,iLightDuration):
                
					# Range check
					if iTime > 1440:
						break
                    
					# Get the number of current active occupants for this minute
					iActiveOccupants = occ_profile[((iTime - 1)/10)]
					
					# If there are no active occupants, turn off the light
					if iActiveOccupants == 0:
						break
                    
					# Store the demand
					lighting_demand_data[i,iTime] = iRating
                        
					# Increment the time
					iTime = iTime + 1

			else:
				# The bulb remains off
				lighting_demand_data[i,iTime-1] =  0
				
				# Increment the time
				iTime = iTime + 1

    
	# return the simulation data to the sheet
	return numpy.sum(lighting_demand_data, axis=0)


