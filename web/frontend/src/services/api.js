import axios from 'axios';

const api = axios.create({
    baseURL: 'http://127.0.0.1:8000',
    headers: {
        'Content-Type': 'application/json',
    },
});

api.interceptors.request.use(
    (config) => {
        const token = localStorage.getItem('accessToken'); 
        if (token) {
            config.headers['Authorization'] = `Bearer ${token}`;
        }
        return config;
    },
    (error) => Promise.reject(error)
);

api.interceptors.response.use(
    (response) => response,
    async (error) => {
        const originalRequest = error.config;

        if (error.response && error.response.status === 401 && !originalRequest._retry) {
            originalRequest._retry = true;

            try {
                const refreshToken = localStorage.getItem('refreshToken'); 
                
                if (!refreshToken) {
                    window.location.href = '/login';
                    return Promise.reject(error);
                }
                const response = await axios.post('http://127.0.0.1:8000/api/users/auth/token/refresh/', {
                    refresh: refreshToken
                });
                const newAccessToken = response.data.access;
                localStorage.setItem('accessToken', newAccessToken); 

                originalRequest.headers['Authorization'] = `Bearer ${newAccessToken}`;
                return api(originalRequest);

            } catch (refreshError) {
                console.error("Refresh token hết hạn", refreshError);
                localStorage.removeItem('accessToken');
                localStorage.removeItem('refreshToken');
                localStorage.removeItem('user'); 
                window.location.href = '/login';
                return Promise.reject(refreshError);
            }
        }
        return Promise.reject(error);
    }
);

export const fetchUsers = async (role = '') => {
    const url = role ? `/api/users/?role=${role}` : '/api/users/';
    const response = await api.get(url);
    return response.data
};

export const createUser = async (userData) => {
    const response = await api.post('/api/users/', userData);
    return response.data;
};

export const updateUser = async (userId, userData) => {
    const response = await api.put(`/api/users/${userId}/`, userData);
    return response.data;
};

export const deleteUser = async (userId) => {
    const response = await api.delete(`/api/users/${userId}/`);
    return response.data;
};

export const fetchCourses = async () => {
    const response = await api.get('/api/courses/');
    return response.data.data || []; 
};

export const createCourse = async (courseData) => {
    const response = await api.post('/api/courses/', courseData);
    return response.data;
};

export const uploadDocument = async (courseId, file) => {
    const formData = new FormData();
    formData.append('course_id', courseId); 
    formData.append('file', file);

    const response = await api.post('/api/documents/', formData);
    return response.data;
};

export const fetchDocuments = async () => {
    const response = await api.get('/api/documents/');
    return response.data;
};

// ==========================================
// CÁC HÀM API CHO CHAT
// ==========================================
export const fetchChatSessions = async (courseId = '') => {
    const url = courseId ? `/api/chat/sessions/?course_id=${courseId}` : '/api/chat/sessions/';
    const response = await api.get(url);
    return response.data;
};

export const sendMessage = async (chatData) => {
    const response = await api.post('/api/chat/send/', chatData);
    return response.data;
};

export const fetchChatMessages = async (sessionId) => {
    const response = await api.get(`/api/chat/sessions/${sessionId}/`);
    return response.data;
};

export const importUserExcel = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await api.post('/api/users/import-excel/', formData, {
        headers: {
            'Content-Type': 'multipart/form-data'
        }
    });
    return response.data;
};

export const fetchUserCourses = async (userId) => {
    const response = await api.get(`/api/users/${userId}/courses/`);
    return response.data.data || response.data || [];
};

export const updateUserCourses = async (userId, courseIds) => {
    const response = await api.post(`/api/users/${userId}/courses/`, { 
        course_ids: courseIds 
    });
    return response.data;
};

export const importCourseExcel = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/users/import-courses/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export const importMemberCourseExcel = async (file) => {
    const formData = new FormData();
    formData.append('file', file);
    const response = await api.post('/api/users/import-members/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

export default api;