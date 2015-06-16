This is a rather convoluted way of getting a VICON system to work with either ROS or YARP. Things could be simplified but instead things have been patched together quickly from an existing running system.

The basic outline of the system is

* You have a VICON system running on Windows
* A windows program called simpleViconLink talks to VICON via the VICON Nexus API and streams data to a YARP server
* The ROS node yarp_ros_vicon talks to the YARP server, and translates the VICON data to ROS by writing transforms to the tf system

If this seems a bit yucky to you, then please use any useful bits here to write a better system, or ignore it completely. There were 'reasons' why things were done as they were, which may, or may not have been reasonable reasons.

# Installation

* Assuming that VICON, specifically Vicon Tracker is installed on your Windows PC
* Sync a copy of this repository to the Windows PC
* Build src/simpleViconLink using Visual Studio
* Install YARP on the Windows PC if needed (instructions [here](http://wiki.icub.org/yarp/specs/dox/user/html/install_yarp_windows.html))
* Install YARP on the Linux ROS PC, instruction in the YARP Installation section below
* Run a YARP server on the ROS PC using

```
yarp server
```

* Tell the Windows PC where the YARP server is by running the following on the command line

```
yarp conf YARP_SERVER_IP_ADDRESS 10000
```

* Run Vicon Tracker on the Windows PC
* Run simpleViconLink on the Windows PC.
* Things may crash as the Nexus API seems to be a bit flaky when it comes to initial connections. Follow the troubleshooting instructions given by simpleViconLink
* On the ROS PC run

```
rosrun yarp_ros_vicon raw_vicon_object_broadcaster.py
```

* If you open up RVIZ, you should be able to see VICON transforms in the vicon tf frame
* Edit raw_vicon_object_broadcaster.py to set the relative pose of your base tf link (in our case it was table_link). Ideally this would be set by a command line parameter.

# YARP Installation

Detailed installation instructions for YARP can be found on the [YARP website](http://eris.liralab.it/yarp/), but the important steps for Ubuntu are as follows.

Open up a terminal window and run the following commands

```
sudo apt-get install cmake libace-dev git python-dev swig
git clone git://github.com/robotology/yarp.git
cd yarp
git checkout v2.3.63
mkdir build
cd build
cmake ..
make
sudo make install
sudo ldconfig
```

## Installing the YARP Python Bindings

We have now installed the main set of YARP tools and libraries. We also need to install the YARP Python bindings as a number of programs make use of these to talk to YARP. Run the following commands in a terminal window

```
cd yarp/bindings
mkdir build
cd build
cmake -D CREATE_PYTHON=ON ..
make
sudo make install
```

## Telling YARP about an existing YARP Network

We need to tell the local YARP installation the IP address and network port of the YARP server. You can do this by running

```
yarp conf SERVER_IP_ADDRESS SERVER_PORT
```

Then run

```
yarp name list
```

in a terminal window on your machine. If successful you should see a list of the active YARP ports.




