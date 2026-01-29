import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';

export const DelegationGame: React.FC = () => {
  const [status, setStatus] = useState<'normal' | 'delegated' | 'success'>('normal');
  const [processing, setProcessing] = useState(false);
  const [message, setMessage] = useState('ACCESS DENIED: MULTI-SIG IDENTITY REQUIRED');

  const resetGame = () => {
    setStatus('normal');
    setProcessing(false);
    setMessage('ACCESS DENIED: MULTI-SIG IDENTITY REQUIRED');
  };

  const handleDelegate = () => {
    setProcessing(true);
    setMessage('SIGNING DELEGATION AUTH...');
    setTimeout(() => {
      setProcessing(false);
      setStatus('delegated');
      setMessage('IDENTITY UPGRADED: MECH SUIT EQUIPPED');
    }, 2000);
  };

  const enterPortal = () => {
    setProcessing(true);
    setMessage('VERIFYING IDENTITY...');
    setTimeout(() => {
      setProcessing(false);
      setStatus('success');
      setMessage('ACCESS GRANTED! MISSION ACCOMPLISHED.');
    }, 1500);
  };

  return (
    <div className="w-full max-w-4xl mx-auto p-8 bg-gray-900 border-4 border-white font-pixel text-white relative overflow-hidden mt-8 shadow-[8px_8px_0px_0px_rgba(0,0,0,0.5)]">
      {/* Header */}
      <div className="flex justify-between items-center mb-8">
        <div>
          <h2 className="text-xl text-yellow-400 mb-2 text-shadow-pixel">LEVEL 3: IDENTITY HIJACK</h2>
          <p className="text-xs text-gray-400 font-sans" style={{fontFamily: '"Press Start 2P", system-ui, sans-serif'}}>MISSION: ENTER THE HIGH-SECURITY PORTAL</p>
        </div>
        <div className="text-right">
          <div className={`text-sm ${status === 'normal' ? 'text-gray-400' : 'text-blue-400'} font-sans font-bold`} style={{fontFamily: '"Press Start 2P", system-ui, sans-serif'}}>
            STATUS: {status === 'normal' ? 'EOA (CIVILIAN)' : 'CONTRACT (MECH)'}
          </div>
        </div>
      </div>

      {/* Game Area */}
      <div className="relative min-h-[300px] flex flex-col items-center justify-center gap-8 bg-black/30 border-2 border-white/10 p-4">
        
        {/* Character & Portal */}
        <div className="flex items-center gap-12">
          {/* Character */}
          <motion.div 
            animate={{ 
              scale: status === 'delegated' ? 1.5 : 1,
              filter: status === 'delegated' ? 'drop-shadow(0 0 10px #3b82f6)' : 'none'
            }}
            className="text-6xl relative"
          >
            {status === 'normal' ? '🧑‍🚀' : '🤖'}
            {status === 'delegated' && (
              <motion.div
                initial={{ opacity: 0, scale: 1.5 }}
                animate={{ opacity: 1, scale: 1 }}
                className="absolute -top-4 -right-4 text-xs bg-blue-600 px-2 py-1 border-2 border-white font-bold shadow-[2px_2px_0px_0px_rgba(0,0,0,1)]"
              >
                7702
              </motion.div>
            )}
          </motion.div>

          {/* Arrow */}
          <div className="text-2xl text-gray-600">➡️</div>

          {/* Portal */}
          <div className={`text-6xl p-4 border-4 transition-colors duration-500 ${
            status === 'success' ? 'border-green-500 bg-green-900/20' : 'border-red-500 bg-red-900/20'
          } shadow-[4px_4px_0px_0px_rgba(0,0,0,0.5)]`}>
            🌀
          </div>
        </div>

        {/* Controls */}
        <div className="flex flex-col items-center gap-4">
          {status === 'normal' && (
            <button 
              onClick={handleDelegate}
              disabled={processing}
              className="px-8 py-4 bg-purple-600 border-2 border-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all text-sm disabled:opacity-50 font-bold"
            >
              {processing ? 'SIGNING...' : 'ACTIVATE 7702 DELEGATION'}
            </button>
          )}

          {status === 'delegated' && (
            <button 
              onClick={enterPortal}
              disabled={processing}
              className="px-8 py-4 bg-blue-600 border-2 border-white shadow-[4px_4px_0px_0px_rgba(0,0,0,1)] hover:translate-y-1 hover:shadow-none transition-all text-sm disabled:opacity-50 font-bold"
            >
              {processing ? 'VERIFYING...' : 'ENTER PORTAL'}
            </button>
          )}

          {status === 'success' && (
            <div className="text-center">
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="mb-4 text-xs text-gray-400 font-sans"
              >
                *Transaction Complete. Reverting to EOA...*
              </motion.div>
              <button 
                onClick={resetGame}
                className="px-6 py-2 border-2 border-white hover:bg-white hover:text-black transition-colors text-xs font-bold"
              >
                RESET SIMULATION
              </button>
            </div>
          )}
        </div>

        {/* Message Toast */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 w-full text-center">
          <span className={`text-xs ${message.includes('DENIED') ? 'text-red-400' : 'text-green-400'} font-sans font-bold bg-black/50 px-2 py-1 rounded`} style={{fontFamily: '"Press Start 2P", system-ui, sans-serif'}}>
            {message}
          </span>
        </div>
      </div>
    </div>
  );
};
