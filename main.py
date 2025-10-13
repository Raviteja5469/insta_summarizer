from src.pipeline import run_pipeline
from src.config import Config
import argparse

if __name__ == "__main__":
    Config.validate()

    parser = argparse.ArgumentParser(description="Instagram Reel Summarizer")
    parser.add_argument("url", type=str, help="Instagram reel URL")
    parser.add_argument("--lang", type=str, default="English", help="Target language")
    args = parser.parse_args()

    output = run_pipeline(args.url, args.lang)
    print("\n=== OUTPUT ===")
    print("Summary:", output["summary"])
    print("Transcript:", output["transcript"])
    print("Frame Descriptions:", output["frame_descriptions"])