# pyCREST
A python implementation of the CREST demand model [1][2] - adapted for the creation of multiple profiles.

The program has been adapted for the creation of a population of demand profiles.The distribution of household sizes is based on the UK census [3]. The model was also adapted so that it 'pre-runs' for the 198 minutes before minute 0. This is to allow for the potential starting of washing machines and other long cycle appliances during this time.

To use it, download all the files into a working directory and in python:

    import pyCREST as cr
    cr.create_profiles(n=10,daytype='weekend',month=1) 

This will create 10 profiles for weekend daytype in month 1. The information is stored in newly created dat (ascii tab delimited) files with an ID string based on the number of profiles created, the daytype and the month. dat files are created for Active Power, Reactive Power, Active occupancy, appliances and Individual appliance profiles. For the above example, the following files will be created:

    Appliancesfile_2x_month-1_daytype-weekend.dat
    AppProfiles2x_month-1_daytype-weekend.dat
    Occfile_2x_month-1_daytype-weekend.dat
    Pfile_2x_month-1_daytype-weekend.dat
    Qfile_2x_month-1_daytype-weekend.dat


[1] I. Richardson, M. Thomson, D. Infield, and C. Clifford, “Domestic electricity use: A high-resolution energy demand model,” Energy Build., vol. 42, no. 10, pp. 1878–1887, Oct. 2010.

[2] I. Richardson, M. Thomson, and D. Infield, “A high-resolution domestic building occupancy model for energy demand simulations,” Energy Build., vol. 40, no. 8, pp. 1560–1566, Jan. 2008.

[3] Office for National Statistics UK, “Families and households, 2001 to 2011 - Data Set - Table 5.” [Online]. Available: bit.ly/KQQB58. [Accessed: 27-Feb-2012]
