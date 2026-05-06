import React, { useState, useEffect } from "react";
import { 
    UploadCloud, FileSpreadsheet, Users, Trash2, Edit2, Plus, 
    X, Loader2, Search, BookOpen, Check, Shield, GraduationCap, Briefcase 
} from 'lucide-react';
import { useOutletContext } from "react-router-dom";
import toast from 'react-hot-toast';

import { fetchUsers, createUser, updateUser, deleteUser, importUserExcel, fetchCourses, fetchUserCourses, updateUserCourses, importCourseExcel, importMemberCourseExcel } from './services/api';

const Admin = () => {
    const { currentUi, currentAccent } = useOutletContext();
    const theme = currentUi;
    const accent = currentAccent;

    // --- STATE QUẢN LÝ USER ---
    const [users, setUsers] = useState([]);
    const [searchTerm, setSearchTerm] = useState("");
    const [activeTab, setActiveTab] = useState('ALL'); // MỚI: State quản lý Tab hiện tại
    const [isLoading, setIsLoading] = useState(false);
    const [isImporting, setIsImporting] = useState(false);
    const [importType, setImportType] = useState('user');
    
    // --- STATE MODAL USER (Thêm/Sửa) ---
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [modalMode, setModalMode] = useState('add'); 
    const [editingId, setEditingId] = useState(null);
    // ĐÃ SỬA: Đổi role mặc định thành chữ IN HOA 'STUDENT'
    const [formData, setFormData] = useState({ name: '', email: '', role: 'STUDENT' });

    // --- STATE QUẢN LÝ GÁN MÔN HỌC ---
    const [isAssignModalOpen, setIsAssignModalOpen] = useState(false);
    const [selectedUser, setSelectedUser] = useState(null);
    const [courses, setCourses] = useState([]); 
    const [assignedCourseIds, setAssignedCourseIds] = useState([]); 
    const [isSavingAssign, setIsSavingAssign] = useState(false);

    // --- FETCH DATA ---
    const loadData = async () => {
        setIsLoading(true);
        try {
            const [usersData, coursesData] = await Promise.all([
                fetchUsers(),
                fetchCourses() 
            ]);
            setUsers(usersData); 
            setCourses(coursesData);
        } catch (error) {
            toast.error("Không thể tải dữ liệu hệ thống");
        } finally {
            setIsLoading(false);
        }
    };

    useEffect(() => { 
        loadData(); 
    }, []);

    // MỚI: LOGIC LỌC USER (KẾT HỢP TAB VÀ SEARCH BAR)
    const filteredUsers = users.filter(u => {
        const userRole = (u.role || 'STUDENT').toUpperCase();
        
        // 1. Lọc theo Tab
        if (activeTab !== 'ALL' && userRole !== activeTab) {
            return false;
        }

        // 2. Lọc theo thanh tìm kiếm
        const nameToSearch = (u.name || u.username || '').toLowerCase();
        const emailToSearch = (u.email || '').toLowerCase();
        const term = searchTerm.toLowerCase();
        
        return nameToSearch.includes(term) || emailToSearch.includes(term);
    });

    // --- HANDLERS USER CRUD ---
    const handleOpenAdd = () => {
        setModalMode('add');
        // ĐÃ SỬA: Đổi role mặc định thành IN HOA
        setFormData({ name: '', email: '', role: 'STUDENT' });
        setIsModalOpen(true);
    };

    const handleOpenEdit = (user) => {
        setModalMode('edit');
        setEditingId(user.id);
        setFormData({
            name: user.name || user.username || '', 
            email: user.email || '',
            // ĐÃ SỬA: Ép về IN HOA để gửi cho Backend chuẩn xác
            role: user.role?.toUpperCase() || 'STUDENT'
        });
        setIsModalOpen(true);
    };

    const handleSubmitUser = async (e) => {
        e.preventDefault();
        const loadingToast = toast.loading("Đang lưu dữ liệu...");
        try {
            if (modalMode === 'add') {
                await createUser(formData);
                toast.success("Thêm người dùng thành công!", { id: loadingToast });
            } else {
                await updateUser(editingId, formData);
                toast.success("Cập nhật thành công!", { id: loadingToast });
            }
            setIsModalOpen(false);
            loadData(); 
        } catch (error) {
            toast.error("Thất bại. Vui lòng kiểm tra lại!", { id: loadingToast });
        }
    };

    const handleDeleteClick = async (id) => {
        if (!window.confirm("Bạn có chắc chắn muốn xóa người dùng này?")) return;
        try {
            await deleteUser(id);
            toast.success("Đã xóa người dùng!");
            setUsers(users.filter(u => u.id !== id));
        } catch (error) {
            toast.error("Lỗi không thể xóa user!");
        }
    };

    const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    setIsImporting(true);
    const importToast = toast.loading(`Đang xử lý file: ${file.name}...`);

    try {
        let result;
        // Dựa vào lựa chọn của Dropdown để gọi đúng API
        if (importType === 'user') {
            result = await importUserExcel(file);
        } else if (importType === 'course') {
            result = await importCourseExcel(file);
        } else if (importType === 'member') {
            result = await importMemberCourseExcel(file);
        }
        
        toast.success(result.message || "Import dữ liệu thành công!", { id: importToast, duration: 5000 });
        loadData(); // Load lại bảng để thấy kết quả
    } catch (error) {
        const errorMsg = error.response?.data?.error || "Định dạng file không đúng!";
        toast.error(`Lỗi: ${errorMsg}`, { id: importToast });
    } finally {
        setIsImporting(false);
        e.target.value = ''; 
    }
};

    // --- HANDLERS GÁN MÔN HỌC ---
    const handleOpenAssign = async (user) => {
        setSelectedUser(user);
        setIsAssignModalOpen(true);
        setAssignedCourseIds([]); 
        
        const loadingId = toast.loading("Đang tải dữ liệu môn học...");
        try {
            const userCourses = await fetchUserCourses(user.id); 
            const ids = userCourses.map(c => typeof c === 'object' ? (c.id || c.course_id) : c);
            setAssignedCourseIds(ids);
            toast.dismiss(loadingId);
        } catch (error) {
            toast.error("Không thể tải thông tin môn học của user", { id: loadingId });
        }
    };

    const toggleCourseAssignment = (courseId) => {
        setAssignedCourseIds(prev => 
            prev.includes(courseId) 
                ? prev.filter(id => id !== courseId) 
                : [...prev, courseId] 
        );
    };

    const handleSaveAssignments = async () => {
        setIsSavingAssign(true);
        const loadingId = toast.loading("Đang lưu phân công...");
        try {
            await updateUserCourses(selectedUser.id, assignedCourseIds);
            toast.success("Cập nhật phân công thành công!", { id: loadingId });
            setIsAssignModalOpen(false);
        } catch (error) {
            toast.error("Cập nhật thất bại!", { id: loadingId });
        } finally {
            setIsSavingAssign(false);
        }
    };

    // MỚI: Mảng cấu hình các Tabs
    const TABS_CONFIG = [
        { id: 'ALL', label: 'Tất cả', icon: Users },
        { id: 'STUDENT', label: 'Sinh viên', icon: GraduationCap },
        { id: 'TEACHER', label: 'Giảng viên', icon: Briefcase },
        { id: 'ADMIN', label: 'Quản trị viên', icon: Shield }
    ];

    return (
        <div className={`p-4 md:p-8 w-full h-full overflow-y-auto custom-scrollbar ${theme.bg} ${theme.text} transition-colors duration-200`}>
            
            {/* Header Section */}
            <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-extrabold flex items-center gap-3">
                        <Users className={`${accent.text} w-8 h-8`} />
                        Hệ thống Quản trị
                    </h1>
                    <p className={`${theme.subText} mt-1`}>Quản lý nhân sự và phân quyền truy cập hệ thống.</p>
                </div>
                <div className="flex gap-3">
                    <button 
                        onClick={handleOpenAdd}
                        className={`flex items-center gap-2 px-5 py-2.5 ${accent.bg} text-white rounded-xl hover:scale-105 active:scale-95 font-semibold transition-all shadow-md`}
                    >
                        <Plus size={20} /> Thêm User
                    </button>
                </div>
            </div>

            {/* Quick Actions & Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
                <div className={`p-6 rounded-2xl ${theme.modalBg} flex items-center gap-4 shadow-sm`}>
                    <div className={`p-3 rounded-xl ${accent.bg} bg-opacity-10 ${accent.text}`}><Users size={24}/></div>
                    <div>
                        <p className={`text-sm ${theme.subText}`}>Tổng thành viên</p>
                        <p className="text-2xl font-bold">{users.length}</p>
                    </div>
                </div>
                
                {/* Search Bar */}
                <div className={`md:col-span-3 p-4 rounded-2xl ${theme.modalBg} flex items-center gap-3 shadow-sm`}>
                    <Search className={theme.subText} size={20} />
                    <input 
                        type="text"
                        placeholder={activeTab === 'ALL' ? "Tìm kiếm nhanh trong toàn hệ thống..." : `Tìm kiếm trong danh sách ${TABS_CONFIG.find(t => t.id === activeTab)?.label}...`}
                        className={`w-full bg-transparent outline-none ${theme.text} font-medium`}
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>
            </div>

            {/* Import Excel Area */}
            <div className={`p-6 rounded-2xl ${theme.modalBg} shadow-sm mb-8 relative overflow-hidden`}>
                <div className="flex items-center justify-between mb-4">
                    <h2 className="text-lg font-bold flex items-center gap-2">
                        <FileSpreadsheet className="text-emerald-500" size={20} />
                        Nhập dữ liệu hàng loạt (Excel)
                    </h2>
                    {/* Thêm Dropdown chọn loại file */}
                    <select 
                        value={importType} 
                        onChange={e => setImportType(e.target.value)}
                        className={`p-2 px-3 rounded-lg outline-none font-bold cursor-pointer transition-colors border-2 
                        ${importType === 'user' ? 'bg-blue-50 text-blue-600 border-blue-200' : 
                        importType === 'course' ? 'bg-purple-50 text-purple-600 border-purple-200' : 
                        'bg-emerald-50 text-emerald-600 border-emerald-200'}`}
                    >
                        <option value="user">1. Import Tài Khoản (User)</option>
                        <option value="course">2. Import Môn Học (Course)</option>
                        <option value="member">3. Phân Công (Vào lớp)</option>
                    </select>
                </div>
                <div className={`border-2 border-dashed rounded-xl p-8 text-center transition-all relative 
                    ${isImporting ? `${accent.border} bg-opacity-5 ${accent.bg}` : `${theme.border} hover:border-gray-400`}`}>
                    
                    <input 
                        type="file" 
                        accept=".xlsx, .xls, .csv" 
                        onChange={handleFileUpload} 
                        className="absolute inset-0 w-full h-full opacity-0 cursor-pointer disabled:cursor-not-allowed" 
                        disabled={isImporting}
                    />

                    {isImporting ? (
                        <div className="flex flex-col items-center animate-pulse">
                            <Loader2 size={32} className={`${accent.text} mb-3 animate-spin`} />
                            <p className={`${accent.text} font-bold`}>Đang phân tích dữ liệu...</p>
                        </div>
                    ) : (
                        <div className="flex flex-col items-center">
                            <UploadCloud size={36} className={`${theme.subText} mb-2`} />
                            <p className="font-semibold">Kéo thả file Excel hoặc click để chọn</p>
                            <p className={`text-xs ${theme.subText} mt-1 uppercase tracking-widest`}>Hỗ trợ: .xlsx, .xls, .csv</p>
                        </div>
                    )}
                </div>
            </div>

            {/* MỚI: Thanh Tabs Điều hướng */}
            <div className="flex gap-3 mb-4 overflow-x-auto custom-scrollbar pb-2">
                {TABS_CONFIG.map(tab => {
                    const count = tab.id === 'ALL' 
                        ? users.length 
                        : users.filter(u => (u.role || 'STUDENT').toUpperCase() === tab.id).length;

                    return (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-bold transition-all whitespace-nowrap
                                ${activeTab === tab.id 
                                    ? `${accent.bg} text-white shadow-md transform scale-[1.02]` 
                                    : `${theme.modalBg} ${theme.subText} hover:bg-opacity-80`
                                }`}
                        >
                            <tab.icon size={18} />
                            {tab.label}
                            <span className={`ml-1 px-2.5 py-0.5 rounded-full text-[11px] ${
                                activeTab === tab.id ? 'bg-white/20' : 'bg-black/5 dark:bg-white/10'
                            }`}>
                                {count}
                            </span>
                        </button>
                    )
                })}
            </div>

            {/* Table Section */}
            <div className={`rounded-2xl ${theme.modalBg} shadow-sm overflow-hidden`}>
                <div className="overflow-x-auto custom-scrollbar">
                    <table className="w-full text-left border-collapse">
                        <thead className={`${theme.inputBg}`}>
                            <tr>
                                <th className="p-5 font-bold text-xs uppercase tracking-wider opacity-70">Thông tin User</th>
                                <th className="p-5 font-bold text-xs uppercase tracking-wider opacity-70">Email</th>
                                <th className="p-5 font-bold text-xs uppercase tracking-wider opacity-70">Vai trò</th>
                                <th className="p-5 font-bold text-xs uppercase tracking-wider text-center opacity-70">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody className={`divide-y ${theme.border}`}>
                            {isLoading ? (
                                <tr><td colSpan="4" className="p-12 text-center"><Loader2 className="animate-spin mx-auto opacity-20" size={32} /></td></tr>
                            ) : filteredUsers.length === 0 ? (
                                <tr>
                                    <td colSpan="4" className="p-12 text-center opacity-50 font-medium">
                                        Không tìm thấy {activeTab !== 'ALL' ? TABS_CONFIG.find(t=>t.id===activeTab)?.label.toLowerCase() : 'kết quả'} nào phù hợp
                                    </td>
                                </tr>
                            ) : (
                                filteredUsers.map((user) => (
                                    <tr key={user.id} className={`${theme.hover} transition-colors group`}>
                                        <td className="p-5">
                                            <div className="font-bold text-[15px]">{user.name || user.username || <span className="opacity-40 italic">Chưa có tên</span>}</div>
                                            <div className="text-[11px] opacity-40 font-mono mt-0.5">ID: {user.id}</div>
                                        </td>
                                        <td className="p-5 text-sm font-medium opacity-80">{user.email}</td>
                                        <td className="p-5">
                                            <span className={`px-3 py-1.5 rounded-md text-[11px] font-black uppercase tracking-wider ${
                                                user.role?.toUpperCase() === 'TEACHER' ? 'bg-purple-500/10 text-purple-600' 
                                                : user.role?.toUpperCase() === 'ADMIN' ? 'bg-red-500/10 text-red-600'
                                                : 'bg-blue-500/10 text-blue-600'
                                            }`}>
                                                {user.role || 'STUDENT'}
                                            </span>
                                        </td>
                                        <td className="p-5">
                                            <div className="flex items-center justify-center gap-2 opacity-30 group-hover:opacity-100 transition-opacity">
                                                
                                                {/* XÓA ĐIỀU KIỆN STUDENT CHO NÚT PHÂN CÔNG (Bạn yêu cầu chỉ giữ TEACHER) */}
                                                {user.role?.toUpperCase() === 'TEACHER' && (
                                                    <button 
                                                        onClick={() => handleOpenAssign(user)} 
                                                        className="p-2 bg-emerald-50 hover:bg-emerald-100 text-emerald-600 rounded-lg transition-colors"
                                                        title="Phân công dạy"
                                                    >
                                                        <BookOpen size={16} />
                                                    </button>
                                                )}
                                                
                                                <button 
                                                    onClick={() => handleOpenEdit(user)} 
                                                    className="p-2 bg-blue-50 hover:bg-blue-100 text-blue-600 rounded-lg transition-colors"
                                                    title="Chỉnh sửa"
                                                >
                                                    <Edit2 size={16} />
                                                </button>
                                                <button 
                                                    onClick={() => handleDeleteClick(user.id)} 
                                                    className="p-2 bg-red-50 hover:bg-red-100 text-red-600 rounded-lg transition-colors"
                                                    title="Xóa user"
                                                >
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </td>
                                    </tr>
                                ))
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Modal Form Thêm/Sửa User */}
            {isModalOpen && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100] backdrop-blur-sm p-4">
                    <div className={`${theme.modalBg} ${theme.text} w-full max-w-md rounded-3xl shadow-2xl animate-in zoom-in-95 duration-200 overflow-hidden`}>
                        <div className={`flex justify-between items-center p-6 border-b ${theme.border}`}>
                            <h3 className="text-xl font-black">{modalMode === 'add' ? 'THÊM NGƯỜI DÙNG' : 'CẬP NHẬT THÔNG TIN'}</h3>
                            <button onClick={() => setIsModalOpen(false)} className={`p-2 ${theme.hover} rounded-full transition-colors`}><X size={20}/></button>
                        </div>
                        <form onSubmit={handleSubmitUser} className="p-6 space-y-5 bg-black/5">
                            <div>
                                <label className="block text-xs font-bold uppercase mb-2 opacity-60">Họ tên</label>
                                <input required type="text" className={`w-full rounded-xl p-3.5 border-none shadow-inner ${theme.inputBg} outline-none focus:ring-2 ${accent.ring} transition-all`}
                                    value={formData.name} onChange={(e) => setFormData({...formData, name: e.target.value})} placeholder="Nhập tên người dùng..." />
                            </div>
                            <div>
                                <label className="block text-xs font-bold uppercase mb-2 opacity-60">Địa chỉ Email</label>
                                <input required type="email" className={`w-full rounded-xl p-3.5 border-none shadow-inner ${theme.inputBg} outline-none focus:ring-2 ${accent.ring} transition-all`}
                                    value={formData.email} onChange={(e) => setFormData({...formData, email: e.target.value})} placeholder="example@email.com" />
                            </div>
                            <div>
                                <label className="block text-xs font-bold uppercase mb-2 opacity-60">Phân quyền (Role)</label>
                                <select className={`w-full rounded-xl p-3.5 border-none shadow-inner ${theme.inputBg} outline-none focus:ring-2 ${accent.ring} transition-all cursor-pointer`}
                                    value={formData.role} onChange={(e) => setFormData({...formData, role: e.target.value})}>
                                    {/* ĐÃ SỬA: VALUE CỦA OPTION ĐƯỢC CHUYỂN VỀ CHỮ IN HOA ĐỂ TRÁNH LỖI 400 */}
                                    <option value="STUDENT">Sinh viên (Student)</option>
                                    <option value="TEACHER">Giáo viên (Teacher)</option>
                                    <option value="ADMIN">Quản trị viên (Admin)</option>
                                </select>
                            </div>
                            <div className="pt-4 flex gap-3">
                                <button type="button" onClick={() => setIsModalOpen(false)} className={`flex-1 py-3.5 rounded-xl font-bold ${theme.hover} transition-colors`}>Hủy bỏ</button>
                                <button type="submit" className={`flex-1 py-3.5 ${accent.bg} text-white rounded-xl font-bold shadow-md hover:opacity-90 transition-opacity`}>
                                    {modalMode === 'add' ? 'Lưu Dữ Liệu' : 'Cập Nhật'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}

            {/* Modal GÁN MÔN HỌC */}
            {isAssignModalOpen && selectedUser && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-[100] backdrop-blur-sm p-4">
                    <div className={`${theme.modalBg} ${theme.text} w-full max-w-lg rounded-3xl shadow-2xl animate-in zoom-in-95 duration-200 overflow-hidden flex flex-col max-h-[85vh]`}>
                        <div className={`flex justify-between items-center p-6 border-b ${theme.border}`}>
                            <div>
                                <h3 className="text-xl font-black">
                                    PHÂN CÔNG GIẢNG DẠY
                                </h3>
                                <p className={`text-sm mt-1 ${theme.subText}`}>Cho: <span className="font-bold">{selectedUser.name || selectedUser.email}</span></p>
                            </div>
                            <button onClick={() => setIsAssignModalOpen(false)} className={`p-2 ${theme.hover} rounded-full transition-colors`}><X size={20}/></button>
                        </div>
                        
                        <div className={`p-6 overflow-y-auto custom-scrollbar flex-1 bg-black/5 space-y-3`}>
                            {courses.length === 0 ? (
                                <div className="text-center p-8 opacity-50">Chưa có môn học nào trong hệ thống.</div>
                            ) : (
                                courses.map(course => {
                                    const isAssigned = assignedCourseIds.includes(course.id);
                                    return (
                                        <div 
                                            key={course.id} 
                                            onClick={() => toggleCourseAssignment(course.id)}
                                            className={`flex items-center justify-between p-4 rounded-xl cursor-pointer transition-all border-2
                                                ${isAssigned ? `${accent.border} ${accent.bg} bg-opacity-10` : `border-transparent ${theme.inputBg} hover:opacity-80`}`}
                                        >
                                            <div className="flex flex-col">
                                                <span className="font-bold text-[15px]">{course.name}</span>
                                                <span className="text-[12px] opacity-60">Mã môn: {course.code || course.id}</span>
                                            </div>
                                            <div className={`w-6 h-6 rounded-md flex items-center justify-center transition-colors 
                                                ${isAssigned ? `${accent.bg} text-white` : `bg-black/10`}`}>
                                                {isAssigned && <Check size={16} strokeWidth={3} />}
                                            </div>
                                        </div>
                                    )
                                })
                            )}
                        </div>

                        <div className={`p-6 border-t ${theme.border} flex gap-3`}>
                            <button 
                                type="button" 
                                onClick={() => setIsAssignModalOpen(false)} 
                                className={`flex-1 py-3.5 rounded-xl font-bold ${theme.hover} transition-colors`}
                            >
                                Hủy bỏ
                            </button>
                            <button 
                                onClick={handleSaveAssignments} 
                                disabled={isSavingAssign}
                                className={`flex-1 py-3.5 ${accent.bg} text-white rounded-xl font-bold shadow-md hover:opacity-90 transition-opacity flex justify-center items-center gap-2`}
                            >
                                {isSavingAssign && <Loader2 size={18} className="animate-spin" />}
                                Lưu Phân Công
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Admin;