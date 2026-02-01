import React, { useState, useEffect } from "react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import {
  Bot,
  User,
  Star,
  ShieldCheck,
  RefreshCw,
  CheckCircle,
  Lock,
  ArrowRight,
  Terminal,
  Loader2,
} from "lucide-react";
import AITutor, { TutorPose, TutorMessage } from "@/components/AITutor";
import ConsoleDialog from "@/components/ConsoleDialog";
import { Trophy } from "lucide-react";
import { startQuiz, submitAnswer } from "@/lib/quizApi";
import { claimERC8004Badge } from "@/lib/nftMint";
import { useAccount } from "wagmi";
import { useConnectModal } from "@rainbow-me/rainbowkit";

type Stage = "IDENTITY" | "REPUTATION" | "VALIDATION";
type TaskType = "BOX" | "DELIVERY" | "CODING";

interface TaskLog {
  id: number;
  type: TaskType;
  reward: number;
  timestamp: string;
}

export default function AgentAcademyGame() {
  const [stage, setStage] = useState<Stage>("IDENTITY");
  const [agentId, setAgentId] = useState<string | null>(null);
  const [reputation, setReputation] = useState(0);
  const [taskLogs, setTaskLogs] = useState<TaskLog[]>([]);
  const [isTaskAnimating, setIsTaskAnimating] = useState(false);
  const [currentTask, setCurrentTask] = useState<TaskType | null>(null);
  const [validationStep, setValidationStep] = useState<
    "IDLE" | "SUBMITTING" | "STAMPING" | "VERIFIED"
  >("IDLE");
  const [isVerified, setIsVerified] = useState(false);
  const [gameMessage, setGameMessage] = useState<string | null>(null);
  const [isMinting, setIsMinting] = useState(false);

  // Tutor states
  const [tutorPose, setTutorPose] = useState<TutorPose>("standing");
  const [tutorMessage, setTutorMessage] = useState<string>("");
  const [chatHistory, setChatHistory] = useState<TutorMessage[]>([]);
  const [hasGreeted, setHasGreeted] = useState(false);

  // Quiz states
  const [showChallenge, setShowChallenge] = useState(false);
  const [quizDialogOpen, setQuizDialogOpen] = useState(false);
  const [quizSessionId, setQuizSessionId] = useState<string | null>(null);
  const [quizMessages, setQuizMessages] = useState<
    Array<{ role: "tutor" | "user"; text: string }>
  >([]);
  const [quizDone, setQuizDone] = useState(false);
  const [quizPassed, setQuizPassed] = useState<boolean | null>(null);

  // Quiz loading states
  const [isStartingQuiz, setIsStartingQuiz] = useState(false);
  const [isSubmittingAnswer, setIsSubmittingAnswer] = useState(false);

  // Wallet and NFT states
  const { address, isConnected } = useAccount();
  const { openConnectModal } = useConnectModal();
  const [isClaimingNFT, setIsClaimingNFT] = useState(false);
  const [nftMinted, setNftMinted] = useState(false);
  const [nftData, setNftData] = useState<{
    tokenId: number;
    contractAddress: string;
    txHash: string;
  } | null>(null);

  // Helper to show in-game messages
  const showMessage = (msg: string, duration = 3000) => {
    setGameMessage(msg);
    const id = setTimeout(() => setGameMessage(null), duration);
    return () => clearTimeout(id);
  };

  // Helper to make tutor speak
  const tutorSpeak = (message: string, pose: TutorPose = "standing") => {
    setTutorPose(pose);
    setTutorMessage(message);

    // Add to chat history
    const newMessage: TutorMessage = {
      id: Date.now().toString(),
      role: "tutor",
      content: message,
      timestamp: Date.now(),
    };
    setChatHistory(prev => [...prev, newMessage]);
  };

  // Initial greeting - only once on mount
  useEffect(() => {
    if (!hasGreeted) {
      tutorSpeak(
        "Hello! I'm Dr. Panda, your AI tutor. I'll guide you through the ERC-8004 Agent Academy. Let's create your first agent identity!",
        "standing"
      );
      setHasGreeted(true);
    }
  }, [hasGreeted]);

  // Stage 1: Identity
  const mintIdentity = () => {
    setIsMinting(true);
    showMessage("Minting your agent identity...");

    setTimeout(() => {
      const newId = "0x" + Math.random().toString(16).slice(2, 10).toUpperCase();
      setAgentId(newId);
      setIsMinting(false);
      showMessage(`Identity Minted: ${newId}`);

      tutorSpeak(
        `Welcome! I see you've minted a new agent identity: ${newId}. This is your unique on-chain identifier. Let's start building your reputation!`,
        "praising"
      );

      setTimeout(() => setStage("REPUTATION"), 1500);
    }, 2000);
  };

  // Stage 2: Reputation
  const performTask = (
    type: TaskType,
    difficulty: "EASY" | "MEDIUM" | "HARD"
  ) => {
    if (difficulty === "HARD" && !isVerified) {
      showMessage("Access Denied: Hard tasks require Verified status!");
      tutorSpeak(
        "Hold on! Hard tasks require validation first. You need to prove your reliability through the validation process.",
        "teaching"
      );
      return;
    }

    setIsTaskAnimating(true);
    setCurrentTask(type);
    showMessage("Executing task...");

    tutorSpeak(
      "I'm monitoring your task execution. Let's see how you perform!",
      "working"
    );

    // Animation duration
    setTimeout(() => {
      // Random reward system: 80% chance of gaining points, 20% chance of losing points
      const isPositive = Math.random() < 0.8;
      let baseReward = 0;
      
      switch (difficulty) {
        case "EASY":
          baseReward = 10;
          break;
        case "MEDIUM":
          baseReward = 20;
          break;
        case "HARD":
          baseReward = 50;
          break;
      }

      // Calculate final reward (positive or negative)
      const reward = isPositive ? baseReward : -Math.floor(baseReward * 0.5);
      const newRep = Math.max(0, reputation + reward); // Don't go below 0
      setReputation(newRep);

      const newLog: TaskLog = {
        id: Date.now(),
        type,
        reward,
        timestamp: new Date().toLocaleTimeString([], { hour12: false }),
      };
      setTaskLogs(prev => [newLog, ...prev].slice(0, 5)); // Keep last 5

      if (isPositive) {
        showMessage(`Task Complete! +${reward} Rep - Great work!`);
        tutorSpeak(
          `Excellent work! Your task was well-received and you got positive feedback. You earned ${reward} reputation points. Your total is now ${newRep}.`,
          "praising"
        );
      } else {
        showMessage(`Task had issues. ${reward} Rep - Keep trying!`);
        tutorSpeak(
          `Oh no! The task didn't go as planned and received some negative feedback. You lost ${Math.abs(reward)} reputation points. Don't worry, you can recover! Your total is now ${newRep}.`,
          "teaching"
        );
      }

      setIsTaskAnimating(false);
      setCurrentTask(null);

      if (newRep >= 50 && !isVerified && stage === "REPUTATION") {
        // No auto jump, just notify
        setTimeout(() => {
          showMessage("Reputation Maxed! Validation Layer Unlocked.");
          tutorSpeak(
            "Congratulations! You've reached 50 reputation. You're now eligible for validation. Click the button to proceed!",
            "teaching"
          );
        }, 2000);
      }
    }, 3000); // 3s animation
  };

  // Stage 3: Validation
  const startValidation = () => {
    setValidationStep("SUBMITTING");
    showMessage("Submitting proof to registry...");

    tutorSpeak(
      "I'm submitting your reputation proof to the validation registry. This is a critical step!",
      "working"
    );

    setTimeout(() => {
      setValidationStep("STAMPING");
      showMessage("Validator checking proof...");
      tutorSpeak(
        "The validator is reviewing your credentials. This ensures only reliable agents get verified.",
        "thinking"
      );
      setTimeout(() => {
        setValidationStep("VERIFIED");
        showMessage("Proof Verified!");
        tutorSpeak(
          "Fantastic! You're now a verified agent. High-value tasks are now unlocked for you!",
          "praising"
        );
        setTimeout(() => {
          setIsVerified(true);
          setStage("REPUTATION"); // Go back to tasks
          setValidationStep("IDLE");
          showMessage("Agent Verified! Hard tasks unlocked.");
          
          // Show challenge button after verification
          setTimeout(() => {
            setShowChallenge(true);
            tutorSpeak(
              "Excellent work! Now that you're verified, you can take the final challenge to test your knowledge of ERC-8004. Pass it to earn an NFT reward!",
              "teaching"
            );
          }, 500);
        }, 2000);
      }, 3000);
    }, 2000);
  };

  const resetGame = () => {
    setStage("IDENTITY");
    setAgentId(null);
    setReputation(0);
    setTaskLogs([]);
    setValidationStep("IDLE");
    setIsVerified(false);
    setGameMessage(null);
    setChatHistory([]);
    setHasGreeted(false);
    setShowChallenge(false);
    setQuizDone(false);
    setQuizPassed(null);
    setQuizMessages([]);
    tutorSpeak("Let's start fresh! Ready to create a new agent?", "standing");
  };

  // Quiz handlers
  const handleStartChallenge = async () => {
    setIsStartingQuiz(true);
    try {
      const result = await startQuiz();
      setQuizSessionId(result.sessionId);
      setQuizMessages([{ role: "tutor", text: result.assistantMessage }]);
      setQuizDialogOpen(true);
      setQuizDone(false);
      setQuizPassed(null);
    } catch (error) {
      console.error("Failed to start quiz:", error);
      showMessage("Failed to start challenge. Please try again.");
    } finally {
      setIsStartingQuiz(false);
    }
  };

  const handleQuizSubmit = async (answer: string) => {
    if (!quizSessionId) return;

    // Add user message to chat
    setQuizMessages(prev => [...prev, { role: "user", text: answer }]);

    setIsSubmittingAnswer(true);
    try {
      const result = await submitAnswer({
        sessionId: quizSessionId,
        answer,
      });

      // Add tutor response
      setQuizMessages(prev => [
        ...prev,
        { role: "tutor", text: result.assistantMessage },
      ]);

      // Check if quiz is done
      if (result.done) {
        setQuizDone(true);
        setQuizPassed(result.passed);
      }
    } catch (error) {
      console.error("Failed to submit answer:", error);
      setQuizMessages(prev => [
        ...prev,
        {
          role: "tutor",
          text: "Error processing your answer. Please try again.",
        },
      ]);
    } finally {
      setIsSubmittingAnswer(false);
    }
  };

  const handleRetryQuiz = () => {
    setQuizDialogOpen(false);
    setQuizMessages([]);
    setQuizDone(false);
    setQuizPassed(null);
    setTimeout(() => handleStartChallenge(), 500);
  };

  const handleClaimNFT = async () => {
    // Check wallet connection
    if (!isConnected || !address) {
      showMessage("Please connect your wallet first!");
      tutorSpeak(
        "You need to connect your wallet to claim your NFT reward. Click the Connect Wallet button in the header!",
        "teaching"
      );
      if (openConnectModal) {
        openConnectModal();
      }
      return;
    }

    // Start claiming process
    setIsClaimingNFT(true);
    showMessage("Minting your NFT badge...");
    tutorSpeak(
      "Excellent! Let me mint your ERC-8004 achievement badge on the blockchain...",
      "praising"
    );

    try {
      const result = await claimERC8004Badge(address);
      
      // Success! Save NFT data and show success state
      setNftMinted(true);
      setNftData({
        tokenId: result.tokenId,
        contractAddress: result.contractAddress,
        txHash: result.txHash,
      });
      
      showMessage(
        `NFT minted successfully! Token ID: ${result.tokenId}`,
        5000
      );
      tutorSpeak(
        `Congratulations! Your ERC-8004 badge has been minted! Token ID: ${result.tokenId}.`,
        "praising"
      );

      // Log success details
      console.log("NFT Claim Success:", {
        tokenId: result.tokenId,
        contractAddress: result.contractAddress,
        txHash: result.txHash,
      });
    } catch (error) {
      // Handle errors
      const errorMessage =
        error instanceof Error ? error.message : "Unknown error occurred";
      showMessage(`Failed to claim NFT: ${errorMessage}`, 5000);
      tutorSpeak(
        `Oops! Something went wrong while minting your badge: ${errorMessage}. Please try again later.`,
        "thinking"
      );
      console.error("NFT Claim Error:", error);
    } finally {
      setIsClaimingNFT(false);
    }
  };

  return (
    <div>
    <div className="w-full max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-12 gap-8">
      {/* AI Tutor */}
      <AITutor
        pose={tutorPose}
        message={tutorMessage}
        onMessageComplete={() => {}}
        chatHistory={chatHistory}
      />
      {/* Left Column: Game Area (8 cols) */}
      <div className="lg:col-span-8 space-y-8">
        {/* Progress Header */}
        <div className="flex justify-between items-center bg-black/60 p-4 rounded-xl border-2 border-white/20 backdrop-blur-sm">
          <div
            className={`flex items-center gap-2 ${stage === "IDENTITY" ? "text-green-400 animate-pulse" : "text-gray-500"}`}
          >
            <User />{" "}
            <span className="font-pixel text-sm md:text-base">IDENTITY</span>
          </div>
          <ArrowRight className="text-gray-600" />
          <div
            className={`flex items-center gap-2 ${stage === "REPUTATION" ? "text-yellow-400 animate-pulse" : "text-gray-500"}`}
          >
            <Star />{" "}
            <span className="font-pixel text-sm md:text-base">REPUTATION</span>
          </div>
          <ArrowRight className="text-gray-600" />
          <div
            className={`flex items-center gap-2 ${stage === "VALIDATION" ? "text-blue-400 animate-pulse" : isVerified ? "text-green-400" : "text-gray-500"}`}
          >
            <ShieldCheck />{" "}
            <span className="font-pixel text-sm md:text-base">
              {isVerified ? "VERIFIED" : "VALIDATION"}
            </span>
          </div>
        </div>

        {/* Main Game Card */}
        <Card className="p-8 bg-gray-900 border-4 border-primary min-h-[600px] flex flex-col relative overflow-hidden shadow-[0_0_20px_rgba(0,0,0,0.5)]">
          {/* Background Grid Animation */}
          <div className="absolute inset-0 bg-[linear-gradient(to_right,#4f4f4f2e_1px,transparent_1px),linear-gradient(to_bottom,#4f4f4f2e_1px,transparent_1px)] bg-[size:40px_40px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] pointer-events-none" />

          {/* Content Container - Flex Grow to push message to bottom */}
          <div className="flex-1 flex flex-col items-center justify-center relative z-10 w-full">
            {/* Stage 1: Identity */}
            {stage === "IDENTITY" && (
              <div className="text-center space-y-8 animate-in fade-in zoom-in">
                <div className="space-y-2">
                  <h2 className="text-4xl font-pixel text-green-400 drop-shadow-[0_4px_0_rgba(0,0,0,0.5)]">
                    MINT AGENT IDENTITY
                  </h2>
                  <p className="text-gray-400 text-sm font-pixel">
                    Create a verifiable on-chain identity for your AI agent.
                  </p>
                </div>
                <div className="relative group inline-block">
                  {/* Compact background glow */}
                  <div className="absolute inset-1 bg-gradient-to-r from-green-600 to-blue-600 rounded-lg blur opacity-25 group-hover:opacity-75 transition duration-1000 group-hover:duration-200"></div>
                  <Button
                    size="lg"
                    onClick={mintIdentity}
                    disabled={isMinting}
                    className="relative text-xl px-12 py-8 bg-green-600 hover:bg-green-500 border-b-4 border-green-800 active:border-b-0 active:translate-y-1 transition-all font-pixel disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isMinting ? (
                      <>
                        <Loader2 className="mr-3 w-6 h-6 animate-spin" /> MINTING...
                      </>
                    ) : (
                      <>
                        <User className="mr-3 w-6 h-6" /> MINT Identity
                      </>
                    )}
                  </Button>
                </div>
              </div>
            )}

            {/* Stage 2: Reputation */}
            {stage === "REPUTATION" && (
              <div className="w-full max-w-3xl space-y-8 animate-in fade-in slide-in-from-right">
                {!isTaskAnimating ? (
                  <>
                    <div className="text-center space-y-2">
                      <h2 className="text-3xl font-pixel text-yellow-400 drop-shadow-[0_4px_0_rgba(0,0,0,0.5)]">
                        {isVerified ? "AGENT TASKS" : "BUILD REPUTATION"}
                      </h2>
                      <p className="text-xs text-gray-400 font-pixel">
                        {isVerified
                          ? "Agent verified. High-value tasks unlocked."
                          : "Complete tasks to collect your reputation. Goal: 50 Rep."}
                      </p>
                       {/* <p className="text-xs text-gray-400 font-pixel">
                        Note: Each task may yield positive or negative reputation based on performance.
                      </p> */}
                        <p className="text-xs text-red-400 font-mono">
                          Note: 80% chance to gain points, 20% chance to lose
                          points.
                        </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6 ">
                      {/* Task 1: Box */}
                      <Button
                        variant="default"
                        onClick={() => performTask("BOX", "EASY")}
                        className="h-auto py-6 flex flex-col gap-4 bg-gray-800/50 border-5 border-green-500/80 hover:bg-green-900/20 hover:border-green-400 hover:-translate-y-1 transition-all"
                      >
                        <div className="w-44 h-44 bg-green-900/30 rounded-lg flex items-center justify-center border border-green-500/30">
                          <img
                            src="/images/erc8004/task-box.png"
                            alt="Box Task"
                            className="w-40 h-40 object-contain pixelated rounded-lg"
                          />
                        </div>
                        <div className="text-center">
                          <div className="text-green-400 font-bold font-pixel text-lg">
                            LOGISTICS
                          </div>
                          <div className="text-xs text-gray-400 mt-1 font-pixel">
                            Reward: +10 Rep
                          </div>
                        </div>
                      </Button>

                      {/* Task 2: Delivery */}
                      <Button
                        variant="default"
                        onClick={() => performTask("DELIVERY", "MEDIUM")}
                        className="h-auto py-6 flex flex-col gap-4 bg-gray-800/50 border-5 border-green-500/80 hover:bg-green-900/20 hover:border-green-400 hover:-translate-y-1 transition-all"
                      >
                        <div className="w-44 h-44 bg-yellow-900/30 rounded-lg flex items-center justify-center border border-yellow-500/30">
                          <img
                            src="/images/erc8004/task-delivery.png"
                            alt="Delivery Task"
                            className="w-40 h-40 object-contain pixelated rounded-lg"
                          />
                        </div>
                        <div className="text-center">
                          <div className="text-yellow-400 font-bold font-pixel text-lg">
                            DELIVERY
                          </div>
                          <div className="text-xs text-gray-400 mt-1 font-pixel">
                            Reward: +20 Rep
                          </div>
                        </div>
                      </Button>

                      {/* Task 3: Coding (Locked/Unlocked) */}
                      <Button
                        variant="default"
                        disabled={!isVerified} // 建议加上 disabled 属性，增强语义化
                        onClick={() =>
                          isVerified && performTask("CODING", "HARD")
                        }
                        className={`h-auto py-6 flex flex-col gap-4 bg-gray-800/50 border-5 transition-all ${
                          isVerified
                            ? "border-green-500/80 hover:bg-green-900/20 hover:border-green-400 hover:-translate-y-1 cursor-pointer"
                            : "border-red-500/50 hover:bg-red-900/10 opacity-70 cursor-not-allowed"
                        }`}
                      >
                        <div
                          className={`w-44 h-44 rounded-lg flex items-center justify-center border relative ${
                            isVerified
                              ? "bg-red-900/30 border-red-500/30"
                              : "bg-gray-900/80 border-gray-700"
                          }`}
                        >
                          <img
                            src="/images/erc8004/task-coding.png"
                            alt="Coding Task"
                            className={`rounded-lg w-40 h-40 object-contain pixelated ${!isVerified ? "grayscale opacity-40" : ""}`}
                          />

                          {/* 锁图标 - 当未验证时显示在正中间 */}
                          {!isVerified && (
                            <div className="absolute inset-0 flex items-center justify-center">
                              <Lock
                                className="text-red-500 drop-shadow-[0_0_15px_rgba(239,68,68,0.9)] animate-pulse z-10 
             transform scale-[5] origin-center"
                                strokeWidth={2.5}
                              />
                            </div>
                          )}
                        </div>

                        <div className="text-center">
                          <div
                            className={`${isVerified ? "text-red-400" : "text-gray-500"} font-bold font-pixel text-lg`}
                          >
                            CODING
                          </div>
                          <div className="text-xs text-gray-400 mt-1 font-pixel">
                            {isVerified ? "Reward: +50 Rep" : "Need Validation"}
                          </div>
                        </div>
                      </Button>
                    </div>

                    {/* Action Buttons Row */}
                    <div className="flex justify-center gap-4 mt-8">
                      {/* Validation Button - Shows when ready and not verified */}
                      {reputation >= 50 && !isVerified && (
                        <Button
                          onClick={() => setStage("VALIDATION")}
                          className="animate-bounce bg-blue-600 hover:bg-blue-500 text-white font-pixel px-8 py-6 text-lg border-b-4 border-blue-800 active:border-b-0 active:translate-y-1"
                        >
                          <ShieldCheck className="mr-2" /> PROCEED TO VALIDATION
                        </Button>
                      )}

                      {/* Deploy New Agent - Shows when verified */}
                      {isVerified && (
                        <Button
                          onClick={resetGame}
                          variant="outline"
                          className="border-white/20 hover:bg-white/10 text-white font-pixel px-8 py-6 text-lg"
                        >
                          <RefreshCw className="mr-2" /> DEPLOY NEW AGENT
                        </Button>
                      )}
                    </div>
                  </>
                ) : (
                  <div className="flex flex-col items-center justify-center space-y-6 animate-in fade-in zoom-in">
                    <div className="relative w-64 h-64">
                      <div className="absolute inset-0 bg-blue-500/20 rounded-full animate-ping"></div>
                      <img
                        src={
                          currentTask === "BOX"
                            ? "/images/erc8004/task-box.png"
                            : currentTask === "DELIVERY"
                              ? "/images/erc8004/task-delivery.png"
                              : "/images/erc8004/task-coding.png"
                        }
                        alt="Task Animation"
                        className="w-full h-full object-contain pixelated animate-bounce rounded-lg"
                      />
                    </div>
                    <h3 className="text-2xl font-pixel text-white animate-pulse">
                      EXECUTING TASK...
                    </h3>
                  </div>
                )}
              </div>
            )}

            {/* Stage 3: Validation */}
            {stage === "VALIDATION" && (
              <div className="text-center space-y-8 animate-in fade-in zoom-in relative z-10 w-full max-w-2xl">
                {validationStep === "IDLE" && (
                  <>
                    <div className="space-y-4">
                      <h2 className="text-3xl font-pixel text-blue-400 drop-shadow-[0_4px_0_rgba(0,0,0,0.5)]">
                        VALIDATION REQUIRED
                      </h2>
                      <p className="text-gray-400 text-lg font-pixel">
                        Submit your reputation proof to the registry for
                        verification.
                      </p>
                    </div>
                    <div className="flex gap-4 justify-center">
                      <Button
                        size="lg"
                        onClick={startValidation}
                        className="text-xl px-12 py-8 bg-blue-600 hover:bg-blue-500 border-b-4 border-blue-800 active:border-b-0 active:translate-y-1 transition-all font-pixel"
                      >
                        <ShieldCheck className="mr-3 w-6 h-6" /> SUBMIT PROOF
                      </Button>
                    </div>
                  </>
                )}

                {validationStep !== "IDLE" && (
                  <div className="flex flex-col items-center justify-center space-y-6">
                    <div className="relative w-80 h-80 bg-white/5 rounded-xl border-2 border-white/10 p-4 flex items-center justify-center overflow-hidden">
                      {validationStep === "SUBMITTING" && (
                        <img
                          src="/images/erc8004/validation-submit.png"
                          alt="Submitting"
                          className="w-full h-full object-contain pixelated animate-in slide-in-from-left duration-1000 rounded-lg"
                        />
                      )}
                      {validationStep === "STAMPING" && (
                        <img
                          src="/images/erc8004/validation-stamp.png"
                          alt="Stamping"
                          className="w-full h-full object-contain pixelated animate-in zoom-in duration-300 rounded-lg"
                        />
                      )}
                      {validationStep === "VERIFIED" && (
                        <div className="text-center space-y-4 animate-in zoom-in">
                          <CheckCircle className="w-32 h-32 text-green-400 mx-auto" />
                          <h3 className="text-2xl font-pixel text-green-400">
                            VERIFIED!
                          </h3>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>

          {/* In-Game Message Log (Bottom) */}
          <div className="w-full h-12 bg-black/80 border-t-2 border-white/10 flex items-center px-4 font-mono text-sm">
            <Terminal className="w-4 h-4 text-green-500 mr-2" />
            <span className="text-green-500 mr-2">{">"}</span>
            {gameMessage ? (
              <span className="text-green-400 animate-pulse">
                {gameMessage}
              </span>
            ) : (
              <span className="text-gray-600 animate-pulse">_</span>
            )}
          </div>
        </Card>
      </div>

      {/* Right Column: Persistent UI (4 cols) */}
      <div className="lg:col-span-4 space-y-6">
        {/* Identity Scroll */}
        <div className="relative w-full aspect-[3/4] group perspective-1000">
          <div
            className={`relative w-full h-full transition-all duration-1000 transform ${agentId ? "rotate-y-0 opacity-100" : "rotate-y-90 opacity-0"}`}
          >
            <img
              src="/images/erc8004/identity-scroll.png"
              alt="Identity Scroll"
              className="w-full h-full object-contain pixelated drop-shadow-2xl"
            />

            {/* Scroll Content Overlay */}
            <div className="absolute inset-0 flex flex-col items-center justify-center pt-20 px-12 text-center space-y-4">
              <div className="font-pixel text-xs text-blue-900 opacity-70">
                ERC-8004
              </div>
              <div className="font-pixel text-xs text-blue-900 opacity-70">
                IDENTITY
              </div>
              <div className="w-20 h-20 bg-blue-900/20 rounded-full border-2 border-blue-800/50 flex items-center justify-center">
                <Bot className="w-10 h-10 text-blue-900" />
              </div>
              <div className="font-mono text-xs text-blue-900 break-all font-bold">
                {agentId || "PENDING..."}
              </div>
              <div className="w-full h-px bg-blue-900/30 my-2"></div>
              <div className="space-y-1">
                <div className="text-[10px] text-blue-900 uppercase tracking-widest font-pixel">
                  Status
                </div>
                <Badge
                  variant={isVerified ? "default" : "secondary"}
                  className={`${isVerified ? "bg-green-600" : "bg-gray-600"} text-white border-none font-pixel`}
                >
                  {isVerified ? "VERIFIED" : "UNVERIFIED"}
                </Badge>
              </div>
            </div>
          </div>

          {/* Placeholder when no ID */}
          {!agentId && (
            <div className="absolute inset-0 flex items-center justify-center border-4 border-dashed border-white/10 rounded-xl bg-black/20">
              <div className="text-center text-gray-500">
                <User className="w-12 h-12 mx-auto mb-2 opacity-50" />
                <p className="font-pixel text-sm">NO IDENTITY</p>
              </div>
            </div>
          )}
        </div>

        {/* Reputation Registry */}
        <div className="relative w-full aspect-video bg-black rounded-xl overflow-hidden border-4 border-blue-900 shadow-lg">
          <img
            src="/images/erc8004/reputation-registry.png"
            alt="Registry"
            className="absolute inset-0 w-full h-full object-cover pixelated opacity-50"
          />

          <div className="absolute inset-0 p-4 flex flex-col">
            <div className="flex justify-between items-center mb-4 border-b border-blue-500/30 pb-2">
              <h3 className="font-pixel text-blue-400 text-sm">TASK LOG</h3>
              <div className="text-xs text-blue-300 font-mono animate-pulse">
                LIVE FEED
              </div>
            </div>

            <div className="flex-1 overflow-hidden space-y-2">
              {taskLogs.length === 0 ? (
                <div className="h-full flex items-center justify-center text-blue-500/30 font-pixel text-xs">
                  AWAITING DATA...
                </div>
              ) : (
                taskLogs.map(log => (
                  <div
                    key={log.id}
                    className="flex justify-between items-center bg-blue-900/20 p-2 rounded border border-blue-500/20 text-xs animate-in slide-in-from-left"
                  >
                    <div className="flex items-center gap-2">
                      {log.type === "BOX" && (
                        <div className="w-2 h-2 bg-green-500 rounded-full" />
                      )}
                      {log.type === "DELIVERY" && (
                        <div className="w-2 h-2 bg-yellow-500 rounded-full" />
                      )}
                      {log.type === "CODING" && (
                        <div className="w-2 h-2 bg-red-500 rounded-full" />
                      )}
                      <span className="text-blue-200 font-mono">
                        {log.type}
                      </span>
                    </div>
                     <span
                        className={`font-mono ${log.reward > 0 ? "text-green-400" : "text-red-400"}`}
                      >
                        {log.reward > 0 ? "+" : ""}
                        {log.reward}
                      </span>
                  </div>
                ))
              )}
            </div>

            <div className="mt-4 pt-2 border-t border-blue-500/30">
              <div className="flex justify-between text-xs mb-1">
                <span className="text-blue-300 font-pixel">TOTAL REP</span>
                <span className="text-white font-pixel">{reputation} / 50</span>
              </div>
              <Progress
                value={Math.min((reputation / 50) * 100, 100)}
                className="h-2 bg-blue-900/50"
              />
            </div>
          </div>
        </div>
      </div>

      {/* Console Quiz Dialog */}
      <ConsoleDialog
        open={quizDialogOpen}
        onOpenChange={open => {
          setQuizDialogOpen(open);
          // If closing and quiz is done but not passed, allow retry
          if (!open && quizDone && !quizPassed) {
            // Dialog closed, user can click retry button
          }
        }}
        messages={quizMessages}
        onSubmit={handleQuizSubmit}
        isLoading={isSubmittingAnswer}
      />
       </div>
      {/* Bottom Button Container */}
      <div className="w-full mt-auto pt-6 pb-4 flex justify-center gap-4">
        {/* Challenge Button - Shows after verification */}
        {showChallenge && !quizPassed && (
          <Button
            onClick={handleStartChallenge}
            disabled={isStartingQuiz}
            className="animate-pulse bg-gradient-to-r from-purple-600 to-pink-600 hover:from-purple-500 hover:to-pink-500 text-white font-pixel px-8 py-6 text-lg border-b-4 border-purple-800 active:border-b-0 active:translate-y-1"
          >
            {isStartingQuiz ? (
              <>
                <Loader2 className="mr-2 animate-spin" />
                LOADING...
              </>
            ) : (
              <>
                <Terminal className="mr-2" />
                {quizDone && !quizPassed
                  ? "RETRY CHALLENGE"
                  : "START CHALLENGE"}
              </>
            )}
          </Button>
        )}

        {/* Claim NFT Button or Success Box */}
        {quizPassed && !nftMinted && (
          <Button
            onClick={handleClaimNFT}
            disabled={isClaimingNFT}
            className="animate-bounce bg-gradient-to-r from-yellow-500 to-orange-500 hover:from-yellow-400 hover:to-orange-400 text-black font-pixel px-8 py-6 text-lg border-b-4 border-yellow-700 active:border-b-0 active:translate-y-1 disabled:opacity-50 disabled:cursor-not-allowed disabled:animate-none"
          >
            {isClaimingNFT ? (
              <>
                <Loader2 className="mr-2 animate-spin" />
                MINTING...
              </>
            ) : (
              <>
                <Trophy className="mr-2" /> CLAIM NFT REWARD
              </>
            )}
          </Button>
        )}

        {/* NFT Minting Success Box */}
        {nftMinted && nftData && (
          <div className="w-full max-w-2xl bg-gradient-to-br from-green-500/20 to-emerald-600/20 border-4 border-green-500 rounded-lg p-6 animate-in zoom-in duration-500">
            <div className="flex items-center gap-3 mb-4">
              <CheckCircle className="w-8 h-8 text-green-500 animate-pulse" />
              <h3 className="text-2xl font-pixel text-green-400">
                🎉 CLAIMED SUCCESSFULLY!
              </h3>
            </div>
            
            <div className="space-y-3 font-mono text-sm">
              <div className="bg-black/40 p-4 rounded border border-green-500/30">
                <p className="text-gray-400 mb-1">Transaction Hash:</p>
                <a
                  href={`https://sepolia.etherscan.io/tx/0x${nftData.txHash}`}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-green-400 hover:text-green-300 underline break-all transition-colors"
                >
                  0x{nftData.txHash}
                </a>
                <p className="text-gray-500 text-xs mt-2">
                  Click to view your transaction on Sepolia Etherscan
                </p>
              </div>
              
              <div className="bg-black/40 p-4 rounded border border-green-500/30">
                <p className="text-gray-400 mb-1">NFT Token ID:</p>
                <p className="text-green-400 text-xl font-bold">
                  #{nftData.tokenId}
                </p>
              </div>
              
              <div className="bg-black/40 p-4 rounded border border-green-500/30">
                <p className="text-gray-400 mb-1">Contract Address:</p>
                <p className="text-green-400 break-all">
                  {nftData.contractAddress}
                </p>
              </div>
            </div>
            
            <div className="mt-4 text-center">
              <p className="text-green-300 font-pixel">
                ✨ Your ERC-8004 Achievement Badge is now in your wallet! ✨
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}