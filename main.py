# from src.pipeline import run_pipeline
from src.config import Config, logger
import time
import argparse
# import src.scheduler as scheduler
from src.contentFetchers import bootstrap_channels

if __name__ == "__main__":
    Config.validate()

    # parser = argparse.ArgumentParser(description="Instagram Reel Summarizer")
    # parser.add_argument("url", type=str, help="Instagram reel URL")
    # args = parser.parse_args()

    # output = run_pipeline(args.url)
    # print("\n=== OUTPUT ===")
    # print(output)
    
    # =====================================================================
    
    # try:
    #     # Run jobs once on startup for immediate feedback
    #     scheduler.get_job('discoverer_job').func()
    #     scheduler.get_job('worker_job').func()
        
    #     # Start the main scheduling loop
    #     scheduler.start()
    # except (KeyboardInterrupt, SystemExit):
    #     logger.info("Scheduler stopped by user.")
    
    
    # =====================================================================

    usernames = ["theaifield"]
    for user in usernames:
        bootstrap_channels.bootstrap_channel(user, limit=50)
        logger.info(f"Completed process for {user}. Waiting 30 seconds before next run.")
        time.sleep(30)