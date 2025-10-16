import os
import cv2
import google.generativeai as genai
from PIL import Image
from pathlib import Path
from typing import List, Optional
from src.config import logger, Config

class ImageProcessor:
    """
    Processes a collection of images from a single post, sending them
    all in a single API call to Google Gemini to generate a cohesive summary.
    """
    def __init__(self):
        # Configure the Gemini API client
        try:
            genai.configure(api_key=Config.GOOGLE_API_KEY)
            self.model = genai.GenerativeModel("gemini-2.0-flash-lite")
            logger.info("Initialized image processor with gemini-2.0-flash-lite.")
        except Exception as e:
            logger.error(f"Failed to configure Google Gemini client: {e}")
            self.model = None

        self.supported_extensions = ['.jpg', '.jpeg', '.png', '.webp']

    def _find_images(self, folder_path: str) -> List[Path]:
        """
        Scans a directory and returns a sorted list of image file paths.
        """
        if not os.path.isdir(folder_path):
            logger.warning(f"Provided path is not a directory: {folder_path}")
            return []
            
        image_paths = [
            p for p in Path(folder_path).iterdir()
            if p.suffix.lower() in self.supported_extensions
        ]
        # Sort images by name to maintain carousel order
        image_paths.sort()
        logger.info(f"Found {len(image_paths)} images in '{folder_path}'.")
        return image_paths

    def process(self, post_folder_path: str) -> Optional[str]:
        """
        Analyzes all images in a post folder and returns a single summary using Gemini.

        Args:
            post_folder_path: The path to the folder containing the post's images.
        
        Returns:
            A string containing the generated summary, or None if an error occurs.
        """
        if not self.model:
            logger.error("Gemini model is not initialized. Cannot process images.")
            return None

        image_paths = self._find_images(post_folder_path)
        if not image_paths:
            logger.warning("No images found to process in the specified folder.")
            return "No images were found in this post."

        # 1. Prepare the prompt and images for the single API call
        prompt_parts = [
            """
            You are a tech analyst. The following images are from a single social media post, likely an informational carousel.
            Analyze all images in the sequence they are provided. Your task is to synthesize the information across all of them into one, single, cohesive summary.
            - Transcribe important text, code snippets, or titles from each image.
            - Explain any diagrams, charts, or key visual elements.
            - Capture the main topic and the key takeaways presented across the entire post.
            - Provide a final, well-structured summary.
            """
        ]

        image_objects = []
        for path in image_paths:
            try:
                # The Gemini API can handle various image formats directly.
                img = Image.open(path)
                image_objects.append(img)
            except Exception as e:
                logger.warning(f"Could not process image {path}: {e}")
                continue
        
        if not image_objects:
            return "Could not read any of the image files."
        
        prompt_parts.extend(image_objects)

        # 2. Make the single, efficient API call
        try:
            logger.info(f"Making a single API call to Gemini with {len(image_objects)} images...")
            response = self.model.generate_content(prompt_parts)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Image post summary generation failed with Gemini: {e}")
            return None