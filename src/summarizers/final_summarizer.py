import google.generativeai as genai
from typing import Dict, Any, Optional
from src.config import logger, Config

# --- Merged and Refined System Prompt ---
# This combines the best elements of both your prompts into a single, effective instruction.
SYSTEM_PROMPT = """
You are an expert technology analyst and AI researcher with a deep understanding of software development, artificial intelligence, and emerging tech trends.

You will receive a structured set of data extracted from a single piece of social media content. This data may include a description, an AI-generated summary of its images, an audio transcription and summaries of its video frames.

Your mission is to act like a human tech analyst: do not just summarize the visible content. Instead, you must synthesize the information, extract hidden value, identify trends, and generate insights specifically for a developer audience.

Follow these core principles for your analysis:

1.  **Synthesize, Don't Repeat:** Integrate information from all provided sources (description, images, transcripts, video) into a cohesive understanding. Find the core message.
2.  **Extract Key Facts:** Identify the specific technology, model, tool, or framework being discussed. What is it, and what does it do?
3.  **Infer and Go Deeper (Think Like a Developer):** This is your most important task. Go beyond the provided text to answer:
    - How can a student, engineer, or researcher experiment with this technology?
    - What problem does it solve better than existing solutions?
    - Are there potential APIs, code libraries, or platforms involved?
    - What are its unique advantages or potential limitations?
4.  **Focus on Signal, Not Noise:** Ignore promotional language ("DM for link," "join our newsletter") and focus on the technical, meaningful points.
5.  **Provide a Forward-Looking Perspective:** Briefly explain why this development is significant and what it might indicate for future tech trends.

Your final output must be structured exactly as follows, using Markdown for formatting:

### Core Summary
(A 1-2 sentence executive summary capturing the essence of the content.)

### Technical Insights
(Bulleted list of the key technical details, unique features, or what makes the technology special.)

### Developer Perspective
(Bulleted list of practical applications, use-cases, and actionable steps for developers, students, or researchers.)

### Broader Impact
(A brief 1-2 sentence analysis on why this matters for the tech industry or the future.)
"""


class FinalSummarizer:
    """
    Synthesizes multimodal data into a final, developer-focused analytical report.
    """
    def __init__(self):
        try:
            api_key = Config.GOOGLE_API_KEY
            if not api_key:
                raise ValueError("GOOGLE_API_KEY environment variable not set.")
            genai.configure(api_key=api_key)
            # Use a more powerful model for the final, complex reasoning step.
            self.model = genai.GenerativeModel('gemini-2.5-flash')
            logger.info("Final Summarizer initialized with Gemini 2.5 Flash.")
        except Exception as e:
            logger.error(f"Failed to configure Google Gemini client for FinalSummarizer: {e}")
            self.model = None

    def _prepare_input_text(self, summary_data: Dict[str, Any]) -> str:
        """Formats the summary dictionary into a clean string for the AI model."""
        content_blocks = []

        if summary_data.get("description"):
            content_blocks.append("--- DESCRIPTION ---\n" + summary_data["description"])

        if summary_data.get("image_summary"):
            content_blocks.append("--- IMAGE ANALYSIS ---\n" + summary_data["image_summary"])

        if summary_data.get("audio_transcripts"):
            # This part can be enhanced if audio transcripts are added later
            pass 

        if summary_data.get("video_summaries"):
            video_section = ["--- VIDEO FRAME SUMMARIES ---"]
            for i, summary in enumerate(summary_data["video_summaries"]):
                video_section.append(f"Frame Group {i+1}:\n{summary}")
            content_blocks.append("\n".join(video_section))
        
        return "\n\n".join(content_blocks)

    def process(self, summary_data: Dict[str, Any]) -> Optional[str]:
        """
        Generates the final, structured summary from the aggregated data.

        Args:
            summary_data: A dictionary containing caption, image_summary, etc.
        
        Returns:
            A string containing the formatted analytical report, or None if an error occurs.
        """
        if not self.model:
            logger.error("FinalSummarizer model not initialized. Cannot process.")
            return None

        logger.info("Starting final synthesis of all collected data...")

        # 1. Format the input dictionary into a single text block
        user_content = self._prepare_input_text(summary_data)
        if not user_content.strip():
            logger.warning("No content to summarize. The input data was empty.")
            return "No content was provided to summarize."

        # 2. Construct the prompt for the API call
        prompt = [
            SYSTEM_PROMPT,
            "Here is the data you need to analyze:",
            user_content
        ]

        # 3. Make the API call
        try:
            response = self.model.generate_content(prompt)
            logger.info("✅ Final analytical report generated successfully.")
            return response.text.strip()
        except Exception as e:
            logger.error(f"Final summary generation failed: {e}")
            return None
