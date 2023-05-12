from Logging import Logging

logger = Logging('daisy.log')
logger.set_up_logging()

import daisy_llm.ModuleLoader as ml
import daisy_llm.ContextHandlers as ch

ch = ch.ContextHandlers('daisy.db')
ml = ml.ModuleLoader(ch,
                  configs_yaml="configs.yaml",
                  modules=["modules.Daisy.Daisy",
                           "modules.Daisy.DaisyPrompt"]
                  )


#Start ModuleLoader dynamic checker
ml.start_update_configs_loop_thread()

#Start front end sub processes
ml.process_main_start_instances()

#When front ends are done, or signal received, stop the loop
#ml.close()