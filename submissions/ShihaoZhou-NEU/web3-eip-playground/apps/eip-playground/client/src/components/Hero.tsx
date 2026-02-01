import { Button } from "@/components/ui/button";
import Typewriter from "./Typewriter";

export default function Hero() {
  const typewriterTexts = [
    "What do you wanna learn today?",
    "What can I help you with?",
    "Start with EIP-1559?",
    "Or ... ERC-8004?",
    "Let's GO 🚀🚀🚀 ! ~"
  ];

  return (
    <section className="relative w-full py-12 md:py-24 lg:py-32 overflow-hidden" style={{paddingTop: '80px'}}>
      <div className="container grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
        
        {/* Left: Slogan & CTA */}
        <div className="flex flex-col gap-8 z-10">
          <div className="space-y-4" style={{width: '780px'}}>
            <h1 className="text-4xl md:text-6xl lg:text-7xl leading-tight text-shadow-pixel">
              LEARN <span className="text-primary">ERC</span>&<span className="text-accent">EIP</span>
              <br />
              THE FUN WAY!
            </h1>
            <p className="font-mono text-xl md:text-2xl text-gray-300 max-w-[780px] bg-black/50 p-4 border-l-4 border-primary" style={{fontSize: '22px', width: '780px'}}>
              Your Web3 odyssey starts here!~ level up your skills through play and visual storytelling.
            </p>
          </div>

          {/* <div className="flex flex-wrap gap-4" style={{width: '700px'}}>
            <button className="btn-pixel btn-pixel-danger text-lg group">
              <span className="mr-2 mb-2">🎮</span> Play Games
            </button>
            <button className="btn-pixel btn-pixel-primary text-lg group" style={{borderColor: '#ffffff'}}>
              <span className="mr-2 mb-2">🗺️</span> Read Comics
            </button>
            <button className="btn-pixel btn-pixel-accent text-lg group" style={{borderColor: '#ffffff'}}>
              <span className="mr-2 mb-2">🤖</span> Ask AI Tutor
            </button>
          </div> */}

<div className="flex flex-wrap gap-6 mt-4" style={{width: '700px'}}>
            {/* Play Games Button */}
            <button className="btn-pixel btn-pixel-danger text-lg group relative pl-16 pr-8 h-16 overflow-visible">
              <div className="absolute -left-6 -top-6 w-20 h-20 transition-transform duration-300 group-hover:scale-200 group-hover:-rotate-12 z-20">
                <img 
                  src="/images/icons/pixel-gamepad.png" 
                  alt="Gamepad" 
                  className="w-full h-full object-contain drop-shadow-lg transform -rotate-1"
                />
              </div>
              <span className="relative z-10">Play Games</span>
            </button>

            {/* Read Comics Button */}
            <button className="btn-pixel btn-pixel-primary text-lg group relative pl-16 pr-8 h-16 overflow-visible" style={{borderColor: '#ffffff'}}>
              <div className="absolute -left-6 -top-6 w-20 h-20 transition-transform duration-300 group-hover:scale-200 group-hover:rotate-12 z-20">
                <img 
                  src="/images/icons/pixel-comic-book.png" 
                  alt="Comic Book" 
                  className="w-full h-full object-contain drop-shadow-lg transform rotate-6"
                />
              </div>
              <span className="relative z-10">Read Comics</span>
            </button>

            {/* Ask AI Tutor Button */}
            <button className="btn-pixel btn-pixel-accent text-lg group relative pl-16 pr-8 h-16 overflow-visible" style={{borderColor: '#ffffff'}}>
              <div className="absolute -left-6 -top-6 w-20 h-20 transition-transform duration-300 group-hover:scale-160 group-hover:rotate-10 z-20">
                <img 
                  src="/images/icons/pixel-panda-phd-red.png" 
                  alt="Panda PhD" 
                  className="w-full h-full object-contain drop-shadow-lg transform -rotate-16"
                />
              </div>
              <span className="relative z-10">Ask AI Tutor</span>
            </button>
          </div>





















          
          <div className="flex gap-8 text-xs font-mono text-gray-400" style={{width: '1700px'}}>
            <div className="flex items-center gap-2" style={{fontSize: '20px', width: '450px'}}>
              <span className="text-primary">+</span> Practice with ERC/EIP
            </div>
            <div className="flex items-center gap-2" style={{fontSize: '20px', width: '450px'}}>
              <span className="text-primary">+</span> Learn through stories
            </div>
            <div className="flex items-center gap-2" style={{fontSize: '20px', width: '450px'}}>
              <span className="text-primary">+</span> Ask Dr.Panda anytime
            </div>
          </div>
        </div>

        {/* Right: Mascot Animation */}
        <div className="relative flex justify-center items-center z-10" style={{width: '733px', height: '700px'}}>
          {/* Speech Bubble */}
          <div className="absolute top-0 right-10 bg-white text-black p-4 font-mono text-sm border-4 border-black animate-float z-20 hidden md:block max-w-[230px]" style={{width: '230px'}}>
            <div style={{fontSize: '16px', minHeight: '48px'}}>
              <Typewriter texts={typewriterTexts} />
            </div>
            {/* Speech Bubble Arrow */}
            <div className="absolute bottom-[-10px] left-[-10px] w-0 h-0 border-t-[10px] border-t-transparent border-r-[20px] border-r-black border-b-[10px] border-b-transparent transform rotate-45"></div>
            <div className="absolute bottom-[-6px] left-[-6px] w-0 h-0 border-t-[8px] border-t-transparent border-r-[16px] border-r-white border-b-[8px] border-b-transparent transform rotate-45 z-10"></div>
          </div>

          {/* Mascot with Glow and Hover Bounce */}
          <div className="relative group cursor-pointer">
            {/* Yellow Glow Background */}
            <div className="absolute inset-0 bg-yellow-400/30 blur-[50px] rounded-full scale-75 group-hover:scale-90 transition-transform duration-500"></div>
            
            <img 
              src="/images/hero_right.png" 
              alt="AI Tutor Mascot" 
              className="relative z-10 w-full max-w-[700px] object-contain drop-shadow-[0_0_15px_rgba(0,255,255,0.3)] transition-transform duration-300 group-hover:-translate-y-4 group-hover:scale-105" 
              style={{width: '700px', height: '700px'}}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
