import React from "react";
import { BookOpen, FileText, ExternalLink } from "lucide-react";

const SourceDocs = ({ sources, theme }) => {
    if (!sources || sources.length === 0) return null;

    return (
        <div className={`mt-3 pt-3 border-t border-dashed ${theme.border} text-xs`}>
            <div className={`flex items-center gap-1 font-bold mb-2 ${theme.subText} uppercase tracking-wider`}>
                <BookOpen size={14} /> Nguồn tham khảo (RAG):
            </div>
            <div className="flex flex-wrap gap-2">
                {sources.map((src, idx) => (
                    <div 
                        key={idx} 
                        className={`group flex items-center gap-2 px-3 py-2 rounded-lg border transition-all cursor-pointer ${theme.inputBg} ${theme.border} hover:border-blue-500 hover:shadow-sm`}
                        title={`Mở tài liệu: ${src.title}`}
                    >
                        <div className="p-1.5 bg-red-100 dark:bg-red-900/30 rounded text-red-600 dark:text-red-400">
                            <FileText size={14} />
                        </div>
                        <div className="flex flex-col">
                            <span className={`font-medium ${theme.text} line-clamp-1 max-w-[150px]`}>
                                {src.title}
                            </span>
                            <span className={`${theme.subText} text-[10px]`}>
                                Trang {src.page} • Độ tin cậy: {src.score}%
                            </span>
                        </div>
                        <ExternalLink size={12} className={`opacity-0 group-hover:opacity-100 transition-opacity ${theme.subText}`} />
                    </div>
                ))}
            </div>
        </div>
    );
};

export default SourceDocs;