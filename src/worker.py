import time
import os
from src.database import Database
from src.pipeline import run_pipeline
from src.extractors.report_parser import parse_report # <-- NEW IMPORT
from src.config import logger

class Worker:
    def __init__(self):
        self.db = Database()
        self.worker_id = f"worker_{os.getpid()}"
        logger.info(f"Worker {self.worker_id} initialized.")

    def run_once(self):
        """Claims and processes a single pending item from the database queue."""
        job = self.db.claim_pending_item()
        if not job:
            logger.info(f"[{self.worker_id}] No pending jobs found. Resting.")
            return

        post_id = job["_id"]
        url = job["source_url"]
        start_time = time.time()
        
        try:
            logger.info(f"⚙️ [{self.worker_id}] Processing job {post_id} for URL: {url}")

            # Step 1: Run the full pipeline to get the final report
            final_report = run_pipeline(url)
            
            # This handles the "skip" case from the downloader
            if isinstance(final_report, dict) and final_report.get("status") == "skipped":
                logger.info(f"⏩ Job {post_id} was skipped by the pipeline. Marking as complete.")
                # We can complete it with minimal data to prevent it from being picked up again.
                metadata = {"worker_id": self.worker_id, "note": "Skipped, already processed."}
                self.db.complete_item(post_id, "Skipped", final_report, metadata)
                return

            if not final_report or not isinstance(final_report, str):
                raise RuntimeError("Pipeline failed to return a valid summary report string.")
            
            # Step 2: Parse the report back into structured data
            structured_data = parse_report(final_report)

            # Step 3: Record metadata and complete the job in the database
            end_time = time.time()
            metadata = {
                "worker_id": self.worker_id,
                "processing_time_sec": round(end_time - start_time, 2)
            }
            
            self.db.complete_item(post_id, final_report, structured_data, metadata)
            logger.info(f"✅ [{self.worker_id}] Job {post_id} completed in {metadata['processing_time_sec']}s.")

        except Exception as e:
            error_msg = f"Job {post_id} failed: {e}"
            logger.error(f"❌ [{self.worker_id}] {error_msg}", exc_info=True)
            self.db.fail_item(post_id, str(e))

if __name__ == '__main__':
    logger.info("Running a single worker process for testing.")
    worker = Worker()
    worker.run_once()
    logger.info("Worker test run finished.")