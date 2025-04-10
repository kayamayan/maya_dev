# Copyright Epic Games, Inc. All Rights Reserved.
import unreal
from datetime import datetime

# This example is an implementation of an "executor" which is responsible for
# deciding how a queue is rendered, giving you complete control over the before,
# during, and after of each render. 
#
# This class is an example of how to make an executor which processes a job in a standalone executable launched with "-game".
# You can follow this example to either do a simple integration (read arguments from the command line as suggested here),
# or it can used to implement an advanced plugin which opens a socket or makes REST requests to a server to find out what
# work it should do, such as for a render farm implementation.
#
# We're building a UClass implementation in Python. This allows the Python to
# integrate into the system in a much more intuitive way but comes with some 
# restrictions: 
# Python classes cannot be serialized. This is okay for executors because they are
#   created for each run and are not saved into assets, but means that you cannot
#   implement a settings class as those do need to get saved into preset assets.
# All class properties must be UProperties. This means you cannot use native
#   Python sockets.
#
# This class must inherit from unreal.MoviePipelinePythonHostExecutor. This class also
# provides some basic socket and async http request functionality as a workaround for no
# native Python member variables.
#
# If you are trying to write your own executor based on this example, you will need to create
# a /Content/Python folder and place the custom python file within that folder. Then you will need
# to create an "init_unreal.py" file within that folder and add "import <YourPyModuleName>" to it
# so that Unreal will attempt to parse the class on engine load and it can be spawned by MRQ.
# If your Python file is named MyExecutorWithExtraFeatures.py, then you would add
#
# import MyExecutorWithExtraFeatures
#
# to your init_unreal.py file. 
#
# REQUIREMENTS:
#    Requires the "Python Editor Script Plugin" to be enabled in your project.
#
# USAGE:
#   Use the following command line argument to launch this:
#   UnrealEditor-Cmd.exe <path_to_uproject> <map_name> -game -MoviePipelineLocalExecutorClass=/Script/MovieRenderPipelineCore.MoviePipelinePythonHostExecutor -ExecutorPythonClass=/Engine/PythonTypes.MoviePipelineExampleRuntimeExecutor -LevelSequence=<path_to_level_sequence> -windowed -resx=1280 -resy=720 -log
#   ie:
#   UnrealEditor-Cmd.exe "E:\SubwaySequencer\SubwaySequencer.uproject" subwaySequencer_P -game -MoviePipelineLocalExecutorClass=/Script/MovieRenderPipelineCore.MoviePipelinePythonHostExecutor -ExecutorPythonClass=/Engine/PythonTypes.MoviePipelineExampleRuntimeExecutor -LevelSequence="/Game/Sequencer/SubwaySequencerMASTER.SubwaySequencerMASTER" -windowed -resx=1280 -resy=720 -log
#
# If you are looking for how to render in-editor using Python, see the MoviePipelineEditorExample.py script instead.
@unreal.uclass()
class CinemaMPRExecutor(unreal.MoviePipelinePythonHostExecutor):
    
    # Declare the properties of the class here. You can use basic
    # Python types (int, str, bool) as well as unreal properties.
    # You can use Arrays and Maps (Dictionaries) as well
    activeMoviePipeline = unreal.uproperty(unreal.MoviePipeline)
    exampleArray = unreal.Array(str) # An array of strings
    exampleDict = unreal.Map(str, bool) # A dictionary of strings to bools.
    
    # Constructor that gets called when created either via C++ or Python
    # Note that this is different than the standard __init__ function of Python
    def _post_init(self):
        # Assign default values to properties in the constructor
        self.activeMoviePipeline = None
        
        self.exampleArray.append("Example String")
        self.exampleDict["ExampleKey"] = True
        
        # Register a listener for socket messages and http messages (unused in this example
        # but shown here as an example)
        self.socket_message_recieved_delegate.add_function_unique(self, "on_socket_message");
        self.http_response_recieved_delegate.add_function_unique(self, "on_http_response_recieved")


    # We can override specific UFunctions declared on the base class with
    # this markup.
    @unreal.ufunction(override=True)
    def execute_delayed(self, inPipelineQueue):
        # This function is called once  the map has finished loading and the 
        # executor is instantiated. If you needed to retrieve data from some
        # other system via a REST api or Socket connection you could do that here.
        for x in range(0, 25):
            unreal.log_error("This script is meant as an example to build your own and is not meant to be run on its own. Please read the source code (/Engine/Plugins/MovieScene/MovieRenderPipeline/Content/Python/MoviePipelineExampleRuntimeExecutor.py) for details on how to make your own. This example automatically overrides various settings on jobs to serve as an example for how to do that in your own script if needed.")
            
        # If your executor needs to make async HTTP calls (such as fetching the value from a third party management library)
        # you can do that with the following code:
        
        # newIndex is a unique index for each send_http_request call that you can store
        # and retrieve in the on_http_response_recieved function to match the return back
        # up to the original intent.
        # newIndex = self.send_http_request("https://google.com", "GET", "", unreal.Map(str, str))
        
        # If your executor wants to make TCP socket connections to send data back and forth with a third party software,
        # you can do that with the following code:
        # Here's an example of how to open a TCP socket connection. This example
        # doesn't need one, but is shown here in the event you wish to build a more
        # in depth integration into render farm software.
        #socketConnected = self.connect_socket("127.0.0.1", 6783)
        #if socketConnected == True:
        #    # Send back a polite hello world message! It will be sent over the socket
        #    # with a 4 byte size prefix so you know how many bytes to expect before
        #    # the message is complete.
        #    self.send_socket_message("Hello World!")
        #else:
        #    unreal.log_warning("This is an example warning for when a socket fails to connect.")
            
        
        # Here's how we can scan the command line for any additional args such as the path to a level sequence.
        (cmdTokens, cmdSwitches, cmdParameters) = unreal.SystemLibrary.parse_command_line(unreal.SystemLibrary.get_command_line())
        levelSequencePath = None
        try:
            levelSequencePath = cmdParameters['LevelSequence']
        except:
            unreal.log_error("Missing '-LevelSequence=/Game/Foo/MySequence.MySequence' argument")
            self.on_executor_errored()
            return
            
        # A movie pipeline needs to be initialized with a job, and a job
        # should be owned by a Queue so we will construct a queue, make one job
        # and then configure the settings on the job. If you want inPipelineQueue to be
        # valid, then you must pass a path to a queue asset via -MoviePipelineConfig. Here
        # we just make one from scratch with the one level sequence as we didn't implement
        # multi-job handling.
        self.pipelineQueue = unreal.new_object(unreal.MoviePipelineQueue, outer=self);
        unreal.log("Building Queue...")
        
        render_resx = 1920
        render_resy = 1080
        try:
            render_resx = int(cmdParameters['RenderResX'])
            render_resy = int(cmdParameters['RenderResY'])
        except:
            unreal.log_error("Missing '-RenderResX, RenderResY' argument")

        # Allocate a job. Jobs hold which sequence to render and what settings to render with.
        newJob = self.pipelineQueue.allocate_new_job(unreal.MoviePipelineExecutorJob)
        newJob.sequence = unreal.SoftObjectPath(levelSequencePath)

        newJob.author = 'Cinema Daily'
        newJob.job_name = datetime.today().strftime('%Y-%m-%d')
        
        newConfig = unreal.load_asset("/Game/Cinema/Render_Setting/MW_Early_4K_422HQ")
        newJob.set_configuration(newConfig)
        # Now we can configure the job. Calling find_or_add_setting_by_class is how you add new settings.
        outputSetting = newJob.get_configuration().find_or_add_setting_by_class(unreal.MoviePipelineOutputSetting)
        # outputSetting.output_resolution = unreal.IntPoint(1280, 720)
        outputSetting.file_name_format = "{sequence_name}.{frame_number}"
        
        try:
            outputName = cmdParameters['OutputName']
            outputSetting.file_name_format = "%s.{frame_number_rel}" % outputName
        except:
            unreal.log_error("Missing '-OutputName' argument")

        try:
            outputDirectoryPath = cmdParameters['OutputDirectory']
            outputSetting.output_directory = unreal.DirectoryPath(outputDirectoryPath)
        except:
            unreal.log_error("Missing '-OutputDirectory' argument")

        # Ensure there is something to render
        newJob.get_configuration().find_or_add_setting_by_class(unreal.MoviePipelineDeferredPassBase)
        # Ensure there's a file output.
        newJob.get_configuration().find_or_add_setting_by_class(unreal.MoviePipelineImageSequenceOutput_PNG)
        
        # This is important. There are several settings that need to be
        # initialized (just so their default values kick in) and instead
        # of requiring you to add every one individually, you can initialize
        # them all in one go at the end.
        newJob.get_configuration().initialize_transient_settings()
        
        # Burnin options
        burninSetting = newJob.get_configuration().find_or_add_setting_by_class(unreal.MoviePipelineBurnInSetting)
        burninSetting.burn_in_class = unreal.SoftClassPath("/MovieRenderPipeline/Blueprints/DefaultBurnIn.DefaultBurnIn_C")
        burninSetting.composite_onto_final_image = True

        gameModeSetting = newJob.get_configuration().find_or_add_setting_by_class(unreal.MoviePipelineGameOverrideSetting)
        # gameModeSetting.game_mode_override = unreal.MoviePipelineGameMode.static_class()
        gameModeSetting.cinematic_quality_settings = True
        gameModeSetting.texture_streaming = unreal.MoviePipelineTextureStreamingMethod.DISABLED
        gameModeSetting.disable_hlo_ds = True
        gameModeSetting.use_lod_zero = True
        gameModeSetting.use_high_quality_shadows = True
        gameModeSetting.shadow_distance_scale = 10
        gameModeSetting.shadow_radius_threshold = 0.001
        gameModeSetting.override_view_distance_scale = True
        gameModeSetting.view_distance_scale = 50

        # Now that we've set up the minimum requirements on the job we can created
        # a movie render pipeline to run our job. Construct the new object
        self.activeMoviePipeline = unreal.new_object(self.target_pipeline_class, outer=self.get_last_loaded_world(), base_type=unreal.MoviePipeline);
        
        # Register to any callbacks we want
        self.activeMoviePipeline.on_movie_pipeline_work_finished_delegate.add_function_unique(self, "on_movie_pipeline_finished")
        
        # And finally tell it to start working. It will continue working
        # and then call the on_movie_pipeline_finished_delegate function at the end.
        self.activeMoviePipeline.initialize(newJob)
   
    # This function is called every frame and can be used to do simple countdowns, checks
    # for more work, etc. Can be entirely omitted if you don't need it.
    @unreal.ufunction(override=True)
    def on_begin_frame(self):
        # It is important that we call the super so that async socket messages get processed.
        super(CinemaMPRExecutor, self).on_begin_frame()        
        
        if self.activeMoviePipeline:
            unreal.log("Progress: %f" % unreal.MoviePipelineLibrary.get_completion_percentage(self.activeMoviePipeline))
           
   
    # This is NOT called for the very first map load (as that is done before Execute is called).
    # This means you can assume this is the resulting callback for the last open_level call.
    @unreal.ufunction(override=True)
    def on_map_load(self, inWorld):
        # We don't do anything here, but if you were processing a queue and needed to load a map
        # to render a job, you could call:
        # 
        # unreal.GameplayStatics.open_level(self.get_last_loaded_world(), mapPackagePath, True, gameOverrideClassPath)
        # 
        # And then know you can continue execution once this function is called. The Executor
        # lives outside of a map so it can persist state across map loads.
        # Don't call open_level from this function as it will lead to an infinite loop.
        pass
        
        
    # This needs to be overriden. Doens't have any meaning in runtime executors, only
    # controls whether or not the Render (Local) / Render (Remote) buttons are locked
    # in Editor executors.
    @unreal.ufunction(override=True)
    def is_rendering(self):
        return False
        
    # This declares a new UFunction and specifies the return type and the parameter types
    # callbacks for delegates need to be marked as UFunctions.
    @unreal.ufunction(ret=None, params=[unreal.MoviePipelineOutputData])
    def on_movie_pipeline_finished(self, results):
        # We're not processing a whole queue, only a single job so we can
        # just assume we've reached the end. If your queue had more than 
        # one job, now would be the time to increment the index of which
        # job you are working on, and start the next one (instead of calling
        # on_executor_finished_impl which should be the end of the whole queue)
        unreal.log("Finished rendering movie! Success: " + str(results.success))
        self.activeMoviePipeline = None
        self.on_executor_finished_impl()
        
    @unreal.ufunction(ret=None, params=[str])
    def on_socket_message(self, message):
        # Message is a UTF8 encoded string. The system expects
        # messages to be sent over a socket with a uint32 to describe
        # the message size (not including the size bytes) so
        # if you wanted to send "Hello" you would send 
        # uint32 - 5
        # uint8 - 'H'
        # uint8 - 'e' 
        # etc.
        # Socket messages sent from the Executor will also be prefixed with a size.
        pass
        
    @unreal.ufunction(ret=None, params=[int, int, str])
    def on_http_response_recieved(self, inRequestIndex, inResponseCode, inMessage):
        # This is called when an http response is returned from a request.
        # the request index will match the value returned when you made the original 
        # call, so you can determine the original intent this response is for.
        pass