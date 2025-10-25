# Test script
# from src.downloaders.instagram import InstagramDownloader
from src.extractors.audio import extract_audio
# from src.processors.audio import AudioProcessor
# from src.processors.video import VideoProcessor
# from src.processors.evaluator import Evaluator
# from src.processors.image import ImageProcessor

# downloader = InstagramDownloader()
# audio_processor = AudioProcessor()
# video_processor = VideoProcessor()
# evaluator = Evaluator()
# imageProcessor = ImageProcessor()

# download_result = downloader.download("https://www.instagram.com/p/DNV0iKfie8O/")
# print(f"Video path: {download_result}")

# image_summary = imageProcessor.process(download_result["folder_path"])
# print(f"Image Summary: {image_summary}")

# audio_path = extract_audio("temp_files/post_DNV0iKfie8O/DNV0iKfie8O_2.mp4")
# print(f"Audio path: {audio_path}")

# audio_result = audio_processor.process("temp_files/reel_DPeG4jdjEAA/DPeG4jdjEAA.wav")
# print(f"Transcript: {audio_result}")

# video_path = "temp_files/reel_DPeG4jdjEAA/DPeG4jdjEAA.mp4"
# evaluation = evaluator.decide(video_path, 0.9763033)
# print(f"Evaluation: {evaluation}")

# if evaluation['decision']:
#     video_summary = video_processor.process(video_path)
#     print(f"Video summary: {video_summary}")    
# else:
#     print("Skipping visual summarization based on evaluation.")

'''
{
  "caption": "Instagram Content Metadata\n==============================\n\nURL: https://www.instagram.com/p/DNV0iKfie8O/\nChannel: @uncover.ai\nUpload Date: 2025-08-14 15:45:00\nType: Post\nLikes: 27,236\n\nDescription:\nGoogle has introduced a way for anyone to create their own AI assistant without writing a single line of code, making advanced technology feel accessible in just a few simple steps.\n\nThis new feature is completely free to use, works with their Gemini platform, and can be set up in under five minutes, offering tools that were once limited to developers now to anyone curious enough to try.\n\nIt marks another moment where everyday users can interact with AI in ways that feel personal, useful, and surprisingly easy to bring into their daily routines.\n\nWe cover more AI tutorials in our newsletter. \n\nWant to join for free? \n\nComment or DM \"NEWSLETTER\" to get the link.\n\n\u2014\n\nCredits: @heygurisingh/X\n",
  "image_summary": "Here's an analysis of the provided social media post:\n\n**Image 1 Analysis:**\n\n*   **Title:** Google has launched Gemini AI\n*   **Key Text:** \"GOOGLE JUST GAVE EVERYONE THE POWER TO BUILD THEIR OWN AI ASSISTANT WITHOUT ANY CODING. IT'S COMPLETELY FREE, AND YOU CAN SET YOURS UP IN UNDER 5 MINUTES:\"\n*   **Visual Elements:** Image of Sundar Pichai (Google CEO), with two circular graphics superimposed: one showing an AI robot working on a laptop, and the other with the Gemini logo.\n*   **Implied Information:** This image is a promotional announcement by Uncover AI, likely about a new Google Gemini AI product that will allow users to create their own AI assistants, without coding.\n\n**Image 2 Analysis:**\n\n*   **Key Text:** \"We cover more AI tutorials in our newsletter. Want to join for free? Comment or DM \"NEWSLETTER\" to get the link.\"\n*   **Key Text:** \"The Biggest AI Week of 2025 (So Far)\"\n    *   This might've been the wildest week in AI history. GPT-5 is finally here, Claude 4.1 is putting up a fight, Google launches Genie 3 and Gemini storybooks, ElevenLabs enters music, Grok adds video gen, and Midjourney rolls out HD video. Let's dive in.\"\n*   **Visual Elements:** Text with a review of a week in the future, filled with many AI announcements and developments\n*   **Implied Information:**\n    *   This is a promotion for a newsletter run by \"Uncover AI\" where they share more tutorials and information about AI.\n    *   The second text block presents a summary of what AI news would have been the 'wildest week in history', with many important updates on AI platforms and their advances, using a future date (August 13, 2025).\n\n**Summary:**\n\nThis social media post from Uncover AI focuses on the launch of a new product by Google. They're promoting the new Google Gemini AI platform, that allows people to easily create AI assistants without any coding experience. The post promises that it's a quick and free process. Additionally, the post promotes their newsletter, which provides more AI-related tutorials. To encourage sign-ups, they highlight how big the current advances in AI technology, which could be related to what the newsletter offers, through a future news recap.",
  "audio_transcripts": [],
  "video_summaries": [
    "This frame is an instructional introduction to creating custom AI assistants, called \"Gems\", using Gemini. The initial steps are: 1. Navigate to gemini.google.com, 2. Click \"Gem Manager\", and 3. Select \"New Gem\". The text states that \"Gems\" are custom AI assistants and lists a few pre-made examples like Brainstormer, Career Guide, and Coding Partner. A screenshot of the Gemini interface is shown, displaying a greeting (\"Hello, Gurinderjeet\") and bottom toolbar with options for AI tasks. The @Uncover AI is the source of the content.",
    "Here's a concise summary of the visual content:\n\nThe video frames demonstrate the process of creating an AI \"Gem\" using a platform called \"Gemini.\" \n\n**Key Steps:**\n\n1.  **Name & Brain:** The video guides the user through the steps to create a new AI:\n    *   Name the Gem.\n    *   Write instructions to define the Gem's behavior.\n    *   Use a \"Magic Pencil\" tool (presumably for auto-improvement).\n\n2.  **User Interface:** The interface includes:\n    *   A \"Gem manager\" section that displays existing and newly created gems.\n    *   An interface to input the Gem's name, instructions, and add data.\n    *   A button to \"Start Chat\".\n\n3.  **Example:** The video demonstrates creating a Gem named \"HeyGuriSingh X\" with a set of instructions. A message confirms that the Gem has been created.",
    "This frame presents step 3 of a tutorial on using an AI platform. The instructions highlight how to enhance the AI's capabilities by feeding it knowledge. Specifically, it instructs the user to upload up to 10 PDFs or images within the \"Knowledge\" section, claiming this will make the AI smarter and more powerful than ChatGPT. A screen capture of a user interface is displayed, showing a chat interface with a sidebar and a prompt area. The interface indicates that the user is interacting with an AI named \"HeyGuriSingh X\" within the \"Gemini\" platform.",     
    "The video frame focuses on the final step before launching an AI. It recommends testing the AI by using a preview window to see how it responds. The video prompts the user to adjust the instructions given to the AI until the AI performs as intended. The visual shows a user interface with the name \"HeyGuriSingh X,\" instructions \"You are the best content creator,\" a \"Preview\" window, and various UI elements such as \"Ask Gemini\". It seems like the user is in the process of creating and testing an AI.",
    "This frame is from an informational video explaining how to edit an AI within the \"Gem Manager\" interface, likely of an AI platform. The text at the top \"Step 5: Edit anytime\" and the subsequent bullet points describe the procedure: Go back to Gem Manager, click edit, tweak instructions or knowledge, and hit update. The interface shows a dark-themed UI with \"Gem Manager\" title at the top. The UI displays pre-made AI options like \"Chess champ\", \"Storybook\", \"Brainstormer\" and \"Career guide\". It also shows the user's created AI \"HeyGurSingh.K\" and how to add a new one.  The bottom of the screen has the @Uncover Al logo and handle."
  ]
}
'''



