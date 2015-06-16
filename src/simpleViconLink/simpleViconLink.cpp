#include <stdio.h>
#include "nexusAPI.h"

#include <yarp/os/all.h>

#include <windows.h>

//--------------------------------------------------------------------------------------------------
CNexusAPI gNexusAPI;
yarp::os::Network gYarpNetwork;
yarp::os::Port gDescriptorsPort;
yarp::os::Port gDataPort;

//--------------------------------------------------------------------------------------------------
void shutdown()
{
    //printf( "Disconnecting...\n" );
    //gNexusAPI.Disconnect();
}

//--------------------------------------------------------------------------------------------------
void shutdownProgramWithPause( int exitCode )
{
    printf( "\n\nPress any key to exit\n" );
    getchar();
    exit( exitCode );
}

//--------------------------------------------------------------------------------------------------
int main( char argc, char** argv )
{
    printf( "Trying to connect to Vicon...\n" );
    if ( gNexusAPI.Connect() != IS_OK )
    {
        printf( "Error: Unable to connect to Vicon system\n" );
        printf( "Please first try restarting this program. If that doesn't work then restart\n" );
        printf( "Vicon Tracker, let it start to track objects, and then run this program twice\n" );
        printf( "(the first attempt at connection will fail...)\n" );
        
        shutdownProgramWithPause( -1 );
    }
 
    printf( "Connected to Vicon\n" );
    atexit( shutdown );
    
    if ( !gDescriptorsPort.open( "/Vicon/Rpobjects/Descriptors:o" ) )
    {
        printf( "Error: Unable to create descriptors Yarp port\n" );
        shutdownProgramWithPause( -1 );
    }
    
    if ( !gDataPort.open( "/Vicon/Rpobjects/Data:o" ) )
    {
        printf( "Error: Unable to create data Yarp port\n" );
        shutdownProgramWithPause( -1 );
    }
    
    while ( true )
    {
        gNexusAPI.UpdateChannelData();
        
        int numBodies;
        gNexusAPI.GetNumBodies( numBodies );
        printf( "%i bodies\n", numBodies );
        
        // Send descriptors and data to Yarp
        yarp::os::Bottle descriptorOutput;
        descriptorOutput.clear();
        
        yarp::os::Bottle dataOutput;
        dataOutput.clear();
        
        for ( int bodyIdx = 0; bodyIdx < numBodies; bodyIdx++ )
        {
            const BodyData& bodyData = gNexusAPI.GetBodyData( bodyIdx );
                        
            std::string data = bodyData.mBodyName + std::string( ":<t-X>" );
            descriptorOutput.addString( data.c_str() );
            data = bodyData.mBodyName + std::string( ":<t-Y>" );
            descriptorOutput.addString( data.c_str()  );
            data = bodyData.mBodyName + std::string( ":<t-Z>" );
            descriptorOutput.addString( data.c_str()  );
            data = bodyData.mBodyName + std::string( ":<e-X>" );
            descriptorOutput.addString( data.c_str()  );
            data = bodyData.mBodyName + std::string( ":<e-Y>" );
            descriptorOutput.addString( data.c_str()  );
            data = bodyData.mBodyName + std::string( ":<e-Z>" );
            descriptorOutput.addString( data.c_str()  );            
        
            printf( "Body %i: %s\n", bodyIdx, bodyData.mBodyName.c_str() );
            printf( "Pos: %2.3f %2.3f %2.3f\n", bodyData.mtX, bodyData.mtY, bodyData.mtZ );
            printf( "Rot: %2.3f %2.3f %2.3f\n", bodyData.meX, bodyData.meY, bodyData.meZ );
            
            
            dataOutput.addDouble( bodyData.mtX );
            dataOutput.addDouble( bodyData.mtY );
            dataOutput.addDouble( bodyData.mtZ );
            dataOutput.addDouble( bodyData.meX );
            dataOutput.addDouble( bodyData.meY );
            dataOutput.addDouble( bodyData.meZ );
            
        }
        
        gDescriptorsPort.write( descriptorOutput );
        gDataPort.write( dataOutput );
        
        Sleep( 100 );
    }
    
    

    return 0;
}