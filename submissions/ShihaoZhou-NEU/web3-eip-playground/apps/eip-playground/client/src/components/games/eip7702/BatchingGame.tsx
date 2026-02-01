import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import AITutor, { TutorPose, TutorMessage } from "@/components/AITutor";

export const BatchingGame: React.FC = () => {
  const [mode, setMode] = useState<"intro" | "eoa" | "7702" | "success">(
    "intro"
  );
  const [cards, setCards] = useState<number[]>(
    Array.from({ length: 10 }, (_, i) => i)
  );
  const [revealedCount, setRevealedCount] = useState(0);
  const [timeLeft, setTimeLeft] = useState(10);
  const [isPlaying, setIsPlaying] = useState(false);
  const [showConfirm, setShowConfirm] = useState(false);
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState("");

  // Tutor states
  const [tutorPose, setTutorPose] = useState<TutorPose>("standing");
  const [tutorMessage, setTutorMessage] = useState<string>("");
  const [chatHistory, setChatHistory] = useState<TutorMessage[]>([]);
  const [hasGreeted, setHasGreeted] = useState(false);

  // Card images mapping
  const cardImages = [
    "/images/tarot/card_01.png",
    "/images/tarot/card_02.png",
    "/images/tarot/card_03.png",
    "/images/tarot/card_04.png",
    "/images/tarot/card_05.png",
    "/images/tarot/card_06.png",
    "/images/tarot/card_07.png",
    "/images/tarot/card_08.png",
    "/images/tarot/card_09.png",
    "/images/tarot/card_10.png",
  ];

  useEffect(() => {
    let timer: NodeJS.Timeout;
    if (isPlaying && timeLeft > 0) {
      timer = setInterval(() => {
        setTimeLeft(prev => prev - 1);
      }, 1000);
    } else if (timeLeft === 0 && isPlaying) {
      setIsPlaying(false);
      setMessage("TIME UP! EOA IS TOO SLOW!");
      setTimeout(() => resetGame(), 4000);
    }
    return () => clearInterval(timer);
  }, [isPlaying, timeLeft]);

  const resetGame = () => {
    setCards(Array.from({ length: 10 }, (_, i) => i));
    setRevealedCount(0);
    setTimeLeft(10);
    setIsPlaying(false);
    setShowConfirm(false);
    setProcessing(false);
    setMessage("");
    setMode("intro");
  };

  const startEOA = () => {
    setMode("eoa");
    setIsPlaying(true);
    setMessage("CLICK ALL 10 CARDS!");
  };

  const start7702 = () => {
    setMode("7702");
    setIsPlaying(false); // No timer needed for instant batch
    setRevealedCount(0);
    setMessage("ONE CLICK TO RULE THEM ALL");
  };

  const handleCardClick = (index: number) => {
    if (!isPlaying || timeLeft === 0) return; // Prevent clicking when time is up
    if (mode === "eoa" && !processing && !showConfirm) {
      setShowConfirm(true);
    }
  };

  const confirmTransaction = () => {
    setProcessing(true);
    setTimeout(() => {
      setProcessing(false);
      setShowConfirm(false);
      setRevealedCount(prev => prev + 1);
      if (revealedCount + 1 === 10) {
        setIsPlaying(false);
        setMessage("PHEW! BARELY MADE IT!");
      }
    }, 1000); // 1s delay per tx
  };

  const handleBatchSign = () => {
    setProcessing(true);
    setTimeout(() => {
      setProcessing(false);
      setRevealedCount(10);
      setMode("success");
      setMessage("BATCHED & EXECUTED INSTANTLY!");
    }, 1500);
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-8 bg-gray-900 border-4 border-white font-pixel text-white relative overflow-hidden shadow-[8px_8px_0px_0px_rgba(0,0,0,0.5)]">
      {/* AI Tutor */}
      <AITutor
        pose={tutorPose}
        message={tutorMessage}
        onMessageComplete={() => {}}
        chatHistory={chatHistory}
      />
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-xl text-yellow-400 mb-2 text-shadow-pixel">
            LEVEL 1: CRAZY CLICKING
          </h2>
          <p
            className="text-xs text-gray-400 font-sans"
            style={{ fontFamily: '"Press Start 2P", system-ui, sans-serif' }}
          >
            MISSION: REVEAL 10 CARDS
          </p>
        </div>
        <div className="text-right">
          <div
            className={`text-2xl ${timeLeft < 5 ? "text-red-500 animate-pulse" : "text-green-400"} text-shadow-pixel`}
          >
            {mode === "eoa"
              ? `00:${timeLeft.toString().padStart(2, "0")}`
              : "--:--"}
          </div>
          <div
            className="text-xs text-gray-500 font-sans"
            style={{ fontFamily: '"Press Start 2P", system-ui, sans-serif' }}
          >
            TIME LEFT
          </div>
        </div>
      </div>

      {/* Game Area */}
      <div className="relative min-h-[500px] flex flex-col items-center justify-center bg-black/30 border-2 border-white/10 p-4">
        {mode === "intro" && (
          <div className="text-center space-y-6">
            <p
              className="text-sm leading-relaxed max-w-lg mx-auto text-gray-300 font-sans"
              style={{ fontFamily: '"Press Start 2P", system-ui, sans-serif' }}
            >
              In the old world (EOA), every action requires a separate
              transaction signature and confirmation wait time.
              <br />
              <br />
              Can you reveal all 10 cards in 10 seconds?
            </p>
            <div className="flex gap-4 justify-center">
              <button
                onClick={startEOA}
                className="px-6 py-3 bg-red-600 border-2 border-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all text-xs font-bold"
              >
                TRY EOA MODE (HARD)
              </button>
              <button
                onClick={start7702}
                className="px-6 py-3 bg-blue-600 border-2 border-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all text-xs font-bold"
              >
                TRY 7702 MODE (EASY)
              </button>
            </div>
          </div>
        )}

        {(mode === "eoa" || mode === "7702" || mode === "success") && (
          <div className="grid grid-cols-5 gap-4 mb-8">
            {cards.map((card, index) => (
              <div
                key={index}
                onClick={() =>
                  index === revealedCount && handleCardClick(index)
                }
                className={`w-24 h-36 cursor-pointer relative perspective-1000 ${
                  index === revealedCount && mode === "eoa"
                    ? "animate-bounce"
                    : ""
                }`}
              >
                <motion.div
                  initial={{ rotateY: 0 }}
                  animate={{ rotateY: index < revealedCount ? 180 : 0 }}
                  transition={{
                    duration: 0.6,
                    type: "spring",
                    stiffness: 260,
                    damping: 20,
                  }}
                  className="w-full h-full relative preserve-3d"
                  style={{ transformStyle: "preserve-3d" }}
                >
                  {/* Card Back */}
                  <div
                    className="absolute inset-0 w-full h-full backface-hidden shadow-[4px_4px_0px_0px_rgba(0,0,0,0.3)] rounded-lg overflow-hidden border-2 border-white/20"
                    style={{ backfaceVisibility: "hidden" }}
                  >
                    <img
                      src="/images/tarot/card_back.png"
                      alt="Card Back"
                      className="w-full h-full object-cover pixelated"
                    />
                  </div>

                  {/* Card Front */}
                  <div
                    className="absolute inset-0 w-full h-full backface-hidden shadow-[4px_4px_0px_0px_rgba(0,0,0,0.3)] rounded-lg overflow-hidden border-2 border-yellow-500/50"
                    style={{
                      backfaceVisibility: "hidden",
                      transform: "rotateY(180deg)",
                    }}
                  >
                    <img
                      src={cardImages[index]}
                      alt={`Card ${index + 1}`}
                      className="w-full h-full object-cover pixelated"
                    />
                  </div>
                </motion.div>
              </div>
            ))}
          </div>
        )}

        {/* EOA Confirmation Modal */}
        <AnimatePresence>
          {showConfirm && (
            <motion.div
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.8, opacity: 0 }}
              className="absolute inset-0 bg-black/80 flex items-center justify-center z-50"
            >
              <div className="bg-gray-800 p-6 border-4 border-white max-w-sm w-full text-center shadow-[8px_8px_0px_0px_rgba(0,0,0,1)]">
                <h3 className="text-yellow-400 mb-4 text-shadow-pixel">
                  CONFIRM TRANSACTION
                </h3>
                <p className="text-xs text-gray-400 mb-6 font-pixel">
                  Gas Fee: 0.001 ETH
                </p>
                {processing ? (
                  <div className="flex flex-col items-center gap-2">
                    <div className="w-8 h-8 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                    <span className="text-xs animate-pulse">MINING...</span>
                  </div>
                ) : (
                  <button
                    onClick={confirmTransaction}
                    className="w-full py-3 bg-green-600 border-2 border-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all text-xs font-bold"
                  >
                    CONFIRM
                  </button>
                )}
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* 7702 Controls */}
        {mode === "7702" && (
          <div className="text-center">
            <p className="text-xs text-blue-300 mb-4 font-pixel">
              EIP-7702 ALLOWS BATCHING OPERATIONS!
            </p>
            {processing ? (
              <div className="flex flex-col items-center gap-2">
                <div className="w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full animate-spin" />
                <span className="text-xs animate-pulse">
                  BATCH EXECUTING...
                </span>
              </div>
            ) : (
              <button
                onClick={handleBatchSign}
                className="px-8 py-4 bg-blue-600 border-2 border-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all text-sm flex items-center gap-2 mx-auto font-bold"
              >
                <span>✍️</span> SIGN ONCE FOR ALL
              </button>
            )}
          </div>
        )}

        {/* Success State */}
        {mode === "success" && (
          <motion.div
            initial={{ scale: 0.5, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            className="text-center"
          >
            <h3 className="text-2xl text-green-400 mb-2 text-shadow-pixel">
              MISSION COMPLETE!
            </h3>
            <p className="text-xs text-gray-400 mb-6 font-pixel">
              1 Signature • 0 Wait Time • 100% Efficiency
            </p>
            <button
              onClick={resetGame}
              className="px-6 py-2 border-2 border-white hover:bg-white hover:text-black transition-colors text-xs font-bold"
            >
              PLAY AGAIN
            </button>
          </motion.div>
        )}

        {/* Message Toast */}
        <div className="flex flex-col items-center">
          {message && (
            <div className="mt-4 bg-gray-800 px-4 py-2 border-2 border-white text-xs text-yellow-300 shadow-[4px_4px_0px_0px_rgba(0,0,0,1)]">
              {message}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
