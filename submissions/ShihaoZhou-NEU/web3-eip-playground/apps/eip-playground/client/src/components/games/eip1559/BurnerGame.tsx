import React, { useState, useEffect, useRef } from 'react';
import { Flame, Activity, Play, Pause } from 'lucide-react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, ReferenceLine } from 'recharts';
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";
import AITutor, { TutorPose } from '@/components/AITutor';

// Constants
const TARGET_GAS = 15000000; // Target block size
const MAX_GAS = 30000000;    // Max block size
const BASE_FEE_MAX_CHANGE_DENOMINATOR = 8; // 12.5% max change per block

interface ChatMessage {
  id: string;
  role: 'tutor' | 'user';
  content: string;
  timestamp: number;
}

const BurnerGame: React.FC = () => {
  const [baseFee, setBaseFee] = useState<number>(100);
  const [blockHistory, setBlockHistory] = useState<{block: number, baseFee: number, usage: number}[]>([]);
  const [blockNumber, setBlockNumber] = useState<number>(1);
  const [demandLevel, setDemandLevel] = useState<number>(50); // 0-100% of max capacity
  const [isPlaying, setIsPlaying] = useState<boolean>(true);
  
  // User simulation
  const [priorityFee, setPriorityFee] = useState<number>(2);
  const [maxFee, setMaxFee] = useState<number>(150);

  // AI Tutor states
  const [tutorPose, setTutorPose] = useState<TutorPose>('standing');
  const [tutorMessage, setTutorMessage] = useState<string>('');
  const [chatHistory, setChatHistory] = useState<ChatMessage[]>([]);
  const [hasGreeted, setHasGreeted] = useState(false);

  const timerRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const prevBaseFeeRef = useRef<number>(100);
  const prevIncludedRef = useRef<boolean>(true);

  // Tutor speak function
  const tutorSpeak = (message: string, pose: TutorPose = 'teaching') => {
    setTutorMessage(message);
    setTutorPose(pose);
    setChatHistory(prev => [...prev, {
      id: `tutor-${Date.now()}-${Math.random()}`,
      role: 'tutor',
      content: message,
      timestamp: Date.now()
    }]);
  };

  // Initial greeting
  useEffect(() => {
    if (!hasGreeted) {
      setHasGreeted(true);
      tutorSpeak(
        "Hello! I'm Dr. Panda, your EIP-1559 guide. I'll help you understand how the base fee mechanism works. Try adjusting the network congestion slider and watch what happens!",
        'standing'
      );
    }
  }, [hasGreeted]);

  const calculateNextBaseFee = (currentBaseFee: number, gasUsed: number) => {
    // EIP-1559 Formula
    if (gasUsed === TARGET_GAS) {
        return currentBaseFee;
    } else if (gasUsed > TARGET_GAS) {
        const gasUsedDelta = gasUsed - TARGET_GAS;
        const baseFeeDelta = Math.max(1, Math.floor(currentBaseFee * gasUsedDelta / TARGET_GAS / BASE_FEE_MAX_CHANGE_DENOMINATOR));
        return currentBaseFee + baseFeeDelta;
    } else {
        const gasUsedDelta = TARGET_GAS - gasUsed;
        const baseFeeDelta = Math.max(1, Math.floor(currentBaseFee * gasUsedDelta / TARGET_GAS / BASE_FEE_MAX_CHANGE_DENOMINATOR));
        return Math.max(0, currentBaseFee - baseFeeDelta);
    }
  };

  const tick = () => {
    setBlockNumber(prev => prev + 1);

    // Simulate random fluctuation around the user-set demand level
    const randomVariation = (Math.random() - 0.5) * 0.2; // +/- 10%
    const actualUsagePercent = Math.min(1, Math.max(0, (demandLevel / 100) + randomVariation));
    const gasUsed = Math.floor(actualUsagePercent * MAX_GAS);

    setBaseFee(prevBaseFee => {
        const next = calculateNextBaseFee(prevBaseFee, gasUsed);
        
        setBlockHistory(prevHist => {
            const newHist = [...prevHist, { block: blockNumber, baseFee: prevBaseFee, usage: actualUsagePercent * 100 }];
            if (newHist.length > 20) newHist.shift();
            return newHist;
        });

        // Tutor feedback on base fee changes
        if (blockHistory.length > 0) {
          const feeChange = next - prevBaseFee;
          if (Math.abs(feeChange) > 10) {
            if (feeChange > 0) {
              tutorSpeak(
                `Base fee increased from ${prevBaseFee} to ${next} Gwei! This happens when blocks are more than 50% full. The network is getting congested.`,
                'teaching'
              );
            } else {
              tutorSpeak(
                `Base fee decreased from ${prevBaseFee} to ${next} Gwei! This happens when blocks are less than 50% full. The network has spare capacity.`,
                'praising'
              );
            }
          }
        }

        prevBaseFeeRef.current = next;
        return next;
    });
  };

  useEffect(() => {
    if (isPlaying) {
        timerRef.current = setInterval(tick, 2000); // New block every 2 seconds for demo speed
    }
    return () => {
        if (timerRef.current) clearInterval(timerRef.current);
    };
  }, [isPlaying, demandLevel, blockNumber]);

  // Monitor transaction inclusion status
  useEffect(() => {
    const totalCost = baseFee + priorityFee;
    const isIncluded = maxFee >= totalCost;

    if (prevIncludedRef.current && !isIncluded) {
      tutorSpeak(
        `⚠️ Your transaction was rejected! Your max fee (${maxFee} Gwei) is lower than the required cost (${totalCost} Gwei). Try increasing your max fee cap.`,
        'thinking'
      );
    } else if (!prevIncludedRef.current && isIncluded) {
      tutorSpeak(
        `✅ Great! Your transaction is now included. You set a max fee of ${maxFee} Gwei, but you'll only pay ${totalCost} Gwei. The difference is automatically refunded!`,
        'praising'
      );
    }

    prevIncludedRef.current = isIncluded;
  }, [baseFee, priorityFee, maxFee]);

  // Monitor demand level changes
  const prevDemandRef = useRef(demandLevel);
  useEffect(() => {
    const demandChange = demandLevel - prevDemandRef.current;
    if (Math.abs(demandChange) >= 20) {
      if (demandLevel > 50) {
        tutorSpeak(
          `You've increased network congestion to ${demandLevel}%! Watch how the base fee starts climbing. This is EIP-1559's automatic price discovery in action.`,
          'working'
        );
      } else {
        tutorSpeak(
          `You've reduced network congestion to ${demandLevel}%. The base fee will gradually decrease, making transactions cheaper for everyone.`,
          'praising'
        );
      }
      prevDemandRef.current = demandLevel;
    }
  }, [demandLevel]);

  // Derived user status
  const totalCost = baseFee + priorityFee;
  const isIncluded = maxFee >= totalCost;
  const actualPaid = isIncluded ? Math.min(maxFee, baseFee + priorityFee) : 0;
  const burnt = isIncluded ? baseFee : 0;
  const minerTip = isIncluded ? Math.min(maxFee - baseFee, priorityFee) : 0;

  return (
    <div className="bg-card border-4 border-border p-6 shadow-pixel relative overflow-hidden">
      {/* CRT Scanline Effect */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-0 pointer-events-none bg-[length:100%_4px,3px_100%]" />

      <div className="relative z-10">
        <div className="flex items-center justify-between mb-6 border-b-4 border-border pb-4">
          <h2 className="text-xl md:text-2xl font-pixel text-primary flex items-center gap-3 text-shadow-pixel">
            <Flame className="text-orange-500 w-6 h-6 md:w-8 md:h-8" />
            EIP-1559 SIMULATOR
          </h2>
          <div className="flex items-center gap-4">
              <div className={`px-3 py-1 border-2 font-pixel text-xs ${baseFee > 150 ? 'bg-red-500/20 border-red-500 text-red-400' : 'bg-green-500/20 border-green-500 text-green-400'}`}>
                  BASE FEE: {baseFee} GWEI
              </div>
              <Button 
                  variant="outline"
                  size="sm"
                  onClick={() => setIsPlaying(!isPlaying)}
                  className="font-pixel text-xs h-8 border-2"
              >
                  {isPlaying ? <Pause className="w-4 h-4 mr-2" /> : <Play className="w-4 h-4 mr-2" />}
                  {isPlaying ? 'PAUSE' : 'RESUME'}
              </Button>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Control Panel */}
          <div className="lg:col-span-1 space-y-6">
              {/* Network Demand Control */}
              <div className="bg-black/40 p-4 border-2 border-border/50">
                  <h3 className="text-xs font-pixel text-muted-foreground mb-4 flex items-center gap-2 uppercase tracking-wider">
                      <Activity size={14} /> NETWORK CONGESTION
                  </h3>
                  <div className="px-2 mb-2">
                    <Slider
                        defaultValue={[50]}
                        max={100}
                        min={0}
                        step={1}
                        value={[demandLevel]}
                        onValueChange={(vals) => setDemandLevel(vals[0])}
                        className={`py-4 ${demandLevel > 50 ? '[&>.relative>.absolute]:bg-red-500' : '[&>.relative>.absolute]:bg-green-500'}`}
                    />
                  </div>
                  <div className="flex justify-between mt-2 text-[10px] font-mono text-muted-foreground uppercase">
                      <span>IDLE (TARGET 50%↓)</span>
                      <span className={demandLevel > 50 ? 'text-red-400 font-bold' : 'text-green-400 font-bold'}>
                          {demandLevel}% FILL
                      </span>
                      <span>CONGESTED (100%)</span>
                  </div>
                  <p className="text-[10px] text-muted-foreground mt-4 leading-relaxed border-t border-border/30 pt-2">
                      {'>'} 50% Fill: Base Fee INCREASES<br/>
                      {'<'} 50% Fill: Base Fee DECREASES
                  </p>
              </div>

              {/* User Transaction Settings */}
              <div className="bg-black/40 p-4 border-2 border-border/50">
                  <h3 className="text-xs font-pixel text-muted-foreground mb-4 uppercase tracking-wider">YOUR TRANSACTION</h3>
                  
                  <div className="mb-4 space-y-2">
                      <label className="block text-[10px] font-mono text-muted-foreground uppercase">Max Fee Cap (Max Willing to Pay)</label>
                      <div className="flex gap-2 items-center">
                          <input 
                              type="number" 
                              value={maxFee}
                              onChange={(e) => setMaxFee(Number(e.target.value))}
                              className="bg-card border-2 border-border px-2 py-1 text-primary font-mono text-sm w-24 focus:outline-none focus:border-primary"
                          />
                          <span className="text-xs font-pixel text-muted-foreground">GWEI</span>
                      </div>
                  </div>

                  <div className="space-y-2">
                      <label className="block text-[10px] font-mono text-muted-foreground uppercase">Priority Fee (Miner Tip)</label>
                      <div className="flex gap-2 items-center">
                          <input 
                              type="number" 
                              value={priorityFee}
                              onChange={(e) => setPriorityFee(Number(e.target.value))}
                              className="bg-card border-2 border-border px-2 py-1 text-primary font-mono text-sm w-24 focus:outline-none focus:border-primary"
                          />
                          <span className="text-xs font-pixel text-muted-foreground">GWEI</span>
                      </div>
                  </div>
              </div>
          </div>

          {/* Visualizers */}
          <div className="lg:col-span-2 space-y-6">
              
              {/* Chart */}
              <div className="h-48 w-full bg-black/60 border-2 border-border p-2 relative">
                  <div className="absolute top-2 right-2 z-10 flex gap-4 text-[10px] font-mono">
                      <div className="flex items-center gap-1"><div className="w-2 h-2 bg-[#8a63d2]"></div>Base Fee</div>
                      <div className="flex items-center gap-1"><div className="w-2 h-2 bg-red-500 border border-dashed border-white/50"></div>Your Max Fee</div>
                  </div>
                  <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={blockHistory}>
                          <XAxis dataKey="block" hide />
                          <YAxis domain={['auto', 'auto']} width={40} tick={{fontSize: 10, fill: '#666', fontFamily: 'monospace'}} tickLine={false} axisLine={false} />
                          <Tooltip 
                              contentStyle={{backgroundColor: '#000', border: '2px solid #333', fontFamily: 'monospace', fontSize: '12px'}}
                              labelStyle={{color: '#666'}}
                          />
                          <ReferenceLine y={maxFee} stroke="#ef4444" strokeDasharray="3 3" />
                          <Line type="step" dataKey="baseFee" stroke="#8a63d2" strokeWidth={2} dot={false} animationDuration={300} />
                      </LineChart>
                  </ResponsiveContainer>
              </div>

              {/* Transaction Result Block */}
              <div className="bg-black/60 p-6 border-2 border-border">
                  <div className="flex justify-between items-center mb-6">
                      <h3 className="text-xs font-pixel text-muted-foreground uppercase tracking-wider">CURRENT BLOCK STATUS</h3>
                      <div className={`px-3 py-1 border-2 font-pixel text-xs ${isIncluded ? 'bg-green-500/20 border-green-500 text-green-400' : 'bg-red-500/20 border-red-500 text-red-400'}`}>
                          {isIncluded ? '✅ INCLUDED' : '⛔ REJECTED (MAX FEE TOO LOW)'}
                      </div>
                  </div>

                  {isIncluded && (
                      <div className="space-y-6">
                          {/* Cost Breakdown Bar */}
                          <div className="h-12 w-full flex border-2 border-border relative bg-card/30">
                              {/* Burn Part */}
                              <div 
                                  className="bg-orange-500/80 flex items-center justify-center text-[10px] font-pixel text-white transition-all duration-300 border-r-2 border-black/20 relative overflow-hidden group"
                                  style={{ width: `${(burnt / actualPaid) * 100}%` }}
                              >
                                  <div className="absolute inset-0 bg-[url('/images/noise.png')] opacity-20 mix-blend-overlay"></div>
                                  <span className="truncate px-1 relative z-10 flex items-center gap-1">
                                    <Flame size={12} className="animate-pulse" /> BURN: {burnt}
                                  </span>
                              </div>
                              {/* Tip Part */}
                              <div 
                                  className="bg-green-500/80 flex items-center justify-center text-[10px] font-pixel text-white transition-all duration-300 relative overflow-hidden"
                                  style={{ width: `${(minerTip / actualPaid) * 100}%` }}
                              >
                                  <div className="absolute inset-0 bg-[url('/images/noise.png')] opacity-20 mix-blend-overlay"></div>
                                  <span className="truncate px-1 relative z-10">TIP: {minerTip}</span>
                              </div>
                          </div>
                          
                          <div className="grid grid-cols-3 gap-4 text-center font-mono text-sm">
                              <div className="bg-card/50 p-3 border border-border/50">
                                  <div className="text-muted-foreground text-[10px] uppercase mb-1">Actual Paid</div>
                                  <div className="text-primary font-bold">{actualPaid} Gwei</div>
                              </div>
                              <div className="bg-card/50 p-3 border border-border/50">
                                  <div className="text-muted-foreground text-[10px] uppercase mb-1">Saved (Refund)</div>
                                  <div className="text-green-400 font-bold">{(maxFee - actualPaid).toFixed(0)} Gwei</div>
                              </div>
                               <div className="bg-card/50 p-3 border border-border/50">
                                  <div className="text-muted-foreground text-[10px] uppercase mb-1">Burned 🔥</div>
                                  <div className="text-orange-400 font-bold">{burnt} Gwei</div>
                              </div>
                          </div>
                          
                          <p className="text-[10px] text-muted-foreground mt-2 text-center border-t border-border/30 pt-2">
                              EIP-1559 Magic: You only pay Base Fee + Tip. Any extra Max Fee is automatically refunded!
                          </p>
                      </div>
                  )}
              </div>
          </div>
        </div>
      </div>

      {/* AI Tutor */}
      <AITutor
        message={tutorMessage}
        pose={tutorPose}
        chatHistory={chatHistory}
      />
    </div>
  );
};

export default BurnerGame;