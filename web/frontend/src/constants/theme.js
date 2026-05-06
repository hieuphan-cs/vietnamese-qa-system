import { Sun, Moon, Monitor } from "lucide-react";

export const uiThemes = {
    dark: {
        id: "dark",
        bg: "bg-[#131314]",           
        sidebar: "bg-[#1e1f20]",    
        text: "text-gray-200",       
        subText: "text-gray-400",    
        border: "border-gray-800",   
        inputBg: "bg-[#1e1f20]",      
        hover: "hover:bg-[#282a2c]",  
        msgBotBg: "bg-transparent",   
        modalBg: "bg-[#1e1f20]",
        dropdownBg: "bg-[#2a2b2d]", 
        dropdownBorder: "border-gray-700"
    },
    light: {
        id: "light",
        bg: "bg-[#ffffff]",           
        sidebar: "bg-[#f3f4f6]",      
        text: "text-gray-800",        
        subText: "text-gray-500",    
        border: "border-gray-200",    
        inputBg: "bg-[#f3f4f6]",      
        hover: "hover:bg-[#e5e7eb]",
        msgBotBg: "bg-gray-100",      
        modalBg: "bg-white",
        dropdownBg: "bg-gray-100",
        dropdownBorder: "border-gray-300"
    },
    grey: {
        id: "grey",
        bg: "bg-[#202124]",           
        sidebar: "bg-[#2d2e30]",
        text: "text-gray-100",
        subText: "text-gray-400",
        border: "border-gray-600",
        inputBg: "bg-[#303134]",
        hover: "hover:bg-[#3c4043]",
        msgBotBg: "bg-transparent",
        modalBg: "bg-[#2d2e30]",
        dropdownBg: "bg-[#303134]", 
        dropdownBorder: "border-gray-500"
    }
};

export const accentMap = {
    blue:   { bg: "bg-blue-600",    text: "text-blue-600",    border: "border-blue-500", ring: "focus-within:ring-blue-500/50" },
    green:  { bg: "bg-emerald-600", text: "text-emerald-600", border: "border-emerald-500", ring: "focus-within:ring-emerald-500/50" },
    purple: { bg: "bg-purple-600",  text: "text-purple-600",  border: "border-purple-500", ring: "focus-within:ring-purple-500/50" },
    orange: { bg: "bg-orange-600",  text: "text-orange-600",  border: "border-orange-500", ring: "focus-within:ring-orange-500/50" },
};

export const themeModes = [
    { id: 'light', icon: Sun, label: 'Sáng' },
    { id: 'grey', icon: Monitor, label: 'Xám' },
    { id: 'dark', icon: Moon, label: 'Tối' }
];