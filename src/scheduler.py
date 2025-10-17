from apscheduler.schedulers.blocking import BlockingScheduler
from src.discoverer import Discoverer  # We will create this next
from src.worker import Worker
from src.config import logger

# --- Instantiate Modules ---
# These are instantiated once and their methods are called by the scheduler.
discoverer = Discoverer()
worker = Worker()

# --- Initialize Scheduler ---
scheduler = BlockingScheduler()

logger.info("🚀 Starting the Content Processing Scheduler.")

# Job 1: The Discoverer 
scheduler.add_job(
    discoverer.run_once, 
    "interval", 
    minutes=30, 
    id="discoverer_job"
)

# Job 2: The Worker
scheduler.add_job(
    worker.run_once,
    "interval", 
    minutes=5, 
    id="worker_job"
)

print("="*50)
print("Scheduler is now running.")
print("  - Discoverer runs every 30 minutes.")
print("  - Worker runs every 5 minutes.")
print("Press Ctrl+C to exit.")
print("="*50)

if __name__ == "__main__":
    try:
        # Run jobs once on startup for immediate feedback
        scheduler.get_job('discoverer_job').func()
        scheduler.get_job('worker_job').func()
        
        # Start the main scheduling loop
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user.")