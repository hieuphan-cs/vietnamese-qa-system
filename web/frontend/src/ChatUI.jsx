import React, { useState, useEffect, useRef } from "react";
import { Send, Plus, Sparkles, Brain, Bot, Zap, ChevronDown, AlertCircle } from "lucide-react";
import { useOutletContext } from "react-router-dom"; 
import CodeBlock from "./components/CodeBlock";
import QuizBlock from "./components/Quiz"; 
import { fetchCourses } from './services/api'; 
import toast, { Toaster } from "react-hot-toast";
import ReactMarkdown from "react-markdown";

// 1. MẢNG MODELS
const models = [
    { 
        id: 'gemini-3-flash-preview', 
        name: 'Gemini 3 Flash preview', 
        desc: 'Thế hệ 3 siêu tốc độ (Bản Preview)', 
        icon: '⚡' 
    },
    { 
        id: 'gemini-2.5-flash', 
        name: 'Gemini 2.5 Flash', 
        desc: 'Cân bằng giữa tốc độ và khả năng xử lý', 
        icon: '🧠' 
    }
];

const ChatUI = () => {
    const { currentUi, currentAccent, uiMode, selectedSubject, activeChatId, setActiveChatId, refreshHistory } = useOutletContext();
    
    const [input, setInput] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [courses, setCourses] = useState([]); 
    const [messages, setMessages] = useState([]);
    
    const [selectedModel, setSelectedModel] = useState(models[0].id);
    const [showModelMenu, setShowModelMenu] = useState(false);

    const messagesEndRef = useRef(null);
    const inputRef = useRef(null);
    const isCreatingNewChatRef = useRef(false);

    // Tự động cuộn xuống cuối chat
    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages, isLoading]);

    // Lấy danh sách môn học để mapping ID
    useEffect(() => {
        const getCourses = async () => {
            try {
                const data = await fetchCourses();
                setCourses(data);
            } catch (error) { 
                console.error("Lỗi fetch môn học:", error); 
                toast.error("Không thể tải danh sách môn học.");
            }
        };
        getCourses();
    }, []);

    // Load tin nhắn khi đổi Chat hoặc đổi Môn 
    useEffect(() => {
        const loadChatContent = async () => {
            
            if (isCreatingNewChatRef.current) return;

            let subjectDisplayName = selectedSubject; 
            
            if (courses && courses.length > 0) {
                const foundCourse = courses.find(c => 
                    c.id.toString() === selectedSubject?.toString() || 
                    c.name === selectedSubject
                );
                if (foundCourse) {
                    subjectDisplayName = foundCourse.name; 
                }
            }

            if (activeChatId) {
                console.log("Đang tải lịch sử cho chat ID:", activeChatId);
                try {
                    const token = localStorage.getItem('accessToken');
                    const res = await fetch(`http://127.0.0.1:8000/api/chat/sessions/${activeChatId}/`, {
                        headers: { 'Authorization': `Bearer ${token}` }
                    });
                    
                    if (res.ok) {
                        const data = await res.json();
                        const messageList = Array.isArray(data) ? data : (data?.results || []);
                        const formattedHistory = messageList.map(msg => ({
                            id: `history-${msg.id}`,
                            sender: msg.sender_role === 'ai' ? 'bot' : 'user',
                            text: msg.content
                        })).reverse();
                        
                        setMessages(formattedHistory);
                    } else {
                        const errData = await res.json().catch(() => ({}));
                        toast.error(errData.message || "Không thể tải lịch sử chat");
                    }
                } catch (error) {
                    console.error("Lỗi tải lịch sử chat:", error);
                    toast.error("Lỗi kết nối khi tải lịch sử");
                }
            } else {
                setMessages([{ 
                    id: 'welcome-msg', 
                    sender: "bot", 
                    //text: `Xin chào! Tôi là trợ lý AI của môn **${subjectDisplayName}**. Hôm nay bạn muốn tìm hiểu về nội dung gì?`
                    text: `Xin chào! Tôi là trợ lý AI về quy chế của trường đại học Tôn Đức Thắng. Hôm nay bạn muốn tìm hiểu về nội dung gì?` 
                }]);
            }
            inputRef.current?.focus();
        };
        
        loadChatContent();
    }, [activeChatId, selectedSubject, courses]);

    const handleSend = async () => {
        if (!input.trim() || isLoading) return;
        
        if (!activeChatId) {
            isCreatingNewChatRef.current = true;
        }

        const userText = input;
        
        const now = Date.now();
        const userMsgId = `user-${now}`;
        const botMsgId = `bot-${now}`; 
        
        setInput("");
        setIsLoading(true);

        setMessages(prev => [
            ...prev, 
            { id: userMsgId, sender: "user", text: userText },
            { id: botMsgId, sender: "bot", text: "" }
        ]);

        try {
            const currentCourse = courses.find(c => c.name === selectedSubject || c.id.toString() === selectedSubject);
            const courseIdToSend = currentCourse ? currentCourse.id : selectedSubject;
            const token = localStorage.getItem('accessToken');

            const response = await fetch('http://127.0.0.1:8000/api/chat/send/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    message: userText,
                    session_id: activeChatId, 
                    model_name: selectedModel
                })
            });

            if (!response.ok) {
                const errData = await response.json().catch(() => ({}));
                throw new Error(errData.message || "Lỗi từ server");
            }

            const newSessionId = response.headers.get('X-Chat-Session-Id');
            console.log("Check ID:", newSessionId)
            if (!activeChatId && newSessionId && setActiveChatId) {
                setActiveChatId(Number(newSessionId)); 
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder('utf-8');
            setIsLoading(false);

            while (true) {
                const { value, done } = await reader.read();
                if (done) break;
                
                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n\n');
                
                for (const line of lines) {
                    if (line.startsWith('data: ')) {
                        const dataText = line.substring(6);
                        if (dataText.trim() === '[DONE]') break;
                        
                        try {
                            const parsedData = JSON.parse(dataText);
                            const actualText = parsedData.content || ""; 
                            const cleanText = actualText.replace(/\\n/g, '\n');
                            
                            setMessages(prev => prev.map(msg => 
                                msg.id === botMsgId && msg.sender === 'bot' ? { ...msg, text: msg.text + cleanText } : msg
                            ));
                        } catch (e) {
                            const cleanText = dataText.replace(/\\n/g, '\n');
                            setMessages(prev => prev.map(msg => 
                                msg.id === botMsgId && msg.sender === 'bot' ? { ...msg, text: msg.text + cleanText } : msg
                            ));
                        }
                    }
                }
            }
            if (!activeChatId && refreshHistory) {
                setTimeout(() => {
                    refreshHistory();
                }, 500);
            }

        } catch (error) {
            console.error("Lỗi gửi tin nhắn:", error);
            setIsLoading(false);
            toast.error(error.message || "❌ Lỗi kết nối. Vui lòng kiểm tra mạng hoặc Server.");
            setMessages(prev => prev.map(msg => 
                msg.id === botMsgId && msg.sender === 'bot' ? { ...msg, text: "❌ Xin lỗi, đã có lỗi xảy ra. Vui lòng thử lại." } : msg
            ));
        } finally {
            
            isCreatingNewChatRef.current = false;
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-full relative overflow-hidden">
            <Toaster position="top-center" reverseOrder={false} />

            {/* Vùng tin nhắn */}
            <div className="flex-1 overflow-y-auto custom-scrollbar">
                <div className="max-w-[850px] mx-auto px-4 pb-40 pt-8 space-y-8">
                    {messages.map((msg) => (
                        <div key={msg.id} className={`flex gap-4 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'} animate-in fade-in duration-300`}>
                            {msg.sender === 'bot' && (
                                <div className={`w-9 h-9 rounded-full flex items-center justify-center shrink-0 mt-1 border shadow-sm ${currentUi.border} ${uiMode === 'light' ? 'bg-white' : 'bg-gray-800'}`}>
                                    <Bot size={18} className={currentAccent.text} />
                                </div>
                            )}
                            <div className={`group relative ${msg.sender === 'bot' 
                                ? `${currentUi.text} ${currentUi.msgBotBg} ${uiMode === 'light' ? 'p-5 rounded-2xl shadow-sm border border-gray-100' : ''} max-w-[90%]` 
                                : `${currentAccent.bg} text-white px-6 py-3 rounded-[24px] max-w-[80%] shadow-md`}`}>
                                
                                {msg.quizData ? (
                                    <QuizBlock data={msg.quizData} />
                                ) : msg.sender === 'bot' ? (
                                    /* ĐÃ SỬA: Thay nguyên đống class lằng nhằng bằng prose và max-w-none */
                                    <div className="prose prose-sm max-w-none text-[15px] leading-relaxed dark:prose-invert">
                                        <ReactMarkdown
                                            components={{
                                                code({ node, inline, className, children, ...props }) {
                                                    return !inline ? (
                                                        <div className="my-3 not-prose"> {/* Thêm not-prose để Tailwind không can thiệp vào CodeBlock của bạn */}
                                                            <CodeBlock code={String(children).replace(/\n$/, '')} />
                                                        </div>
                                                    ) : (
                                                        <code className="bg-black/10 dark:bg-white/10 px-1.5 py-0.5 rounded-md text-sm font-mono text-red-500" {...props}>
                                                            {children}
                                                        </code>
                                                    );
                                                }
                                            }}
                                        >
                                            {msg.text}
                                        </ReactMarkdown>
                                    </div>
                                ) : (
                                    <span className="whitespace-pre-wrap">{msg.text}</span>
                                )}
                                
                                {/* Nút copy ẩn - chỉ hiện khi hover */}
                                {msg.sender === 'bot' && msg.text && (
                                    <div className="absolute -bottom-6 left-2 opacity-0 group-hover:opacity-100 transition-opacity text-[10px] uppercase font-bold tracking-widest opacity-50">
                                        EduBot Response
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                    {isLoading && (
                        <div className="flex gap-4 items-center px-2 opacity-60">
                            <div className="animate-spin text-blue-500"><Sparkles size={16}/></div>
                            <span className="text-xs font-medium italic">AI đang phân tích tài liệu...</span>
                        </div>
                    )}
                    <div ref={messagesEndRef} />
                </div>
            </div>

            {/* THANH INPUT */}
            <div className={`absolute bottom-0 left-0 w-full bg-gradient-to-t ${uiMode === 'light' ? 'from-white via-white/90' : 'from-[#131314] via-[#131314]/90'} to-transparent pb-8 pt-12 z-10`}>
                <div className="max-w-[850px] mx-auto px-4">
                    <div className={`relative ${currentUi.inputBg} rounded-[32px] flex items-center p-2 border-2 shadow-lg transition-all focus-within:shadow-xl ${currentUi.border} focus-within:${currentAccent.border}`}>
                        {/* Ô Input */}
                        <input
                            ref={inputRef}
                            type="text"
                            className={`flex-1 bg-transparent border-none outline-none ${currentUi.text} px-3 py-2 text-[15px]`}
                            placeholder={`Hỏi trí tuệ nhân tạo (${models.find(m => m.id === selectedModel).name})...`}
                            value={input}
                            onChange={(e) => setInput(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSend()}
                        />

                        {/* Nhóm nút bên phải */}
                        <div className="flex items-center gap-1.5 pr-1">
                            
                            {/* NÚT CHỌN MODEL */}
                            <div className="relative">
                                <button 
                                    onClick={() => setShowModelMenu(!showModelMenu)}
                                    className={`flex items-center gap-1.5 px-3 py-2 rounded-full text-xs font-bold transition-all ${currentUi.hover} ${currentUi.subText} hover:${currentUi.text} border border-transparent hover:border-gray-400/30`}
                                >
                                    {models.find(m => m.id === selectedModel).icon}
                                    <span className="hidden md:inline">{models.find(m => m.id === selectedModel).name}</span>
                                    <ChevronDown size={14} className={showModelMenu ? "rotate-180 transition-transform" : "transition-transform"} />
                                </button>

                                {showModelMenu && (
                                    <div className={`absolute bottom-full right-0 mb-4 w-56 rounded-2xl border shadow-2xl z-[60] ${currentUi.modalBg} ${currentUi.border} overflow-hidden animate-in fade-in slide-in-from-bottom-4`}>
                                        <div className={`px-4 py-3 text-[11px] font-black uppercase tracking-tighter opacity-40 ${currentUi.text} border-b ${currentUi.border}`}>
                                            Mô hình ngôn ngữ
                                        </div>
                                        {models.map((m) => (
                                            <button
                                                key={m.id}
                                                onClick={() => { setSelectedModel(m.id); setShowModelMenu(false); }}
                                                className={`w-full flex items-center justify-between px-4 py-4 hover:bg-black/5 transition-colors ${selectedModel === m.id ? `${currentAccent.text} bg-black/5` : currentUi.text}`}
                                            >
                                                <div className="flex flex-col items-start">
                                                    <div className="flex items-center gap-2 font-bold text-sm">{m.icon} {m.name}</div>
                                                    <div className="text-[10px] opacity-60 font-medium">{m.desc}</div>
                                                </div>
                                                {selectedModel === m.id && <Zap size={14} className="fill-current" />}
                                            </button>
                                        ))}
                                    </div>
                                )}
                            </div>

                            {/* NÚT GỬI */}
                            <button 
                                onClick={handleSend} 
                                disabled={!input.trim() || isLoading} 
                                className={`p-3 rounded-full transition-all ${
                                    input.trim() 
                                    ? `${currentAccent.bg} text-white shadow-md hover:scale-105 active:scale-95` 
                                    : `bg-transparent ${currentUi.subText} opacity-10 cursor-not-allowed`
                                }`}
                            >
                                <Send size={20} />
                            </button>
                        </div>
                    </div>
                    <div className="flex justify-center items-center gap-2 mt-3 opacity-30">
                        <AlertCircle size={10} className={currentUi.subText} />
                        <p className={`text-[10px] font-medium ${currentUi.subText}`}>
                            Hệ thống AI có thể đưa ra câu trả lời nhầm lẫn.
                        </p>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default ChatUI;