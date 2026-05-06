from .models import ChatSession, ChatMessage, Course
import chromadb
import time
from django.conf import settings
from django.http import StreamingHttpResponse

from rest_framework.response import Response
from rest_framework import status

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_huggingface import HuggingFaceEmbeddings

from langchain_chroma import Chroma
from langchain.chains import create_retrieval_chain, create_history_aware_retriever
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage

#config
MAX_HISTORY_CHARS = 1000
MAX_MESSAGE_CHARS = 300

chroma_client = chromadb.HttpClient(
    host=settings.CHROMA_HOST, 
    port=settings.CHROMA_PORT
)

embeddings = HuggingFaceEmbeddings(
    model_name="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
)

vectorstore = Chroma(
    client=chroma_client,
    embedding_function=embeddings,
    collection_name=settings.CHROMA_COLLECTION_NAME
)

retriever_cache = {}

def get_retriever(course_id=None):
    key = course_id or "default"
    if key not in retriever_cache:
        search_kwargs = {"k": 7}
        if course_id:
            search_kwargs["filter"] = {"course_id": course_id}
        retriever_cache[key] = vectorstore.as_retriever(search_kwargs=search_kwargs)
    return retriever_cache[key]

def trim_message(msg):
    if not msg:
        return ""
    return str(msg)[:MAX_MESSAGE_CHARS]

def build_chat_history(raw_chat_history):
    chat_history = []
    total_chars = 0
    for msg in reversed(raw_chat_history[-6:]):
        content = trim_message(msg.get("content"))
        if total_chars + len(content) > MAX_HISTORY_CHARS:
            break
        total_chars += len(content)
        if msg.get("role") == "user":
            chat_history.insert(0, HumanMessage(content=content))
        else:
            chat_history.insert(0, AIMessage(content=content))
    return chat_history

def safe_invoke(chain, payload, retry=3):
    for i in range(retry):
        try:
            return chain.invoke(payload)
        except Exception as e:
            print(f"[Retry {i+1}] Gemini error: {e}")
            time.sleep(1)
    raise Exception("Gemini failed after retries")

def generate_chat_response(user_message, raw_chat_history, course_id=None, model_name="gemini-2.5-flash"):
    try:
        if not user_message or not user_message.strip():
            yield "Vui lòng nhập câu hỏi."
            return 
        
        chat_history = build_chat_history(raw_chat_history)
        retriever = get_retriever(course_id)
        
        # SỬ DỤNG ĐÚNG MODEL NGƯỜI DÙNG ĐÃ CHỌN
        llm = ChatGoogleGenerativeAI(model=model_name, temperature=0.3, streaming=True)
        search_query = user_message
        
        if chat_history:
            rewrite_prompt = ChatPromptTemplate.from_messages([
                ("system", "Dựa trên lịch sử trò chuyện, hãy viết lại câu hỏi mới nhất thành một câu hỏi độc lập và rõ nghĩa. KHÔNG trả lời, CHỈ viết lại câu hỏi. Nếu không cần viết lại thì trả về đúng nguyên bản."),
                MessagesPlaceholder("chat_history"),
                ("human", "{input}")
            ])
            rewrite_chain = rewrite_prompt | llm
            rewritten_msg = safe_invoke(rewrite_chain, {
                "chat_history": chat_history, 
                "input": user_message
            })
            search_query = rewritten_msg.content.strip()

            time.sleep(1)
        
        docs = retriever.invoke(search_query)
        
        print("====== TEST CHROMA DB ======")
        for i, doc in enumerate(docs):
            print(f"Chunk {i+1}: {doc.page_content}")
            print(f"Meta: {doc.metadata}")
        
        if len(docs) == 0:
            yield "Xin lỗi, tôi không tìm thấy thông tin này trong kho tài liệu."
            return
        
        qa_system_prompt = (
            "Bạn là một trợ lý AI thông minh, hỗ trợ sinh viên giải đáp thắc mắc về môn học.\n"
            "Hãy sử dụng CHỈ các thông tin từ tài liệu được cung cấp dưới đây để trả lời câu hỏi.\n"
            "Nếu thông tin không có trong tài liệu, thành thật nói 'Xin lỗi, tôi không tìm thấy thông tin này', không bịa kiến thức.\n"
            "QUY TẮC TRẢ LỜI:\n"
            "1. NGÔN NGỮ: BẮT BUỘC phải trả lời bằng CHÍNH NGÔN NGỮ mà người dùng đã sử dụng để đặt câu hỏi.\n"
            "2. CUNG CẤP THÔNG TIN ĐẦY ĐỦ: Hãy trả lời chi tiết, diễn đạt tự nhiên và trình bày rõ ràng (dùng markdown, bullet point nếu cần).\n"
            "3. ĐI ĐÚNG TRỌNG TÂM: Chỉ giải quyết chính xác những gì người dùng đang hỏi.\n"
            "4. KHÔNG lan man sang các phần kiến thức dư thừa không được yêu cầu.\n\n"
            "TÀI LIỆU CUNG CẤP:\n"
            "{context}"
        )
        
        qa_prompt = ChatPromptTemplate.from_messages([
            ("system", qa_system_prompt),
            ("human", "{input}"),
        ])  

        question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
        
        for chunk in question_answer_chain.stream({"input": search_query, "context": docs}):
            word = ""
            if isinstance(chunk, dict) and "answer" in chunk:
                word = chunk["answer"]
            elif isinstance(chunk, str):
                word = chunk
            elif hasattr(chunk, 'content'):
                word = chunk.content

            if word:
                yield word
        
        sources = set() 
        for doc in docs:
            metadata = doc.metadata
            title = metadata.get("title", "Tài liệu không tên") # Đề phòng title bị None
            source = metadata.get("source", "")
            source_url = metadata.get("source_url", "")
            
            if title:
                sources.add((title, source, source_url))

        if sources:
            # Sắp xếp theo title -> source -> url
            sorted_sources = sorted(sources, key=lambda x: (x[0], x[1], x[2]))
            
            source_text = "\n\n---\n**📚 Thông tin tham khảo:**\n"
            
            for t, s, s_url in sorted_sources:
                # Nếu có URL thì làm Markdown link, không thì in text thường
                if s_url: 
                    source_text += f'* [{t}]({s_url}) (Nguồn: {s})\n'
                else:
                    source_text += f'* {t} (Nguồn: {s})\n'
                    
            yield source_text

    except Exception as e:
        print(f"Lỗi khi gọi Gemini: {e}")
        # Lỗi mạng thực sự mới in ra câu này
        yield f"\n\n*(Lỗi kết nối: {str(e)})*"
    
