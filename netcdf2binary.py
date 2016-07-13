#!/usr/bin/python
#
#  This program converts a variable in NetCDF format to binary individual files
#  one for each time frame
#  It requires the program ncdump to export a single variable into ASCII CSV format, 
#  and the program uses the unix pipeline to avoid creating large temporary files. 
#  Make sure you have ncdump in your path.
#
#  Syntax:
#
#  ncdump -v variable NetCDFfile.nc  |  netcdf2bin.py
#
#  where variable is what you want to export to Blender voxels
#
#
import struct;
import math;
import sys;
import array;
from optparse import OptionParser;


usage = "Convert output from ncdump (NetCDF)) to raw binary.\n  syntax: ncdump -v var file.nc | netcdf2bin.py [options]";
parser = OptionParser(usage=usage);

parser.add_option("-V","--verbose",action="store_true", 
    dest="Verbose",default=False, 
    help="Switch on verbose mode.");
parser.add_option("-x","--xlength",type="int",action="store", dest="Xres",default=50, 
    help="X lenght of the data.");
parser.add_option("-y","--ylength",type="int",action="store", dest="Yres",default=50, 
    help="Y lenght of the data.");
parser.add_option("-z","--zlength",type="int",action="store", dest="Zres",default=50, 
    help="Z lenght of the data.");
parser.add_option("-t", "--times", type="int", action="store", dest="Times", default = 1,
    help="Number of frames to process.");
parser.add_option("-f", "--file", action="store", dest="Filename", default = "out.XXXXX",
    help="Output file name.");
parser.add_option("-m", "--min", action="store", dest="minvalue", type="float", default = 0.0,
    help="Minimum data value to output as zero.");
parser.add_option("-M", "--max", action="store", dest="maxvalue", type="float", default = 0.0, 
    help="Maximum data value to output as one");    
parser.add_option("-s", "--scale", action="store", dest="ScaleFactor", type="float", default = 1.0, 
    help="Scale Data by Factor");    
    
# Parse arguments
(options, args) = parser.parse_args();

times = options.Times
xres = options.Xres;
yres = options.Yres;
zres = options.Zres;
Verbose = options.Verbose
MinValue = options.minvalue;
MaxValue = options.maxvalue;
filename = options.Filename
scalefactor = options.ScaleFactor;

if (MinValue != MaxValue):
    def Normalize(val):
        return max ( min( 1.0, (val-MinValue)/(MaxValue-MinValue) ) , 0.0)
else:
    def Normalize(val):
        return val

# In this function one must define any change of scales (linear to log or whatever)
def scale(x):
    return scalefactor*x;

TotalDataToRead = xres*yres*zres*times;
TotalDataRead = 0;
ChunkSize = xres*yres*zres;
AccumulatedRead = 0;
ChunksRead = 0;

MinValueFound = 1.0E100;
MaxValueFound = -1.0E100;

if Verbose:
    print("Out as "+filename);
    print("x as "+str(xres));
    print("y as "+str(yres));
    print("z as "+str(zres));
    print("T as "+str(times));
    if (MinValue != MaxValue):
        print("min as "+str(MinValue));
        print("Max as "+str(MaxValue));

#skip the ncdump header
line = sys.stdin.readline();
while (line.find("data:") == -1) :
    line = sys.stdin.readline();
line = sys.stdin.readline();
line = sys.stdin.readline();


fil = open(filename+"."+str(ChunksRead).zfill(5),'wb')
for line in sys.stdin:
    linedata = line.split(',');
    prepareddata = array.array('f');
    for Strnumber in linedata:
        #We need to check for the final ";" in the data
        if Strnumber.find(";") > -1:
            Strnumber = Strnumber.replace(";","");
        try:
            RawData = scale(float(Strnumber.strip()));
            NormalizedValue = Normalize(RawData)
            prepareddata.append(NormalizedValue);
            #if Verbose: print(str(RawData)+" converted to "+str(NormalizedValue));
            TotalDataRead = TotalDataRead + 1;
            AccumulatedRead = AccumulatedRead +1;
            if (AccumulatedRead == ChunkSize): #We should finish up the frame
                prepareddata.tofile(fil);
                fil.flush();
                fil.close();
                ChunksRead = ChunksRead + 1;
                AccumulatedRead = 0;
                prepareddata = array.array('f');
                fil = open(filename+"."+str(ChunksRead).zfill(5),'wb')
            if ((100*TotalDataRead) % TotalDataToRead==0): 
                print(str((100.0*TotalDataRead)/TotalDataToRead)+" % done")
            MinValueFound = min (MinValueFound, RawData);
            MaxValueFound = max (MaxValueFound, RawData);
            if (TotalDataRead == TotalDataToRead):
                break;
        except:
            continue;
    if (len(prepareddata)>0):
        prepareddata.tofile(fil);
    if (TotalDataRead == TotalDataToRead):                
        break;

fil.flush();
fil.close();

print "Maximum Value Found :"+str(MaxValueFound);
print "Minimum Value Found :"+str(MinValueFound);
if (MaxValue != MinValue):
    print " but wrote in the range "+str(MinValue)+"--"+str(MaxValue);

if ( TotalDataToRead != TotalDataRead):
    print "Some error occurred, expected "+str(TotalDataToRead)+" points and found "+str(TotalDataRead);
