import React, { useState, useEffect } from "react";
import { Toaster, toast } from 'react-hot-toast';
import { Outlet, Link, useLocation, useNavigate } from "react-router-dom"; 
import { 
    MessageSquare, Settings, Check, X, BookOpen, ChevronDown, 
    UploadCloud, Plus, Clock, UserCircle, Menu, Shield, LogOut,
} from "lucide-react";
import logoImage from './assets/logo.jpg';
import { uiThemes, accentMap, themeModes } from "./constants/theme";
import { fetchCourses } from "./services/api"; 

const DashBoard = () => {
    const location = useLocation(); 
    const navigate = useNavigate(); 
    
    // --- STATE ---
    const [courses, setCourses] = useState([]);
    const [isLoadingCourses, setIsLoadingCourses] = useState(true);
    const [selectedSubject, setSelectedSubject] = useState(""); 
    
    const userString = localStorage.getItem('user');
    let initialUser = { name: 'Khách', role: 'student', avatar: '' };
    try {
        if (userString) initialUser = JSON.parse(userString);
    } catch (e) {
        console.error("Lỗi parse thông tin user:", e);
    }
    const [user] = useState(initialUser);
    const [role] = useState((user.role || "STUDENT").toUpperCase());
    
    const [showSettings, setShowSettings] = useState(false);
    const [uiMode, setUiMode] = useState("dark"); 
    const [accentColor, setAccentColor] = useState("blue"); 
    const [isSidebarOpen, setIsSidebarOpen] = useState(true);
    const [activeChatId, setActiveChatId] = useState(null); 
    const [chatHistory, setChatHistory] = useState([]);

    // --- CÔNG TẮC REFRESH LỊCH SỬ CHAT ---
    const [refreshTrigger, setRefreshTrigger] = useState(0);
    const refreshHistory = () => setRefreshTrigger(prev => prev + 1);

    const currentUi = uiThemes[uiMode];       
    const currentAccent = accentMap[accentColor]; 
    const isDarkTheme = uiMode === 'dark' || uiMode === 'grey';

    // 1. Tải danh sách môn học
    useEffect(() => {
        const loadCourses = async () => {
            try {
                setIsLoadingCourses(true);
                const data = await fetchCourses();
                const coursesList = Array.isArray(data) ? data : (data?.results || []);
                setCourses(coursesList);
                if (coursesList.length > 0) {
                    setSelectedSubject(coursesList[0].id.toString()); 
                }
            } catch (error) {
                console.error("Lỗi khi tải danh sách môn học:", error);
                setCourses([]); 
            } finally {
                setIsLoadingCourses(false);
            }
        };
        loadCourses();
    }, []);

    // 2. Tải Lịch sử Chat
    useEffect(() => {
        const loadChatHistory = async () => {
            try {
                const token = localStorage.getItem('accessToken');
                if (!token) return;

                const response = await fetch(`http://127.0.0.1:8000/api/chat/sessions/?t=${Date.now()}`, {
                    headers: { 
                        'Authorization': `Bearer ${token}`
                    }
                });

                if (response.ok) {
                    const data = await response.json();
                    const formattedHistory = data.map(session => ({
                        id: session.id,
                        title: session.title || `Phiên chat môn ${session.course_name || ''}`,
                        date: session.created_at ? new Date(session.created_at).toLocaleDateString() : 'Gần đây'
                    }));
                    setChatHistory(formattedHistory);
                }
            } catch (error) {
                console.error("Lỗi tải danh sách lịch sử chat:", error);
            }
        };

        loadChatHistory();
    }, [activeChatId, location.pathname, refreshTrigger]); 

    const handleNewChat = () => {
        setActiveChatId(null); 
        if (location.pathname !== '/chat') {
            navigate('/chat');
        }
        
        const inputEl = document.querySelector('input[type="text"]');
        if (inputEl) {
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set;
            nativeInputValueSetter.call(inputEl, '');
            const ev2 = new Event('input', { bubbles: true});
            inputEl.dispatchEvent(ev2);
        }
    };

    const handleLogout = () => {
        localStorage.removeItem('accessToken');
        localStorage.removeItem('refreshToken');
        localStorage.removeItem('user');
        navigate('/login');
    };

    return (
        <div className={`flex h-screen w-full ${currentUi.bg} ${currentUi.text} font-sans overflow-hidden transition-colors duration-300`}>
            {/* SIDEBAR */}
            <div 
                className={`h-full ${currentUi.sidebar} flex flex-col shrink-0 z-20 transition-all duration-300 ease-in-out overflow-hidden relative ${
                    isSidebarOpen ? `w-[280px] border-r ${currentUi.border}` : "w-0 border-r-0 opacity-0"
                }`}
            >
                <button 
                    onClick={() => setIsSidebarOpen(false)}
                    className={`absolute top-4 right-4 p-1.5 rounded-lg ${currentUi.hover} ${currentUi.subText} hover:${currentUi.text} transition-colors`}
                    title="Thu gọn menu"
                >
                    <Menu size={20} />
                </button>

                <div className="p-4 flex items-center gap-3 cursor-pointer min-w-[280px]" onClick={handleNewChat}>
                     <img src={logoImage} alt="EduBot Logo" className="w-8 h-8 object-cover rounded-full border border-gray-500" />
                     <div className={`font-bold text-xl tracking-tight ${currentUi.text}`}>
                        Edu<span className={currentAccent.text}>Bot</span>
                    </div>
                </div>

                <div className="px-4 mt-2 mb-4 min-w-[280px]">
                    <button 
                        onClick={handleNewChat} 
                        className={`w-full flex items-center gap-2 px-4 py-2.5 rounded-lg border border-dashed transition-all ${currentUi.border} hover:border-gray-400 ${currentUi.text} hover:bg-gray-500/10`}
                    >
                        <Plus size={18} />
                        <span className="font-medium text-sm">Đoạn chat mới</span>
                    </button>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar px-2 min-w-[280px]">
                    <div className={`text-xs font-bold ${currentUi.subText} px-4 py-2 mb-2 uppercase`}>Menu Chính</div>
                    <Link 
                        to="/chat" 
                        onClick={handleNewChat}
                        className={`flex items-center gap-3 px-4 py-3 text-sm rounded-lg w-full transition-all mb-1 ${
                            location.pathname === '/chat' && activeChatId === null 
                            ? `${currentAccent.bg} text-white shadow-md` 
                            : `${currentUi.subText} ${currentUi.hover} hover:${currentUi.text}`
                        }`}
                    >
                        <MessageSquare size={18} /> Chat với AI
                    </Link>

                    {(role === 'TEACHER' || role === 'ADMIN') && (
                        <Link to="/knowledge" className={`flex items-center gap-3 px-4 py-3 text-sm rounded-lg w-full transition-all mb-1 ${location.pathname === '/knowledge' ? `${currentAccent.bg} text-white shadow-md` : `${currentUi.subText} ${currentUi.hover} ${currentUi.text}`}`}>
                            <UploadCloud size={18} /> Quản lý Tài liệu 
                        </Link>
                    )}

                    {role === 'ADMIN' && (
                        <Link to="/admin" className={`flex items-center gap-3 px-4 py-3 text-sm rounded-lg w-full transition-all mb-1 ${location.pathname === '/admin' ? `${currentAccent.bg} text-white shadow-md` : `${currentUi.subText} ${currentUi.hover} ${currentUi.text}`}`}>
                            <Shield size={18} /> Quản lý Hệ thống
                        </Link>
                    )}

                    {/* HIỂN THỊ LỊCH SỬ CHAT TỪ API */}
                    <div className={`text-xs font-bold ${currentUi.subText} px-4 pt-6 pb-2 uppercase flex items-center gap-2`}>
                        <Clock size={14}/> Lịch sử
                    </div>
                    <div className="space-y-1">
                        {chatHistory.length === 0 ? (
                            <div className={`px-4 py-2 text-xs italic ${currentUi.subText}`}>Chưa có cuộc trò chuyện nào</div>
                        ) : (
                            chatHistory.map((chat) => (
                                <Link 
                                    to="/chat" key={chat.id} 
                                    onClick={() => setActiveChatId(chat.id)}
                                    className={`w-full text-left flex items-center gap-3 px-4 py-2.5 text-sm rounded-lg transition-all mb-1 
                                    ${String(activeChatId) === String(chat.id) && location.pathname === '/chat'
                                        ? `${currentAccent.bg} text-white shadow-md font-medium` 
                                        : `${currentUi.subText} ${currentUi.hover} hover:${currentUi.text}`
                                    }`}
                                >
                                    <MessageSquare size={16} className="shrink-0 opacity-70" /> 
                                    <div className="truncate flex-1">
                                        <div>{chat.title}</div>
                                        <div className="text-[10px] opacity-60 mt-0.5">{chat.date}</div>
                                    </div>
                                </Link>
                            ))
                        )}
                    </div>
                </div>

                <div className={`p-4 mt-auto border-t ${currentUi.border} space-y-2 min-w-[280px]`}>
                    <button onClick={() => setShowSettings(true)} className={`flex items-center gap-3 px-4 py-3 ${currentUi.hover} rounded-lg cursor-pointer transition-all w-full text-left ${currentUi.subText} hover:${currentUi.text}`}>
                        <Settings size={18} /> <span className="text-sm font-medium">Cài đặt giao diện</span>
                    </button>
                </div>
            </div>

            {/* MAIN CONTENT */}
            <div className="flex-1 flex flex-col h-full overflow-hidden min-w-0 relative">
                <div className={`h-16 flex items-center px-6 ${currentUi.bg} border-b ${currentUi.border} shrink-0 transition-colors duration-300 ${!isSidebarOpen ? 'justify-between' : 'justify-end'}`}>
                    {!isSidebarOpen && (
                        <button 
                            onClick={() => setIsSidebarOpen(true)} 
                            className={`p-2 rounded-lg transition-all ${currentUi.hover} ${currentUi.text} hover:opacity-80`}
                            title="Mở menu"
                        >
                            <Menu size={22} />
                        </button>
                    )}
                    
                    <div className="flex items-center gap-4">
                        {/* <div className={`relative group flex items-center ${currentUi.dropdownBg} ${currentUi.dropdownBorder} border rounded-xl shadow-sm transition-all`}>
                            <div className={`pl-3 pointer-events-none ${currentUi.text}`}><BookOpen size={16} /></div>
                            <select 
                                value={selectedSubject}
                                onChange={(e) => setSelectedSubject(e.target.value)}
                                className={`appearance-none cursor-pointer pl-2 pr-9 py-2 rounded-xl text-sm font-semibold bg-transparent focus:outline-none ${currentUi.text} w-full max-w-[160px] truncate`}
                                disabled={isLoadingCourses}
                            >
                                {isLoadingCourses ? (
                                    <option value="" disabled>Đang tải...</option>
                                ) : courses?.length === 0 ? (
                                    <option value="" disabled>Không có môn học</option>
                                ) : (
                                    courses?.map((course) => (
                                        <option 
                                            key={course.id} 
                                            value={course.id} 
                                            className={isDarkTheme ? "bg-[#2d2e30] text-gray-100" : "bg-white text-gray-800"}
                                        >
                                            {course.name}
                                        </option>
                                    ))
                                )}
                            </select>
                            <div className={`absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none ${currentUi.subText}`}><ChevronDown size={14} /></div>
                        </div> */}

                        <div className={`flex items-center gap-3 pl-4 ml-2 border-l ${currentUi.border}`}>
                            <div className="text-right hidden sm:block">
                                <p className={`text-sm font-bold ${currentUi.text}`}>{user.name}</p>
                                <p className={`text-[10px] font-bold tracking-wider ${currentAccent.text} uppercase`}>{role}</p>
                            </div>
                            
                            {user.avatar ? (
                                <img src={user.avatar} alt="Avatar" className="w-8 h-8 rounded-full border border-gray-500 object-cover" />
                            ) : (
                                <UserCircle size={32} className={currentUi.subText} />
                            )}

                            <button 
                                onClick={handleLogout}
                                className={`p-2 rounded-lg transition-all hover:bg-red-500 hover:text-white ${currentUi.subText} group`}
                                title="Đăng xuất"
                            >
                                <LogOut size={18} className="group-hover:scale-110 transition-transform" />
                            </button>
                        </div>
                    </div>
                </div>

                <div className="flex-1 overflow-y-auto custom-scrollbar relative">
                    <Outlet context={{ currentUi, currentAccent, uiMode, selectedSubject, role, activeChatId, setActiveChatId, user, refreshHistory }} />
                </div>
            </div>
            
            {/* SETTINGS MODAL */}
            {showSettings && (
                <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex justify-center items-center">
                    <div className={`w-[400px] rounded-2xl shadow-xl overflow-hidden border ${currentUi.border} ${currentUi.modalBg}`}>
                        <div className={`flex justify-between items-center px-6 py-4 border-b ${currentUi.border}`}>
                            <h3 className={`font-semibold ${currentUi.text}`}>Cài đặt giao diện</h3>
                            <button 
                                onClick={() => setShowSettings(false)}
                                className={`p-1 rounded-md ${currentUi.hover} ${currentUi.subText} hover:${currentUi.text}`}
                            >
                                <X size={20} />
                            </button>
                        </div>
                        
                        <div className="p-6 space-y-6">
                            <div>
                                <h4 className={`text-sm font-medium mb-3 ${currentUi.text}`}>Màu nền (Theme)</h4>
                                <div className="grid grid-cols-3 gap-3">
                                    {themeModes.map((theme) => {
                                        const Icon = theme.icon;
                                        return (
                                            <button
                                                key={theme.id}
                                                onClick={() => setUiMode(theme.id)}
                                                className={`flex flex-col items-center gap-2 p-3 rounded-xl border-2 transition-all ${
                                                    uiMode === theme.id 
                                                        ? `${currentAccent.border} bg-${accentColor}-500/10` 
                                                        : `${currentUi.border} hover:border-gray-400 ${currentUi.inputBg}`
                                                }`}
                                            >
                                                <Icon size={24} className={uiMode === theme.id ? currentAccent.text : currentUi.subText} />
                                                <span className={`text-xs font-medium ${uiMode === theme.id ? currentAccent.text : currentUi.text}`}>
                                                    {theme.label}
                                                </span>
                                            </button>
                                        )
                                    })}
                                </div>
                            </div>

                            <div>
                                <h4 className={`text-sm font-medium mb-3 ${currentUi.text}`}>Màu chủ đạo (Accent)</h4>
                                <div className="flex gap-4">
                                    {Object.entries(accentMap).map(([colorName, colorValue]) => (
                                        <button
                                            key={colorName}
                                            onClick={() => setAccentColor(colorName)}
                                            className={`w-8 h-8 rounded-full flex items-center justify-center transition-all ${colorValue.bg} ${
                                                accentColor === colorName ? 'ring-4 ring-offset-2 ring-offset-transparent ring-white/30 scale-110' : 'hover:scale-110'
                                            }`}
                                        >
                                            {accentColor === colorName && <Check size={16} className="text-white" />}
                                        </button>
                                    ))}
                                </div>
                            </div>
                        </div>

                        <div className={`px-6 py-4 border-t ${currentUi.border} flex justify-end`}>
                            <button 
                                onClick={() => setShowSettings(false)}
                                className={`px-4 py-2 rounded-lg text-sm font-medium text-white transition-colors ${currentAccent.bg} hover:opacity-90`}
                            >
                                Hoàn tất
                            </button>
                        </div>
                    </div>
                </div>
            )}
            
            <Toaster position="top-right" />
        </div>
    );
};

export default DashBoard;