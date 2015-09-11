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

License:

   Copyright (C) 2008, 2011 Ian Richardson*, Murray Thomson*, 2013 Lee Thomas**

   *CREST (Centre for Renewable Energy Systems Technology),
   Department of Electronic and Electrical Engineering
   Loughborough University, Leicestershire LE11 3TU, UK
   Tel. +44 1509 635326. Email address: I.W.Richardson@lboro.ac.uk

   ** Institute of Energy, 
   Cardiff School of Engineering
   Cardiff University, CF24 3AA
   Tel. +442920870674. Email address: ThomasL62@cf.ac.uk
   http://energy.engineering.cf.ac.uk/

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, either version 3 of the License, or
   (at your option) any later version.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>.
