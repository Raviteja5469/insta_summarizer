from src.config import Config, logger
from apscheduler.schedulers.blocking import BlockingScheduler
from src.fetchers.discoverer import DiscovererService
from src.worker import WorkerService

if __name__ == "__main__":
    # 1. Validate config first
    logger.info("Validating configuration...")
    Config.validate()
    logger.info("Configuration valid.")

    # 2. Instantiate services
    logger.info("Initializing services...")
    discoverer = DiscovererService()
    worker = WorkerService()

    # 3. Initialize scheduler
    scheduler = BlockingScheduler()
    logger.info("🚀 Starting the Content Processing Scheduler.")

    # Job 1: The Discoverer (Scout)
    # Runs every 30 minutes to find new posts
    scheduler.add_job(
        discoverer.run_once,
        "interval",
        minutes=30,
        id="discoverer_job"
    )

    # Job 2: The Worker (Factory)
    # Runs every 5 minutes to process one item from the queue
    scheduler.add_job(
        worker.run_once,
        "interval",
        minutes=5,
        id="worker_job"
    )

    print("=" * 50)
    print("Scheduler is now running.")
    print("  - Discoverer (Scout) runs every 30 minutes.")
    print("  - Worker (Factory) runs every 5 minutes.")
    print("Press Ctrl+C to exit.")
    print("=" * 50)

    # 4. Run the scheduler
    try:
        # Run jobs once on startup for immediate feedback
        logger.info("--- Running initial discoverer job on startup... ---")
        scheduler.get_job('discoverer_job').func()
        logger.info("--- Running initial worker job on startup... ---")
        scheduler.get_job('worker_job').func()
        logger.info("--- Initial jobs complete. Starting main scheduling loop... ---")

        # Start the main scheduling loop (this is a blocking call)
        scheduler.start()
        
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped by user.")