def process_chat_message(user, data: dict) -> dict:
    #course_id = data.get('course_id','')
    user_text = data.get('message')
    session_id = data.get('session_id')
    model_name = data.get('model_name', 'gemini-2.5-flash') # LẤY MODEL TỪ FRONTEND

    # try:
    #     course = Course.objects.get(id=course_id)
    # except Course.DoesNotExist:
    #     return {"success": False, "error": "The subject does not exist."}

    if session_id:
        try:
            session = ChatSession.objects.get(id=session_id, user=user)
        except ChatSession.DoesNotExist:
            return {"success": False, "error": "Invalid chat session."}
    else:
        title = user_text[:30] + "..." if len(user_text) > 30 else user_text
        session = ChatSession.objects.create(user=user, title=title)

    ChatMessage.objects.create(session=session, sender_role='user', content=user_text)

    recent_messages = ChatMessage.objects.filter(session_id=session_id).order_by('-created_at')[:6]
    recent_messages = reversed(recent_messages)
    
    raw_chat_history = []
    for msg in recent_messages:
        role = 'user' if msg.sender_role else 'ai' 
        raw_chat_history.append({'role': role, 'content': msg.content})
    
    def stream_and_save():
        full_ai_content = ""
        # TRUYỀN model_name XUỐNG HÀM GENERATE
        ai_generator = generate_chat_response(
            user_message=user_text, 
            raw_chat_history=raw_chat_history,
            model_name=model_name
        )

        for chunk in ai_generator:
            full_ai_content += chunk
            clean_chunk = chunk.replace('\n', '\\n')
            # Thêm khoảng nghỉ cực nhỏ để React render mượt hơn
            yield f"data: {clean_chunk}\n\n"

        if full_ai_content.strip():
            ChatMessage.objects.create(session=session, sender_role='ai', content=full_ai_content)

        yield "data: [DONE]\n\n"

    return True, stream_and_save, session.id
    
def get_user_chat_sessions(user_id: int, course_id: int = None):
    sessions = ChatSession.objects.filter(user_id=user_id).order_by('-created_at')
    if course_id is not None:
        sessions = sessions.filter(course_id=course_id)
    return sessions

def get_user_chat(user_id: int, session_id: int, before: int = None, limit: int = 20):

    if session_id is None:
        return Response({"error": "session_id is required"},status=status.HTTP_400_BAD_REQUEST)
    chats = ChatMessage.objects.filter(session_id=session_id, session__user_id=user_id)
    if before:
        chats = chats.filter(id__lt=before)
    return chats.order_by('-id')[:limit]