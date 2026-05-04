import React, { useState } from "react";

const Quiz = ({ data, theme, accent }) => {
    const [selected, setSelected] = useState(null);
    const [submitted, setSubmitted] = useState(false);
    const isCorrect = selected === data.correctId;

    return (
        <div className={`mt-3 mb-2 border ${theme.border} rounded-xl overflow-hidden shadow-sm`}>
            <div className={`${accent.bg} text-white px-4 py-2 text-sm font-bold flex justify-between items-center`}>
                <span>📝 Bài tập nhanh</span>
                {submitted && (
                    <span className={`px-2 py-0.5 rounded bg-white/20 text-xs`}>
                        {isCorrect ? "Chính xác!" : "Sai rồi"}
                    </span>
                )}
            </div>
            
            <div className={`p-4 ${theme.inputBg}`}>
                <p className={`font-medium mb-3 ${theme.text}`}>{data.question}</p>
                <div className="space-y-2">
                    {data.options.map((opt) => (
                        <button
                            key={opt.id}
                            disabled={submitted}
                            onClick={() => setSelected(opt.id)}
                            className={`w-full text-left px-4 py-3 rounded-lg border transition-all text-sm flex justify-between items-center
                                ${selected === opt.id 
                                    ? `border-${accent.bg.split('-')[1]}-500 ring-1 ring-${accent.bg.split('-')[1]}-500 ${theme.bg}` 
                                    : `${theme.border} hover:bg-black/5 dark:hover:bg-white/5`
                                }
                                ${submitted && opt.id === data.correctId ? "bg-green-500/10 border-green-500 !text-green-600 dark:!text-green-400" : ""}
                                ${submitted && selected === opt.id && !isCorrect ? "bg-red-500/10 border-red-500 !text-red-600 dark:!text-red-400" : ""}
                            `}
                        >
                            <span className={theme.text}>{opt.text}</span>
                            {selected === opt.id && !submitted && <div className={`w-3 h-3 rounded-full ${accent.bg}`}></div>}
                        </button>
                    ))}
                </div>
                
                {!submitted && (
                    <button 
                        onClick={() => setSubmitted(true)}
                        disabled={!selected}
                        className={`mt-4 w-full py-2 rounded-lg font-medium transition-all ${selected ? `${accent.bg} text-white shadow-md hover:opacity-90` : `bg-gray-300 dark:bg-gray-700 text-gray-500 cursor-not-allowed`}`}
                    >
                        Nộp bài
                    </button>
                )}
            </div>
        </div>
    );
};

export default Quiz;