import { ConnectButton } from '@rainbow-me/rainbowkit';
import { Link } from 'wouter';

export default function Header() {
  return (
    <header className="sticky top-0 z-50 w-full border-b-4 border-border bg-background/90 backdrop-blur-sm">
      <div className="container flex h-20 items-center justify-between">
        {/* Logo Area */}
        <Link href="/" className="flex items-center gap-3 group">
          <img 
            // src="/images/panda_logo.png" 
            src="/images/eiplay-logo.png" 
            alt="Panda Logo" 
            className="h-12 w-12 object-contain group-hover:animate-pixel-bounce" 
          />
          <div className="flex items-baseline gap-2">
            <span className="font-pixel text-lg text-primary text-shadow-pixel" style={{fontSize: '35px'}}>EIP</span>
            <span className="font-pixel text-xs text-accent text-shadow-pixel ml-2" style={{fontSize: '28px'}}>PLAYGROUND</span>
          </div>
        </Link>

        {/* Nav Links */}
        <nav className="hidden md:flex items-center gap-8">
          {['Home', 'Blog', 'FAQ', 'Team'].map((item) => (
            <Link 
              key={item} 
              href={item === 'Home' ? '/' : `/${item.toLowerCase()}`}
              className="relative font-pixel text-xs text-foreground hover:text-primary transition-colors text-shadow-pixel uppercase group"
            >
              {item}
              <span className="absolute left-0 -bottom-1 w-0 h-[2px] bg-primary transition-all duration-300 group-hover:w-full block" />
            </Link>
          ))}
        </nav>

        {/* Status Bar / Wallet Connect */}
        <div className="flex items-center gap-4">
          <img src="/images/wallet_icon.png" alt="Wallet" className="w-5 h-5 pixelated" />
          <ConnectButton/>
        </div>
      </div>
    </header>
  );
}
