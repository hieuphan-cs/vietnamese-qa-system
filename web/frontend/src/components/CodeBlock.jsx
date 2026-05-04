import React, { useState } from "react";
import { Check, Copy } from "lucide-react";

const CodeBlock = ({ code, language = "javascript" }) => {
    const [copied, setCopied] = useState(false);

    const handleCopy = () => {
        navigator.clipboard.writeText(code);
        setCopied(true);
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="my-3 rounded-lg overflow-hidden border border-gray-700 bg-[#1e1e1e] shadow-md font-mono text-sm">
            <div className="flex justify-between items-center px-4 py-2 bg-[#2d2d2d] border-b border-gray-700 text-gray-400 text-xs select-none">
                <span className="uppercase font-semibold">{language}</span>
                <button 
                    onClick={handleCopy} 
                    className="flex items-center gap-1 hover:text-white transition-colors"
                >
                    {copied ? <Check size={14} className="text-green-400"/> : <Copy size={14} />}
                    <span>{copied ? "Đã chép" : "Sao chép"}</span>
                </button>
            </div>
            <div className="p-4 overflow-x-auto text-gray-300 leading-relaxed whitespace-pre">
                {code}
            </div>
        </div>
    );
};

export default CodeBlock;