import React, { useState, useEffect } from 'react';
import { RefreshCw, ArrowRight, Coins, AlertTriangle } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Slider } from "@/components/ui/slider";

interface Transaction {
  id: string;
  gasPrice: number;
  isUser: boolean;
  status: 'pending' | 'included' | 'dropped';
}

const BLOCK_CAPACITY = 5;

const GasWarGame: React.FC = () => {
  const [mempool, setMempool] = useState<Transaction[]>([]);
  const [userBid, setUserBid] = useState<number>(50);
  const [lastBlock, setLastBlock] = useState<Transaction[] | null>(null);
  const [simulationStatus, setSimulationStatus] = useState<string>('WAITING FOR INPUT...');
  const [analysis, setAnalysis] = useState<{
    userBid: number;
    lowestIncluded: number;
    overpaid: number;
  } | null>(null);

  // Generate random background transactions
  const generateMempool = () => {
    const txs: Transaction[] = Array.from({ length: 8 }).map((_, i) => ({
      id: `tx-${Date.now()}-${i}`,
      gasPrice: Math.floor(Math.random() * 60) + 20, // Random price between 20-80
      isUser: false,
      status: 'pending'
    }));
    setMempool(txs);
    setLastBlock(null);
    setAnalysis(null);
    setSimulationStatus('MEMPOOL UPDATED. PLACE YOUR BID!');
  };

  useEffect(() => {
    generateMempool();
  }, []);

  const runSimulation = () => {
    const userTx: Transaction = {
      id: 'user-tx',
      gasPrice: userBid,
      isUser: true,
      status: 'pending'
    };

    const allTxs = [...mempool, userTx];
    // Sort by Gas Price (Highest First) - First Price Auction
    const sortedTxs = allTxs.sort((a, b) => (b.gasPrice || 0) - (a.gasPrice || 0));
    
    const included = sortedTxs.slice(0, BLOCK_CAPACITY).map(tx => ({ ...tx, status: 'included' as const }));
    
    setLastBlock(included);
    
    // Determine user fate
    const userResult = included.find(tx => tx.isUser);
    
    // Calculate market clearing price (lowest included price)
    const lowestIncludedTx = included[included.length - 1];
    const lowestIncludedPrice = lowestIncludedTx ? (lowestIncludedTx.gasPrice || 0) : 0;

    if (userResult) {
      setSimulationStatus(`SUCCESS! TRANSACTION MINED.`);
      setAnalysis({
        userBid: userBid,
        lowestIncluded: lowestIncludedPrice,
        overpaid: userBid - lowestIncludedPrice
      });
    } else {
      setSimulationStatus('FAILED. BID TOO LOW.');
      setAnalysis(null);
    }
  };

  return (
    <div className="bg-card border-4 border-border p-6 shadow-pixel relative overflow-hidden">
      {/* CRT Scanline Effect */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-0 pointer-events-none bg-[length:100%_4px,3px_100%]" />
      
      <div className="relative z-10">
        <div className="flex items-center justify-between mb-6 border-b-4 border-border pb-4">
          <h2 className="text-xl md:text-2xl font-pixel text-primary flex items-center gap-3 text-shadow-pixel">
            <Coins className="text-yellow-400 w-6 h-6 md:w-8 md:h-8" />
            LEGACY AUCTION
          </h2>
          <span className="hidden md:inline-block px-3 py-1 bg-yellow-500/20 text-yellow-400 text-xs font-pixel border-2 border-yellow-500/50">
            FIRST PRICE AUCTION
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          {/* Left: Mempool & Controls */}
          <div className="space-y-6">
            <div className="bg-black/40 p-4 border-2 border-border/50">
              <h3 className="text-xs font-pixel text-muted-foreground mb-4 uppercase tracking-wider">CURRENT MEMPOOL</h3>
              <div className="space-y-2 font-mono text-sm">
                {mempool.map(tx => (
                  <div key={tx.id} className="flex justify-between items-center p-2 bg-card/50 border border-border/30 hover:bg-card/80 transition-colors">
                    <span className="text-muted-foreground text-xs">OTHER USER</span>
                    <span className="text-primary">{tx.gasPrice} Gwei</span>
                  </div>
                ))}
                <div className="flex justify-between items-center p-2 bg-primary/20 border-2 border-primary animate-pulse">
                  <span className="text-primary font-bold text-xs">YOU (WAITING)</span>
                  <span className="font-bold text-primary">{userBid} Gwei</span>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div>
                <label className="block text-xs font-pixel text-muted-foreground mb-4">
                  YOUR GAS PRICE BID (GWEI)
                </label>
                <div className="px-2">
                  <Slider
                    defaultValue={[50]}
                    max={100}
                    min={10}
                    step={1}
                    value={[userBid]}
                    onValueChange={(vals) => setUserBid(vals[0])}
                    className="py-4"
                  />
                </div>
                <div className="flex justify-between mt-2 font-mono text-xs text-muted-foreground">
                  <span>10 Gwei</span>
                  <span className="text-lg font-bold text-primary">{userBid} Gwei</span>
                  <span>100 Gwei</span>
                </div>
              </div>

              <div className="flex gap-4">
                <Button 
                  onClick={runSimulation}
                  className="flex-1 font-pixel text-xs h-12 border-b-4 border-r-4 border-primary-foreground active:border-b-0 active:border-r-0 active:translate-y-1 active:translate-x-1 transition-all"
                >
                  <ArrowRight className="mr-2 h-4 w-4" />
                  MINE BLOCK
                </Button>
                <Button 
                  variant="secondary"
                  onClick={generateMempool}
                  className="w-12 h-12 p-0 font-pixel border-b-4 border-r-4 border-secondary-foreground/50 active:border-b-0 active:border-r-0 active:translate-y-1 active:translate-x-1 transition-all"
                  title="Reset"
                >
                  <RefreshCw className="h-4 w-4" />
                </Button>
              </div>
              
              <div className={`p-4 border-2 font-pixel text-xs text-center leading-relaxed ${
                simulationStatus.includes('SUCCESS') 
                  ? 'bg-green-500/10 border-green-500 text-green-400' 
                  : simulationStatus.includes('FAILED') 
                    ? 'bg-red-500/10 border-red-500 text-red-400' 
                    : 'bg-card/50 border-border text-muted-foreground'
              }`}>
                {simulationStatus}
              </div>

              {/* Analysis Overlay */}
              {analysis && (
                  <div className="mt-4 p-4 bg-yellow-500/10 border-2 border-yellow-500/50 text-sm space-y-3 animate-in fade-in slide-in-from-top-2">
                      <div className="flex items-start gap-2">
                          <AlertTriangle className="text-yellow-500 shrink-0 w-5 h-5" />
                          <h4 className="font-pixel text-yellow-500 text-xs pt-1">PAIN POINT: BLIND AUCTION</h4>
                      </div>
                      <div className="pl-7 space-y-2 font-mono text-xs">
                          <div className="flex justify-between items-center text-muted-foreground border-b border-border/50 pb-2">
                              <span>YOUR BID:</span>
                              <span className="font-bold text-foreground">{analysis.userBid} Gwei</span>
                          </div>
                          <div className="flex justify-between items-center text-muted-foreground border-b border-border/50 pb-2">
                              <span>LOWEST MINED:</span>
                              <span className="font-bold text-muted-foreground">{analysis.lowestIncluded} Gwei</span>
                          </div>
                          <div className="flex justify-between items-center text-red-400 font-bold pt-1">
                              <span>OVERPAID (WASTED):</span>
                              <span>+{analysis.overpaid} Gwei</span>
                          </div>
                          
                          <p className="text-[10px] leading-relaxed text-muted-foreground mt-2 bg-black/20 p-2 border border-white/5">
                              In Legacy mode, you pay exactly what you bid. Since you couldn't see others' bids, you overpaid by {analysis.overpaid} Gwei just to be safe. No refunds!
                          </p>
                      </div>
                  </div>
              )}
            </div>
          </div>

          {/* Right: Block Visualization */}
          <div className="bg-black/60 p-6 border-2 border-border flex flex-col relative overflow-hidden min-h-[400px]">
            <h3 className="text-xs font-pixel text-muted-foreground mb-6 text-center uppercase tracking-wider">
              BLOCK CAPACITY: {BLOCK_CAPACITY}
            </h3>
            
            <div className="flex-1 flex flex-col-reverse gap-3">
              {lastBlock ? (
                lastBlock.map((tx, idx) => (
                  <div 
                    key={idx} 
                    className={`p-4 border-2 flex justify-between items-center transition-all duration-500 font-mono text-sm ${
                      tx.isUser 
                        ? 'bg-primary text-primary-foreground border-primary-foreground shadow-[0_0_15px_rgba(var(--primary),0.5)] scale-105 z-10' 
                        : 'bg-card border-border text-muted-foreground opacity-80'
                    }`}
                  >
                    <span className="text-xs">{tx.isUser ? 'YOUR TX' : `TX #${idx}`}</span>
                    <span className="font-bold">{tx.gasPrice} Gwei</span>
                  </div>
                ))
              ) : (
                <div className="h-full flex flex-col items-center justify-center text-muted-foreground/50 gap-4">
                  <div className="w-16 h-16 border-4 border-dashed border-muted-foreground/30 animate-spin-slow" />
                  <span className="font-pixel text-xs">WAITING FOR BLOCK...</span>
                </div>
              )}
            </div>
            
            <div className="mt-6 pt-4 border-t-2 border-border/50 text-[10px] text-muted-foreground font-mono">
               <div className="flex items-start gap-2">
                  <AlertTriangle className="text-yellow-500 w-4 h-4 shrink-0" />
                  <p>
                    Legacy First-Price Auction: You pay what you bid. Miners prioritize highest bids. Overpayment is common and necessary for safety.
                  </p>
               </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GasWarGame;
