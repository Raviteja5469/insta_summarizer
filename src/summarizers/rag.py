from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
import google.generativeai as genai
from src.config import Config, logger

embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001", google_api_key=Config.GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash-lite")

def gemini_summarize_with_rag(transcript: str, frame_descriptions: str = None, target_lang: str = "English") -> str:
    if not transcript.strip():
        return "Transcript empty."

    try:
        all_text = transcript
        if frame_descriptions:
            all_text += f"\n\nVisuals: {frame_descriptions}"

        splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
        chunks = splitter.split_text(all_text)
        db = FAISS.from_texts(chunks, embeddings)

        query = f"Summarize in {target_lang} (3-5 sentences)."
        docs = db.similarity_search(query, k=5)
        retrieved_text = "\n\n".join([d.page_content for d in docs])

        prompt = f"Summarize: {retrieved_text}"
        response = model.generate_content(prompt)
        summary = response.text.strip() if hasattr(response, "text") else "No summary generated."
        logger.info("Generated RAG summary")
        return summary
    except Exception as e:
        logger.error(f"RAG summary failed: {e}")
        return f"Error: {e}"