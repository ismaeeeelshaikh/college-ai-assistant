import os
import pickle
import logging
from datetime import datetime
from typing import List, Dict, Any, Tuple
from langchain_community.document_loaders import DirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_groq import ChatGroq
from langchain.schema import Document
from ..config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Custom TextLoader that handles encoding issues
class SafeTextLoader:
    def __init__(self, file_path: str):
        self.file_path = file_path
    
    def load(self) -> List[Document]:
        """Load text file with proper encoding handling"""
        try:
            # Try UTF-8 first
            with open(self.file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            try:
                # Try UTF-8 with error handling
                with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                logger.warning(f"Used UTF-8 with error handling for {self.file_path}")
            except Exception:
                try:
                    # Try Windows encoding
                    with open(self.file_path, 'r', encoding='cp1252', errors='ignore') as f:
                        content = f.read()
                    logger.warning(f"Used cp1252 with error handling for {self.file_path}")
                except Exception:
                    # Last resort - read as binary and decode
                    with open(self.file_path, 'rb') as f:
                        raw_content = f.read()
                    content = raw_content.decode('utf-8', errors='ignore')
                    logger.warning(f"Used binary decode for {self.file_path}")
        
        # Clean content - remove problematic characters
        content = self._clean_content(content)
        
        return [Document(
            page_content=content,
            metadata={"source": self.file_path}
        )]
    
    def _clean_content(self, content: str) -> str:
        """Clean content of problematic characters"""
        # Replace common problematic characters
        replacements = {
            '\x9d': "'",  # Replace problematic character
            '\x91': "'",  # Left single quotation mark
            '\x92': "'",  # Right single quotation mark
            '\x93': '"',  # Left double quotation mark
            '\x94': '"',  # Right double quotation mark
            '\x96': '-',  # En dash
            '\x97': '-',  # Em dash
            '\u2019': "'", # Right single quotation mark
            '\u201c': '"', # Left double quotation mark
            '\u201d': '"', # Right double quotation mark
            '\u2013': '-', # En dash
            '\u2014': '-', # Em dash
        }
        
        for old, new in replacements.items():
            content = content.replace(old, new)
        
        # Remove any remaining non-printable characters
        content = ''.join(char for char in content if ord(char) >= 32 or char in '\n\r\t')
        
        return content

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
        # Keep old-style user conversations for backward compatibility
        self.user_conversations: Dict[int, List[Dict]] = {}
        
        self._load_or_create_vectorstore()
        logger.info("✅ RAG Service initialized successfully")
    
    def _should_recreate_vectorstore(self) -> bool:
        """Check if vectorstore needs to be recreated based on file modifications"""
        vectorstore_path = "vectorstore.pkl"
        
        if not os.path.exists(vectorstore_path):
            return True
        
        # Get vectorstore creation time
        vectorstore_time = os.path.getmtime(vectorstore_path)
        
        # Check if any .txt files in college_data are newer than vectorstore
        if os.path.exists("college_data"):
            for root, dirs, files in os.walk("college_data"):
                for file in files:
                    if file.endswith('.txt'):
                        file_path = os.path.join(root, file)
                        if os.path.getmtime(file_path) > vectorstore_time:
                            logger.info(f"Found updated file: {file_path}, recreating vectorstore")
                            return True
        
        return False
    
    def _load_or_create_vectorstore(self):
        vectorstore_path = "vectorstore.pkl"
        
        # Check if we need to recreate vectorstore
        if self._should_recreate_vectorstore():
            logger.info("Creating/updating vectorstore with latest data...")
            self._create_vectorstore()
        else:
            try:
                with open(vectorstore_path, 'rb') as f:
                    self.vectorstore = pickle.load(f)
                logger.info("✅ Loaded existing vectorstore")
            except Exception as e:
                logger.error(f"❌ Failed to load vectorstore: {e}")
                self._create_vectorstore()
    
    def _create_vectorstore(self):
        logger.info("Creating new vectorstore with all college data...")
        
        if not os.path.exists("college_data"):
            os.makedirs("college_data")
        
        # Create default APSIT data if needed
        self._ensure_default_data()
        
        try:
            # Load all .txt files using safe text loader
            documents = []
            
            if os.path.exists("college_data"):
                for root, dirs, files in os.walk("college_data"):
                    for file in files:
                        if file.endswith('.txt'):
                            file_path = os.path.join(root, file)
                            logger.info(f"Loading file: {file_path}")
                            try:
                                loader = SafeTextLoader(file_path)
                                docs = loader.load()
                                documents.extend(docs)
                                logger.info(f"✅ Successfully loaded {file_path}")
                            except Exception as e:
                                logger.error(f"❌ Failed to load {file_path}: {e}")
                                continue
            
            logger.info(f"✅ Loaded {len(documents)} documents total")
            
            if not documents:
                logger.warning("No documents found in college_data directory")
                return
            
            # Split documents into chunks
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000,
                chunk_overlap=200
            )
            texts = text_splitter.split_documents(documents)
            logger.info(f"✅ Split into {len(texts)} text chunks")
            
            # Create vectorstore
            self.vectorstore = FAISS.from_documents(texts, self.embeddings)
            
            # Save vectorstore
            with open("vectorstore.pkl", 'wb') as f:
                pickle.dump(self.vectorstore, f)
            logger.info("✅ Vectorstore created and saved")
            
        except Exception as e:
            logger.error(f"❌ Error creating vectorstore: {e}")
            raise
    
    def _ensure_default_data(self):
        """Ensure default APSIT data exists"""
        apsit_file = "college_data/apsit_data.txt"
        if not os.path.exists(apsit_file):
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
- Bachelor of Engineering (B.E.) in CSE (AI and ML) - 4 years
- Bachelor of Engineering (B.E.) in CSE (Data Science) - 4 years

