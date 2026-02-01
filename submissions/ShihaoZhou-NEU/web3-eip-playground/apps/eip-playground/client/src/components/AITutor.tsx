import { useState, useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { MessageCircle, X } from "lucide-react";

export type TutorPose =
  | "standing"
  | "sitting-relaxed"
  | "working"
  | "thinking"
  | "teaching"
  | "praising";

export type TutorMessage = {
  id: string;
  role: "tutor" | "user";
  content: string;
  timestamp: number;
};

type AITutorProps = {
  pose: TutorPose;
  message?: string;
  onMessageComplete?: () => void;
  chatHistory?: TutorMessage[];
};

const POSE_IMAGES: Record<TutorPose, string> = {
  standing: "/images/tutor/panda-standing.png",
  "sitting-relaxed": "/images/tutor/panda-sitting-relaxed.png",
  working: "/images/tutor/panda-working.png",
  thinking: "/images/tutor/panda-thinking.png",
  teaching: "/images/tutor/panda-teaching.png",
  praising: "/images/tutor/panda-praising.png",
};

export default function AITutor({
  pose,
  message,
  onMessageComplete,
  chatHistory = [],
}: AITutorProps) {
  const [displayedMessage, setDisplayedMessage] = useState("");
  const [isTyping, setIsTyping] = useState(false);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const chatEndRef = useRef<HTMLDivElement>(null);
  const lastMessageRef = useRef<string>("");

  // Word-by-word typewriter effect
  useEffect(() => {
    if (!message) {
      // Don't clear the message - keep it persistent
      setIsTyping(false);
      return;
    }

    // Prevent duplicate messages
    if (message === lastMessageRef.current) {
      return;
    }
    lastMessageRef.current = message;

    setIsTyping(true);
    const words = message.split(" ");
    let currentIndex = 0;

    // Display first word immediately
    if (words.length > 0) {
      setDisplayedMessage(words[0]);
      currentIndex = 1;
    }

    const interval = setInterval(() => {
      if (currentIndex < words.length) {
        setDisplayedMessage(prev => prev + " " + words[currentIndex++]);
      } else {
        setIsTyping(false);
        clearInterval(interval);
        onMessageComplete?.();
      }
    }, 100); // Speed: 100ms per word

    return () => clearInterval(interval);
  }, [message, onMessageComplete]);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    if (isChatOpen) {
      chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatHistory, isChatOpen]);

  return (
    <>
      {/* Fixed Container for Tutor and Dialog */}
      <div className="fixed bottom-4 right-15 z-50 w-64 flex flex-col items-center pointer-events-none">
        {/* Speech Bubble Area */}
        <div className="relative w-full mb-4 h-40 flex items-end justify-center">
          <AnimatePresence>
            {displayedMessage && (
              <motion.div
                initial={{ scale: 0, opacity: 0, y: 20 }}
                animate={{ scale: 1, opacity: 1, y: 0 }}
                exit={{ scale: 0, opacity: 0 }}
                className="relative bg-white text-black p-4 rounded-xl border-4 border-black shadow-[8px_8px_0px_0px_rgba(0,0,0,1)] w-full pointer-events-auto"
              >
                <p className="font-mono text-sm leading-relaxed">
                  {displayedMessage}
                  {isTyping && (
                    <span className="inline-block w-2 h-4 ml-1 bg-black animate-pulse" />
                  )}
                </p>

                {/* Speech Bubble Arrow - Adjusted to point to character center */}
                <div className="absolute -bottom-4 left-1/2 transform -translate-x-1/2">
                  {/* Black Border Triangle */}
                  <div className="w-0 h-0 border-l-[12px] border-l-transparent border-r-[12px] border-r-transparent border-t-[16px] border-t-black" />
                  {/* White Inner Triangle */}
                  <div className="absolute -top-1 left-1/2 transform -translate-x-1/2 w-0 h-0 border-l-[9px] border-l-transparent border-r-[9px] border-r-transparent border-t-[12px] border-t-white" />
                </div>

                {/* Chat History Toggle Button - Positioned at Bottom Right */}
                <button
                  onClick={() => setIsChatOpen(!isChatOpen)}
                  className="absolute -bottom-3 -right-3 bg-primary text-white p-2.5 rounded-full shadow-lg hover:scale-110 active:scale-95 transition-all border-2 border-black pointer-events-auto z-10"
                  aria-label="Toggle chat history"
                >
                  {isChatOpen ? <X size={16} /> : <MessageCircle size={16} />}
                </button>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Tutor Character */}
        <motion.div
          key={pose}
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="w-40 h-40 relative"
        >
          <img
            src={POSE_IMAGES[pose]}
            alt="AI Tutor"
            className="w-full h-full object-contain drop-shadow-xl animate-float"
          />
        </motion.div>
      </div>
      {/* Collapsible Chat History Panel */}
      <AnimatePresence>
        {isChatOpen && (
          <motion.div
            initial={{ x: 400, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: 400, opacity: 0 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="fixed top-20 right-4 bottom-80 w-96 bg-card border-4 border-black rounded-[10px] shadow-2xl z-100 flex flex-col"
          >
            {/* Header */}
            <div className="bg-primary text-white px-4 py-3 font-mono font-bold border-b-4 border-black rounded-t-[6px]">
              Chat History
            </div>

            {/* Messages */}
            <div className="flex-1 overflow-y-auto p-4 space-y-3">
              {chatHistory.length === 0 ? (
                <p className="text-gray-500 text-center font-mono text-sm mt-8">
                  No messages yet. Dr. Panda will guide you through the game!
                </p>
              ) : (
                chatHistory.map(msg => (
                  <div
                    key={msg.id}
                    className={`flex ${
                      msg.role === "tutor" ? "justify-start" : "justify-end"
                    }`}
                  >
                    <div
                      className={`max-w-[80%] p-3 rounded-lg font-mono text-sm text-black ${
                        msg.role === "tutor"
                          ? "bg-gray-100 border-2 border-gray-300"
                          : "bg-primary/10 border-2 border-primary/30"
                      }`}
                    >
                      {msg.content}
                    </div>
                  </div>
                ))
              )}
              <div ref={chatEndRef} />
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </>
  );
}
