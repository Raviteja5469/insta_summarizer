from src.pipeline import run_pipeline
from src.config import Config
import argparse

if __name__ == "__main__":
    Config.validate()

    parser = argparse.ArgumentParser(description="Instagram Reel Summarizer")
    parser.add_argument("url", type=str, help="Instagram reel URL")
    args = parser.parse_args()

    output = run_pipeline(args.url)
    print("\n=== OUTPUT ===")
    print(output)