import os
import pickle
import logging
from typing import List, Dict, Any, Tuple
from langchain_community.document_loaders import TextLoader, DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.schema import Document
from ..config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RAGService:
    def __init__(self):
        logger.info("Initializing RAG Service...")
        
        self.embeddings = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
        
        self.llm = ChatGroq(
            groq_api_key=settings.groq_api_key,
            model_name="llama-3.3-70b-versatile",
            temperature=0.1
        )
        
        self.vectorstore = None
        # Store conversation history per user per session: {user_id: {session_id: [messages]}}
        self.session_conversations: Dict[int, Dict[int, List[Dict]]] = {}
        
        self._load_or_create_vectorstore()
        logger.info("✅ RAG Service initialized successfully")
        
    def _load_or_create_vectorstore(self):
        vectorstore_path = "vectorstore.pkl"
        
        if os.path.exists(vectorstore_path):
            try:
                with open(vectorstore_path, 'rb') as f:
                    self.vectorstore = pickle.load(f)
                logger.info("✅ Loaded existing vectorstore")
            except Exception as e:
                logger.error(f"❌ Failed to load vectorstore: {e}")
                self._create_vectorstore()
        else:
            self._create_vectorstore()
            
    def _create_vectorstore(self):
        logger.info("Creating new vectorstore...")
        
        if not os.path.exists("college_data"):
            os.makedirs("college_data")
            
        sample_file = "college_data/apsit_data.txt"
        if not os.path.exists(sample_file):
            apsit_data = """Welcome to A.P. Shah Institute of Technology (APSIT)! Here's comprehensive information about our institution:
About APSIT:
A.P. Shah Institute of Technology (APSIT) was established in 2014 and is located in Thane West, Maharashtra. We are a private engineering institute offering undergraduate programs in various engineering disciplines. APSIT is affiliated with the University of Mumbai and approved by AICTE. Our campus is strategically located on the Mumbai-Pune Highway, making it easily accessible.
Academic Programs Available:
- Bachelor of Engineering (B.E.) in Computer Engineering - 4 years
- Bachelor of Engineering (B.E.) in Information Technology - 4 years (180 seats)
- Bachelor of Engineering (B.E.) in Electronics and Telecommunication Engineering - 4 years
- Bachelor of Engineering (B.E.) in Mechanical Engineering - 4 years
- Bachelor of Engineering (B.E.) in Civil Engineering - 4 years
- Bachelor of Engineering (B.E.) in Electronics Engineering - 4 years
Information Technology Department Details:
Our IT department offers a comprehensive 4-year B.E. program in Information Technology with an intake of 180 students per year. The curriculum is designed to meet industry standards and includes programming, databases, networking, AI/ML, cybersecurity, and more.
Admission Process:
Admissions conducted through Maharashtra CAP (90% seats) and Institute level (10% seats). Requirements include 12th pass with Physics, Math, Chemistry/Biology, minimum 45% marks, and MHT-CET or JEE Main score.
Fee Structure: Approximately Rs. 1,33,000 per year total.
Facilities: Modern labs, library, sports facilities, hostel, cafeteria, and more.
Placements: 85-90% placement rate with companies like TCS, Infosys, Microsoft, Google, Amazon.
Contact: +91-22-25397659, info@apsit.edu.in, www.apsit.edu.in
Address: Mumbai-Pune Highway, Thane West, Thane - 400615, Maharashtra."""
            
            with open(sample_file, "w", encoding='utf-8') as f:
                f.write(apsit_data)
            logger.info("✅ Created APSIT data")
            
        try:
            loader = DirectoryLoader("college_data/", glob="**/*.txt", loader_cls=TextLoader, show_progress=True, loader_kwargs={'encoding': 'utf-8'})
            documents = loader.load()
            
            if not documents:
                documents = [Document(page_content=open(sample_file, 'r', encoding='utf-8').read())]
                
            text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
            texts = text_splitter.split_documents(documents)
            
            self.vectorstore = FAISS.from_documents(texts, self.embeddings)
            
            with open("vectorstore.pkl", 'wb') as f:
                pickle.dump(self.vectorstore, f)
            logger.info("✅ Vectorstore created and saved")
            
        except Exception as e:
            logger.error(f"❌ Error creating vectorstore: {e}")
            raise
            
    def _get_session_context(self, user_id: int, session_id: int, limit: int = 6) -> str:
        """Get conversation history for specific session"""
        if user_id not in self.session_conversations:
            return ""
            
        if session_id not in self.session_conversations[user_id]:
            return ""
            
        recent_messages = self.session_conversations[user_id][session_id][-limit:]
        if not recent_messages:
            return ""
            
        context = "Previous conversation in this chat:\n"
        for msg in recent_messages:
            context += f"Student: {msg['question']}\nAssistant: {msg['answer']}\n\n"
        return context.strip()
        
    def _store_session_conversation(self, user_id: int, session_id: int, question: str, answer: str):
        """Store conversation for specific session"""
        if user_id not in self.session_conversations:
            self.session_conversations[user_id] = {}
            
        if session_id not in self.session_conversations[user_id]:
            self.session_conversations[user_id][session_id] = []
            
        self.session_conversations[user_id][session_id].append({
            'question': question,
            'answer': answer
        })
        
        # Keep only last 20 exchanges per session
        if len(self.session_conversations[user_id][session_id]) > 20:
            self.session_conversations[user_id][session_id] = self.session_conversations[user_id][session_id][-20:]
            
    def get_response_for_session(self, question: str, user_id: int, session_id: int) -> str:
        """Get response with session-specific memory"""
        logger.info(f"Processing question from user {user_id}, session {session_id}: {question}")
        
        try:
            # Get relevant documents
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 4})
            relevant_docs = retriever.get_relevant_documents(question)
            
            college_context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Get session-specific conversation history
            session_history = self._get_session_context(user_id, session_id)
            
            prompt = f"""You are APSIT's helpful college assistant. You maintain conversation context within each chat session.
{session_history}
APSIT COLLEGE INFORMATION:
{college_context}
CURRENT QUESTION: {question}
INSTRUCTIONS:
- Use conversation context from THIS chat session
- Remember what the student told you in THIS specific conversation
- Answer based on APSIT information and this session's history
- Be helpful and conversational
- If you don't have specific APSIT information, say so clearly
ANSWER:"""
            response = self.llm.invoke(prompt)
            
            # Store in session-specific memory
            self._store_session_conversation(user_id, session_id, question, response.content)
            
            logger.info(f"✅ Response generated for session {session_id}")
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Error in get_response_for_session: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again or contact APSIT at +91-22-25397659."
            
    def clear_session_memory(self, user_id: int, session_id: int):
        """Clear memory for specific session"""
        if user_id in self.session_conversations:
            if session_id in self.session_conversations[user_id]:
                del self.session_conversations[user_id][session_id]
                
    def clear_all_user_memory(self, user_id: int):
        """Clear all session memories for user"""
        if user_id in self.session_conversations:
            del self.session_conversations[user_id]

# Global RAG service instance
rag_service = RAGService()