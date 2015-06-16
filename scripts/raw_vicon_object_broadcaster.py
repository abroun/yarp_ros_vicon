#! /usr/bin/env python

#-------------------------------------------------------------------------------
# Gets data about an object from the Vicon system and broadcasts it
# to the tf system
#-------------------------------------------------------------------------------

# ROS imports
import roslib
roslib.load_manifest( 'yarp_ros_vicon' )
import rospy
import tf

import yarp
import math

#-------------------------------------------------------------------------------
class DataProcessor( yarp.PortReader ):
    
    #---------------------------------------------------------------------------     
    def __init__( self, callback ):

        yarp.PortReader.__init__( self )
        self.callback = callback
    
    #---------------------------------------------------------------------------
    def read( self, connection ):
        
        if not connection.isValid():
            print "Connection shutting down"
            return True

        bottleIn = yarp.Bottle()
        ok = bottleIn.read( connection )
        if not ok:
            print "Failed to read input"
            return False

        self.callback( bottleIn.toString() )

        return True

#-------------------------------------------------------------------------------
class Descriptor:
    
    def __init__( self, fieldString ):
        
        self.fieldString = fieldString
        self.idx = -1

#-------------------------------------------------------------------------------
class ViconBroadcaster:
    
    VICON_FRAME_ID = "vicon"
    TABLE_FRAME_ID = "table_link"

    VICON_IN_TABLE_SPACE_POS = [ 0.317, 0.0, 0.0 ]
    VICON_IN_TABLE_SPACE_ROT = [ 0.0, 0.0, 0.0 ]    # X, Y, and Z angle
    
    BASE_YARP_NAMESPACE = "/ViconROS"
    
    DESCRIPTOR_SERVER_NAME = "/Vicon/Rpobjects/Descriptors:o"
    DESCRIPTOR_CLIENT_NAME = BASE_YARP_NAMESPACE + "/ObjectDescriptors:o"
    DATA_SERVER_NAME = "/Vicon/Rpobjects/Data:o"
    DATA_CLIENT_NAME = BASE_YARP_NAMESPACE + "/ObjectData:o"
    
    #---------------------------------------------------------------------------
    def __init__( self ):
        
        self.objectDescriptorsDict = {}
        
        self.desctiptorDict = { 
            "x" : Descriptor( "<t-X>" ),
            "y" : Descriptor( "<t-Y>" ),
            "z" : Descriptor( "<t-Z>" ),
            "rotX" : Descriptor( "<e-X>" ),
            "rotY" : Descriptor( "<e-Y>" ),
            "rotZ" : Descriptor( "<e-Z>" ) }
        
        # Connect to ROS
        rospy.init_node( 'ViconObjectBroadcaster', anonymous=True )
        self.transformBroadcaster = tf.TransformBroadcaster()
        
        # Connect to the YARP server
        self.yarpNetwork = yarp.Network()
        self.descriptorPort = yarp.Port()
        self.descriptorProcessor = DataProcessor( self.onNewDescriptorMsg )
        self.descriptorPort.setReader( self.descriptorProcessor ) 
        
        self.dataPort = yarp.Port()
        self.dataProcessor = DataProcessor( self.onNewDataMsg )
        self.dataPort.setReader( self.dataProcessor ) 
        
        if not self.descriptorPort.open( self.DESCRIPTOR_CLIENT_NAME ):
            raise Exception( "Unable to open port for getting descriptors" )
        
        if not self.yarpNetwork.connect( self.DESCRIPTOR_SERVER_NAME, self.DESCRIPTOR_CLIENT_NAME ):
            raise Exception( "Unable connect to the {0} port".format( self.DESCRIPTOR_SERVER_NAME ) )
        
        if not self.dataPort.open( self.DATA_CLIENT_NAME ):
            raise Exception( "Unable to open port for getting data" )
        
        if not self.yarpNetwork.connect( self.DATA_SERVER_NAME, self.DATA_CLIENT_NAME ):
            raise Exception( "Unable connect to the {0} port".format( self.DATA_SERVER_NAME ) )
        
        print "Connected..."
        
    #---------------------------------------------------------------------------
    def shutdown( self ):
        
        if self.dataPort != None:
            self.dataPort.close()
            self.dataPort = None
        
        if self.descriptorPort != None:
            self.descriptorPort.close()
            self.descriptorPort = None
        
        if self.yarpNetwork != None:
            self.yarpNetwork.fini()
            self.yarpNetwork = None
    
    #---------------------------------------------------------------------------
    def onNewDescriptorMsg( self, msg ):
        
        # Extract indices for object from the descriptor
        descriptorStrings = msg.split( " " )
        
        for i, descriptorString in enumerate( descriptorStrings ):
            
            descriptorString = descriptorString.strip( '"' )
            descriptorData = descriptorString.split( ":" )
            if len( descriptorData ) >= 3:
                
                objectName = descriptorData[ 1 ]
                fieldName = descriptorData[ 2 ]
                
                if objectName in self.objectDescriptorsDict:
                    
                    objectDescriptors = self.objectDescriptorsDict[ objectName ]
                    
                else:
                    
                    objectDescriptors = { 
                        "x" : Descriptor( "<t-X>" ),
                        "y" : Descriptor( "<t-Y>" ),
                        "z" : Descriptor( "<t-Z>" ),
                        "rotX" : Descriptor( "<e-X>" ),
                        "rotY" : Descriptor( "<e-Y>" ),
                        "rotZ" : Descriptor( "<e-Z>" ) }
                    self.objectDescriptorsDict[ objectName ] = objectDescriptors
            
                # Check to see if the fieldName string matches a descriptor
                for descriptor in objectDescriptors.values():
                    
                    if fieldName == descriptor.fieldString:
                        descriptor.idx = i
                        break
    
    #---------------------------------------------------------------------------
    def onNewDataMsg( self, msg ):
        
        dataStrings = msg.split( " " )
        
        for objectName in self.objectDescriptorsDict:

            objectDescriptors = self.objectDescriptorsDict[ objectName ]
            
            # Check that we got all indices for the object
            allIndicesFound = True
            for descriptor in objectDescriptors.values(): 
                if descriptor.idx < 0:
                    allIndicesFound = False
                    break
            
            if not allIndicesFound:
                print "Warning: Can't get all indices for", objectName
            else:
                
                x = float( dataStrings[ objectDescriptors[ "x" ].idx ] )/1000.0
                y = float( dataStrings[ objectDescriptors[ "y" ].idx ] )/1000.0
                z = float( dataStrings[ objectDescriptors[ "z" ].idx ] )/1000.0
                
                rotX = float( dataStrings[ objectDescriptors[ "rotX" ].idx ] )
                rotY = float( dataStrings[ objectDescriptors[ "rotY" ].idx ] )
                rotZ = float( dataStrings[ objectDescriptors[ "rotZ" ].idx ] )
                
                self.transformBroadcaster.sendTransform( ( x, y, z ), 
                    tf.transformations.quaternion_from_euler( rotX, rotY, rotZ ),
                    rospy.Time.now(), child="vicon_" + objectName, parent=self.VICON_FRAME_ID )
                    
        # Broadcast the transform from the TABLE_FRAME_ID to VICON_FRAME_ID
        self.transformBroadcaster.sendTransform( self.VICON_IN_TABLE_SPACE_POS, 
            tf.transformations.quaternion_from_euler( 
                self.VICON_IN_TABLE_SPACE_ROT[ 0 ],
                self.VICON_IN_TABLE_SPACE_ROT[ 1 ],
                self.VICON_IN_TABLE_SPACE_ROT[ 2 ] ),
            rospy.Time.now(), child=self.VICON_FRAME_ID, parent=self.TABLE_FRAME_ID )

#-------------------------------------------------------------------------------
if __name__ == "__main__":
    
    broadcaster = ViconBroadcaster()
    
    hz = rospy.get_param( "rate", 100 ) # 100hz
    r = rospy.Rate( hz ) 
    
    while not rospy.is_shutdown():
        r.sleep()
    
    broadcaster.shutdown()
    