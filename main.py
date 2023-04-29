from Logging import Logging

logger = Logging('daisy.log')
logger.set_up_logging()

from daisy_llm import ModuleLoader, ContextHandlers

ch = ContextHandlers('daisy.db')
ml = ModuleLoader(ch,
                  configs_yaml="configs.yaml",
                  modules=["modules.Daisy.Daisy"]
                  )


#Start ModuleLoader dynamic checker
ml.start_update_configs_loop_thread()

#Start front end sub processes
ml.process_main_start_instances()

#When front ends are done, or signal received, stop the loop
ml.stop_update_modules_loop_thread()