Contact Information:
Phone: +91-22-25397659 / +91-22-25397660
Email: info@apsit.edu.in
Website: www.apsit.edu.in
Address: Mumbai-Pune Highway, Thane West, Thane - 400615, Maharashtra."""
            
            with open(apsit_file, "w", encoding='utf-8') as f:
                f.write(apsit_data)
            logger.info("✅ Created default APSIT data")
    
    def _get_conversation_context(self, user_id: int, limit: int = 6) -> str:
        """Get recent conversation history for old-style conversations"""
        if user_id not in self.user_conversations:
            return ""
        
        recent_messages = self.user_conversations[user_id][-limit:]
        if not recent_messages:
            return ""
            
        context = "Previous conversation:\n"
        for msg in recent_messages:
            context += f"Student: {msg['question']}\nAssistant: {msg['answer']}\n\n"
        return context.strip()
    
    def _store_conversation(self, user_id: int, question: str, answer: str):
        """Store conversation in old-style memory"""
        if user_id not in self.user_conversations:
            self.user_conversations[user_id] = []
        
        self.user_conversations[user_id].append({
            'question': question,
            'answer': answer
        })
        
        # Keep only last 15 exchanges per user
        if len(self.user_conversations[user_id]) > 15:
            self.user_conversations[user_id] = self.user_conversations[user_id][-15:]
    
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
    
    # OLD METHOD: For backward compatibility with existing chat service
    def get_response(self, question: str, user_id: int) -> str:
        """Get response with old-style user memory (for backward compatibility)"""
        logger.info(f"Processing question from user {user_id} (old-style): {question}")
        
        try:
            # Get relevant documents
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
            relevant_docs = retriever.get_relevant_documents(question)
            
            college_context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Get old-style conversation history
            conversation_history = self._get_conversation_context(user_id)
            
            prompt = f"""You are APSIT's helpful college assistant. You have comprehensive information about APSIT including faculty details, departments, and all college information.

{conversation_history}

APSIT COLLEGE INFORMATION:
{college_context}

CURRENT QUESTION: {question}

INSTRUCTIONS:
- Use conversation context naturally (remember what the student told you before)
- Answer based on APSIT information including faculty details, department information, and all available college data
- If asked about faculty, provide specific names, qualifications, and experience from the faculty information
- If asked about departments, provide detailed information about faculty and programs
- Be helpful and conversational
- If you don't have specific APSIT information, say so clearly

ANSWER:"""

            response = self.llm.invoke(prompt)
            
            # Store in old-style memory
            self._store_conversation(user_id, question, response.content)
            
            logger.info(f"✅ Response generated (old-style)")
            return response.content
            
        except Exception as e:
            logger.error(f"❌ Error in get_response: {e}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again or contact APSIT at +91-22-25397659."
    
    # NEW METHOD: For session-based conversations
    def get_response_for_session(self, question: str, user_id: int, session_id: int) -> str:
        """Get response with session-specific memory"""
        logger.info(f"Processing question from user {user_id}, session {session_id}: {question}")
        
        try:
            # Get relevant documents
            retriever = self.vectorstore.as_retriever(search_kwargs={"k": 5})
            relevant_docs = retriever.get_relevant_documents(question)
            
            college_context = "\n\n".join([doc.page_content for doc in relevant_docs])
            
            # Get session-specific conversation history
            session_history = self._get_session_context(user_id, session_id)
            
            prompt = f"""You are APSIT's helpful college assistant. You have comprehensive information about APSIT including faculty details, departments, and all college information.

{session_history}

APSIT COLLEGE INFORMATION:
{college_context}

CURRENT QUESTION: {question}

INSTRUCTIONS:
- Use conversation context from THIS chat session
- Answer based on APSIT information including faculty details, department information, and all available college data
- If asked about faculty, provide specific names, qualifications, and experience from the faculty information
- If asked about departments, provide detailed information about faculty and programs
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
        if user_id in self.user_conversations:
            del self.user_conversations[user_id]
    
    def force_recreate_vectorstore(self):
        """Force recreation of vectorstore - useful when new data is added"""
        logger.info("Force recreating vectorstore...")
        self._create_vectorstore()

# Global RAG service instance
rag_service = RAGService()
