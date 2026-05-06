import React, { useEffect } from 'react';
import { GoogleLogin } from '@react-oauth/google';
import { useNavigate } from 'react-router-dom'; 
import api from '../services/api'; 

const Login = () => {
  const navigate = useNavigate();
  
  useEffect(() => {
    if (localStorage.getItem('accessToken')) {
      navigate('/');
    }
  }, [navigate]);

  const handleLoginSuccess = async (credentialResponse) => {
    try {
      const authRes = await api.post('/api/users/auth/google/', {
        token: credentialResponse.credential 
      });

      const { access, refresh } = authRes.data;
      localStorage.setItem('accessToken', access);
      localStorage.setItem('refreshToken', refresh);

      const userRes = await api.get('/api/users/auth/me/');
      const userData = userRes.data;
      localStorage.setItem('user', JSON.stringify(userData));
      
      navigate('/'); 
    } catch (error) {
      console.error("Lỗi đăng nhập:", error);
      alert("Đăng nhập thất bại. Vui lòng thử lại!");
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-950 via-blue-950 to-slate-950 p-4">
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-72 h-72 bg-blue-500/10 rounded-full blur-3xl pointer-events-none"></div>

      <div className="max-w-md w-full bg-slate-900/40 backdrop-blur-2xl border border-white/10 rounded-3xl p-10 shadow-[0_8px_32px_0_rgba(0,0,0,0.5)] text-center relative z-10">
        <div className="mb-8 inline-flex items-center justify-center w-20 h-20 rounded-2xl bg-cyan-500/10 text-cyan-400 shadow-[0_0_20px_rgba(34,211,238,0.2)] border border-cyan-500/20">
          <svg className="w-10 h-10" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
          </svg>
        </div>

        <h1 className="text-3xl font-extrabold text-white mb-2 tracking-tight">
          Smart RAG Assistant
        </h1>
        <p className="text-cyan-200/60 mb-10 font-medium text-sm">
          Hệ thống Trợ lý ảo hỗ trợ Giảng dạy
        </p>
        <div className="bg-blue-950/50 rounded-2xl p-6 border border-cyan-500/20 mb-8 shadow-inner">
          <p className="text-cyan-100 text-sm mb-5 font-medium">Đăng nhập bằng tài khoản sinh viên/giảng viên</p>
          
          <div className="flex justify-center">
            <GoogleLogin
              onSuccess={handleLoginSuccess}
              onError={() => alert("Lỗi kết nối với Google!")}
              useOneTap
              theme="filled_black"
              shape="pill"        
            />
          </div>
        </div>

        <p className="text-xs text-slate-500 mt-8 font-medium">
          © 2026 CK Full Stack Team. All rights reserved.
        </p>
      </div>
    </div>
  );
};

export default Login;