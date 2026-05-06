import React, { useState, useRef, useEffect } from 'react';
import { useOutletContext } from "react-router-dom";
import { UploadCloud, FileText, CheckCircle2, Clock, Trash2, AlertCircle, Loader2, Plus, X, Pencil, PlusCircle } from 'lucide-react';
import toast from 'react-hot-toast'; 
import api, { fetchCourses, fetchDocuments, createCourse } from './services/api';

const Knowledge = () => {
    const { currentUi, currentAccent, user } = useOutletContext();
    const fileInputRef = useRef(null);
    const [documents, setDocuments] = useState([]);
    const [courses, setCourses] = useState([]);
    
    // States cho Upload
    const [isUploadModalOpen, setIsUploadModalOpen] = useState(false);
    const [selectedCourseId, setSelectedCourseId] = useState("");
    const [selectedFile, setSelectedFile] = useState(null);
    const [isUploading, setIsUploading] = useState(false);
    const [isDragging, setIsDragging] = useState(false);
    
    // States cho Thêm Môn Học
    const [showAddCourseModal, setShowAddCourseModal] = useState(false);
    const [newCourseId, setNewCourseId] = useState(""); 
    const [newCourseName, setNewCourseName] = useState(""); 
    const [isAddingCourse, setIsAddingCourse] = useState(false);

    // States cho Edit Document
    const [editModalOpen, setEditModalOpen] = useState(false);
    const [editingDoc, setEditingDoc] = useState(null);
    const [newTitle, setNewTitle] = useState("");

    const loadInitialData = async () => {
        try {
            const [docsData, coursesData] = await Promise.all([
                fetchDocuments(),
                fetchCourses()
            ]);
            setDocuments(docsData);
            setCourses(coursesData);
        } catch (error) {
            console.error("Lỗi khi lấy dữ liệu:", error);
        }
    };

    useEffect(() => {
        loadInitialData();
        const intervalId = setInterval(() => {
            setDocuments(prevDocs => {
                const hasProcessing = prevDocs.some(doc => doc.status === 'PROCESSING' || doc.status === 'PENDING');
                if (hasProcessing) loadInitialData();
                return prevDocs;
            });
        }, 5000);
        return () => clearInterval(intervalId);
    }, []);

    //HÀM KIỂM TRA ĐỊNH DẠNG FILE
    const validateFile = (file) => {
        if (!file) return false;
        const fileExtension = file.name.split('.').pop().toLowerCase();
        const allowedExtensions = ['pdf', 'doc', 'docx', 'txt'];
        
        if (!allowedExtensions.includes(fileExtension)) {
            toast.error(`Sai định dạng! Không hỗ trợ file .${fileExtension}`);
            return false;
        }
        return true;
    };

    const handleDragOver = (e) => { e.preventDefault(); setIsDragging(true); };
    const handleDragLeave = (e) => { e.preventDefault(); setIsDragging(false); };
    
    const handleDrop = (e) => { 
        e.preventDefault(); 
        setIsDragging(false); 
        if(e.dataTransfer.files && e.dataTransfer.files[0]) {
            const file = e.dataTransfer.files[0];
            //Kiểm tra file trước khi nhận
            if (validateFile(file)) {
                setSelectedFile(file);
            }
        }
    };
    
    const handleFileSelect = (e) => { 
        if(e.target.files && e.target.files[0]) {
            const file = e.target.files[0];
            //Kiểm tra file trước khi nhận
            if (validateFile(file)) {
                setSelectedFile(file);
            } else {
                e.target.value = null; // Reset ô chọn file
            }
        }
    };

    // CHỨC NĂNG 1: UPLOAD TÀI LIỆU
    const handleUploadSubmit = async () => {
        if (!selectedCourseId || !selectedFile) {
            toast.error("⚠️ Vui lòng chọn khóa học và file!");
            return;
        }
        setIsUploading(true);
        const loadingToast = toast.loading("⏳ Đang tải lên tài liệu..."); 
        
        const formData = new FormData();
        formData.append('file', selectedFile);
        formData.append('course_id', selectedCourseId);
        formData.append('title', selectedFile.name);

        try {
            await api.post('/api/documents/', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            });
            toast.success("🎉 Tải lên tài liệu thành công!", { id: loadingToast });
            setIsUploadModalOpen(false);
            setSelectedFile(null);
            setSelectedCourseId("");
            loadInitialData();
        } catch (error) {
            console.error(`Lỗi upload:`, error);
            toast.error(error.response?.data?.message || "❌ Lỗi khi tải lên file!", { id: loadingToast });
        } finally {
            setIsUploading(false);
        }
    };

    // CHỨC NĂNG 2: THÊM MÔN HỌC
    const handleAddCourseSubmit = async () => {
        if(!newCourseId.trim() || !newCourseName.trim()) {
            toast.error("⚠️ Vui lòng nhập đầy đủ Mã môn và Tên môn!");
            return;
        }
        setIsAddingCourse(true);
        const loadingToast = toast.loading("⏳ Đang thêm môn học...");
        
        try {
            const response = await api.post('/api/courses/', {
                code: newCourseId.trim(),
                name: newCourseName.trim()
            });
            
            const createdCourseId = response.data?.data?.id;
            
            toast.success("🎉 Thêm môn học thành công!", { id: loadingToast });
            setShowAddCourseModal(false);
            
            if (createdCourseId) {
                setSelectedCourseId(createdCourseId);
            }
            
            setNewCourseId("");
            setNewCourseName("");
            
            await loadInitialData();
        } catch (error) {
            console.error("Lỗi thêm môn học:", error);
            toast.error(error.response?.data?.message || "❌ Không thể thêm môn học. Có thể mã môn đã tồn tại!", { id: loadingToast });
        } finally {
            setIsAddingCourse(false);
        }
    };

    // XOÁ TÀI LIỆU
    const handleDelete = async (id) => {
        if (!window.confirm("Bạn có chắc muốn xóa tài liệu này?")) return;
        
        const loadingToast = toast.loading("⏳ Đang xóa tài liệu...");
        try {
            await api.delete(`/api/documents/${id}/`);
            setDocuments(documents.filter(doc => doc.id !== id));
            toast.success("🗑️ Đã xóa tài liệu thành công!", { id: loadingToast });
        } catch (error) {
            console.error("Lỗi khi xóa:", error);
            toast.error("❌ Không thể xóa tài liệu. Vui lòng thử lại!", { id: loadingToast });
        }
    };

    // MỞ MODAL SỬA TÀI LIỆU
    const openEditModal = (doc) => {
        setEditingDoc(doc);
        setNewTitle(doc.title || doc.file.split('/').pop());
        setEditModalOpen(true);
    };

    // LƯU SỬA TÀI LIỆU
    const handleEditSubmit = async () => {
        if(!newTitle.trim()) {
            toast.error("⚠️ Tên tài liệu không được để trống!");
            return;
        }
        
        const loadingToast = toast.loading("⏳ Đang cập nhật tên...");
        try {
            await api.patch(`/api/documents/${editingDoc.id}/`, { title: newTitle });
            toast.success("✏️ Đổi tên tài liệu thành công!", { id: loadingToast });
            setEditModalOpen(false);
            loadInitialData();
        } catch (error) {
            console.error("Lỗi sửa tài liệu:", error);
            toast.error("❌ Cập nhật thất bại. Vui lòng thử lại!", { id: loadingToast });
        }
    };

    const renderStatusBadge = (status) => {
        const s = status ? String(status).toUpperCase() : 'PENDING';
        switch (s) {
            case 'READY': return <span className="flex items-center gap-1 text-xs font-medium text-green-600 bg-green-500/10 px-2 py-1 rounded-md w-fit"><CheckCircle2 size={14} /> Sẵn sàng</span>;
            case 'PROCESSING': return <span className="flex items-center gap-1 text-xs font-medium text-blue-500 bg-blue-500/10 px-2 py-1 rounded-md w-fit"><Loader2 size={14} className="animate-spin" /> Đang xử lý</span>;
            case 'PENDING': return <span className="flex items-center gap-1 text-xs font-medium text-yellow-600 bg-yellow-500/10 px-2 py-1 rounded-md w-fit"><Clock size={14} /> Chờ xử lý</span>;
            case 'FAILED': return <span className="flex items-center gap-1 text-xs font-medium text-red-500 bg-red-500/10 px-2 py-1 rounded-md w-fit"><AlertCircle size={14} /> Lỗi định dạng</span>;
            default: return <span className="flex items-center gap-1 text-xs font-medium text-gray-500 bg-gray-100 px-2 py-1 rounded-md w-fit">{s}</span>;
        }
    };

    const formatFileSize = (bytes) => {
        if (!bytes) return '-- MB';
        const k = 1024;
        const sizes = ['Bytes', 'KB', 'MB', 'GB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));
        return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
    };

    return (
        <div className={`p-6 lg:p-10 h-full flex flex-col overflow-y-auto ${currentUi.bg}`}>
            <div className="flex justify-between items-center mb-8">
                <div>
                    <h1 className={`text-2xl font-bold ${currentUi.text} mb-2`}>Quản lý Kho dữ liệu</h1>
                    <p className={`${currentUi.subText} text-sm`}>Tải lên tài liệu dạng PDF, Word, Text để AI học.</p>
                </div>
                
                <button 
                    onClick={() => setIsUploadModalOpen(true)}
                    className={`flex items-center gap-2 px-5 py-2.5 rounded-xl font-medium text-white transition-transform hover:scale-105 shadow-md ${currentAccent.bg}`}
                >
                    <Plus size={18} />
                    <span>Tải tài liệu lên</span>
                </button>
            </div>

            <div className={`flex-1 rounded-xl border ${currentUi.border} ${currentUi.dropdownBg} overflow-hidden flex flex-col`}>
                <div className="overflow-x-auto flex-1">
                    <table className="w-full text-left border-collapse">
                        <thead className={`sticky top-0 ${currentUi.dropdownBg} border-b z-10 ${currentUi.border}`}>
                            <tr className={`text-sm ${currentUi.subText}`}>
                                <th className="px-5 py-3 font-medium">Tên file</th>
                                <th className="px-5 py-3 font-medium">Môn học</th>
                                <th className="px-5 py-3 font-medium">Kích thước</th>
                                <th className="px-5 py-3 font-medium">Trạng thái</th>
                                <th className="px-5 py-3 font-medium text-right">Thao tác</th>
                            </tr>
                        </thead>
                        <tbody>
                            {documents.length === 0 ? (
                                <tr>
                                    <td colSpan="5" className="px-5 py-10 text-center text-gray-500">Chưa có tài liệu nào. Bấm nút Tải lên góc phải để bắt đầu!</td>
                                </tr>
                            ) : (
                                documents.map((doc) => {
                                    const fileName = doc.title || (doc.file ? doc.file.split('/').pop() : `Tài liệu #${doc.id}`);
                                    const courseName = courses.find(c => String(c.id) === String(doc.course || doc.course_id))?.name || "Chưa phân loại";

                                    return (
                                        <tr key={doc.id} className={`border-b ${currentUi.border} ${currentUi.hover} transition-colors group`}>
                                            <td className="px-5 py-4">
                                                <div className="flex items-center gap-3">
                                                    <FileText size={20} className={fileName.includes('pdf') ? 'text-red-400' : 'text-blue-400'} />
                                                    <span className={`font-medium ${currentUi.text} truncate max-w-[200px] lg:max-w-xs`} title={fileName}>
                                                        {fileName}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className={`px-5 py-4 text-sm font-medium ${currentUi.text}`}>{courseName}</td>
                                            <td className={`px-5 py-4 text-sm ${currentUi.subText}`}>{formatFileSize(doc.file_size)}</td>
                                            <td className="px-5 py-4">{renderStatusBadge(doc.status)}</td>
                                            <td className="px-5 py-4 text-right">
                                                <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                                    <button onClick={() => openEditModal(doc)} className="p-2 rounded-lg text-blue-500 hover:bg-blue-500/10 transition-colors" title="Đổi tên file">
                                                        <Pencil size={18} />
                                                    </button>
                                                    <button onClick={() => handleDelete(doc.id)} className="p-2 rounded-lg text-gray-500 hover:text-red-500 hover:bg-red-500/10 transition-colors" title="Xoá">
                                                        <Trash2 size={18} />
                                                    </button>
                                                </div>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* MODAL UPLOAD TÀI LIỆU (z-50) */}
            {isUploadModalOpen && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex justify-center items-center">
                    <div className={`w-[500px] rounded-2xl shadow-xl overflow-hidden border ${currentUi.border} ${currentUi.modalBg || currentUi.bg}`}>
                        <div className={`flex justify-between items-center px-6 py-4 border-b ${currentUi.border}`}>
                            <h3 className={`font-semibold text-lg ${currentUi.text}`}>Tải lên tài liệu mới</h3>
                            <button onClick={() => setIsUploadModalOpen(false)} className={`p-1.5 rounded-lg ${currentUi.hover} ${currentUi.subText}`}>
                                <X size={20} />
                            </button>
                        </div>
                        
                        <div className="p-6 space-y-6">
                            {/* KHU VỰC CHỌN VÀ THÊM MÔN HỌC */}
                            <div>
                                <label className={`block text-sm font-medium mb-2 ${currentUi.text}`}>
                                    Chọn môn học (Khóa học) <span className="text-red-500">*</span>
                                </label>
                                
                                <div className="flex items-center gap-2 h-12">
                                    {/* Ô Select chọn môn */}
                                    <div className={`relative flex-1 h-full flex items-center border ${currentUi.border} ${currentUi.dropdownBg} rounded-xl shadow-sm overflow-hidden`}>
                                        <select 
                                            value={selectedCourseId}
                                            onChange={(e) => setSelectedCourseId(e.target.value)}
                                            className={`w-full h-full px-3 bg-transparent ${currentUi.text} focus:outline-none cursor-pointer`}
                                        >
                                            <option value="" disabled className={currentUi.dropdownBg}>-- Bấm để chọn môn học --</option>
                                            {courses.map(course => (
                                                <option key={course.id} value={course.id} className={currentUi.dropdownBg}>
                                                    {course.name} - {course.code || course.id}
                                                </option>
                                            ))}
                                        </select>
                                    </div>

                                    {/* NÚT DẤU CỘNG: Chỉ hiện cho ADMIN */}
                                    {user?.role?.toUpperCase() === 'ADMIN' && (
                                        <button 
                                            type="button"
                                            onClick={() => setShowAddCourseModal(true)}
                                            className={`h-full aspect-square flex items-center justify-center rounded-xl border ${currentUi.border} hover:bg-blue-500/10 text-blue-500 transition-colors shrink-0 shadow-sm`}
                                            title="Thêm môn học mới"
                                        >
                                            <PlusCircle size={22} />
                                        </button>
                                    )}
                                </div>
                            </div>

                            {/* CHỌN FILE */}
                            <div>
                                <label className={`block text-sm font-medium mb-2 ${currentUi.text}`}>Chọn File tài liệu <span className="text-red-500">*</span></label>
                                <div 
                                    onDragOver={handleDragOver} onDragLeave={handleDragLeave} onDrop={handleDrop}
                                    onClick={() => !isUploading && fileInputRef.current?.click()}
                                    className={`relative flex flex-col items-center justify-center p-8 border-2 border-dashed rounded-xl transition-all cursor-pointer
                                        ${isDragging ? `border-blue-500 ${currentAccent.bg} bg-opacity-10` : `${currentUi.border} hover:bg-black/5`}`}
                                >
                                    {/*Thêm accept chuẩn để lọc file ngay từ cửa sổ mở */}
                                    <input 
                                        type="file" 
                                        ref={fileInputRef} 
                                        onChange={handleFileSelect} 
                                        className="hidden" 
                                        accept=".pdf,.doc,.docx,.txt,application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain" 
                                        disabled={isUploading}
                                    />
                                    <UploadCloud size={40} className={`mb-3 ${isDragging ? currentAccent.text : currentUi.subText}`} />
                                    {selectedFile ? (
                                        <div className="text-center">
                                            <p className={`text-sm font-bold ${currentAccent.text}`}>{selectedFile.name}</p>
                                        </div>
                                    ) : (
                                        <div className="text-center">
                                            <p className={`text-sm font-medium ${currentUi.text}`}>Kéo thả file hoặc click để chọn</p>
                                            {/*Thêm dòng text lưu ý cho người dùng */}
                                            <p className={`text-xs mt-2 font-semibold ${currentUi.subText}`}>Chỉ hỗ trợ file PDF, Word (.doc, .docx), TXT</p>
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        <div className={`px-6 py-4 border-t ${currentUi.border} flex justify-end gap-3 bg-black/10`}>
                            <button onClick={() => setIsUploadModalOpen(false)} className={`px-4 py-2 rounded-lg text-sm font-medium ${currentUi.subText}`} disabled={isUploading}>Hủy</button>
                            <button onClick={handleUploadSubmit} disabled={isUploading || !selectedCourseId || !selectedFile} className={`px-6 py-2 rounded-lg text-sm font-medium text-white ${currentAccent.bg} hover:opacity-90 disabled:opacity-50 flex gap-2 items-center`}>
                                {isUploading && <Loader2 size={16} className="animate-spin" />}
                                {isUploading ? "Đang đẩy lên..." : "Tải lên ngay"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {showAddCourseModal && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] flex justify-center items-center">
                    <div className={`w-[400px] rounded-2xl shadow-xl overflow-hidden border ${currentUi.border} ${currentUi.modalBg || currentUi.bg}`}>
                        <div className={`flex justify-between items-center px-6 py-4 border-b ${currentUi.border}`}>
                            <h3 className={`font-semibold ${currentUi.text}`}>Thêm Môn Học Mới</h3>
                            <button onClick={() => setShowAddCourseModal(false)} className={`p-1.5 rounded-lg ${currentUi.hover} ${currentUi.subText}`}>
                                <X size={20} />
                            </button>
                        </div>
                        <div className="p-6 space-y-4">
                            <div>
                                <label className={`block text-sm mb-1 ${currentUi.subText}`}>Mã môn học (ID) *</label>
                                <input type="text" value={newCourseId} onChange={e => setNewCourseId(e.target.value)} placeholder="VD: INT1434" className={`w-full p-2.5 rounded-lg border ${currentUi.border} bg-transparent ${currentUi.text} focus:border-blue-500 outline-none`} />
                            </div>
                            <div>
                                <label className={`block text-sm mb-1 ${currentUi.subText}`}>Tên môn học *</label>
                                <input type="text" value={newCourseName} onChange={e => setNewCourseName(e.target.value)} placeholder="VD: Lập trình Web" className={`w-full p-2.5 rounded-lg border ${currentUi.border} bg-transparent ${currentUi.text} focus:border-blue-500 outline-none`} onKeyDown={(e) => e.key === 'Enter' && handleAddCourseSubmit()} />
                            </div>
                        </div>
                        <div className={`px-6 py-4 border-t ${currentUi.border} flex justify-end gap-3`}>
                            <button onClick={() => setShowAddCourseModal(false)} className={`px-4 py-2 rounded-lg text-sm ${currentUi.subText}`} disabled={isAddingCourse}>Hủy</button>
                            <button onClick={handleAddCourseSubmit} disabled={isAddingCourse} className={`px-5 py-2 rounded-lg text-sm text-white bg-blue-600 hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2`}>
                                {isAddingCourse && <Loader2 size={16} className="animate-spin"/>} Lưu Môn Học
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {editModalOpen && (
                <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[60] flex justify-center items-center">
                    <div className={`w-[400px] rounded-2xl shadow-xl overflow-hidden border ${currentUi.border} ${currentUi.modalBg || currentUi.bg}`}>
                        <div className={`px-6 py-4 border-b ${currentUi.border}`}>
                            <h3 className={`font-semibold ${currentUi.text}`}>Đổi tên tài liệu</h3>
                        </div>
                        <div className="p-6">
                            <input type="text" value={newTitle} onChange={e => setNewTitle(e.target.value)} className={`w-full p-2.5 rounded-lg border ${currentUi.border} bg-transparent ${currentUi.text} outline-none focus:border-blue-500`} autoFocus />
                        </div>
                        <div className={`px-6 py-4 border-t ${currentUi.border} flex justify-end gap-3`}>
                            <button onClick={() => setEditModalOpen(false)} className={`px-4 py-2 rounded-lg text-sm ${currentUi.subText}`}>Hủy</button>
                            <button onClick={handleEditSubmit} className={`px-5 py-2 rounded-lg text-sm text-white ${currentAccent.bg} hover:opacity-90`}>Lưu thay đổi</button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default Knowledge;