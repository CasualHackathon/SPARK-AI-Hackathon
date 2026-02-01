export default function Footer() {
  return (
    <footer className="relative z-20 w-full bg-black/80 border-t-4 border-border py-8 mt-auto backdrop-blur-md">
      <div className="container flex flex-col md:flex-row items-center justify-between gap-6">
        
        <div className="flex flex-col gap-2">
          <h3 className="font-pixel text-sm text-white/80">Supported ❤️ by</h3>
          <div className="flex items-center gap-6">
            <a href="https://ethpanda.org" target="_blank" rel="noopener noreferrer" className="hover:opacity-80 transition-opacity">
              <img src="/images/ETHPanda-logo.svg" alt="ETHPanda" className="h-8 md:h-10 w-auto" />
            </a>
            <span className="text-white/30 text-2xl">×</span>
            <a href="https://lxdao.io" target="_blank" rel="noopener noreferrer" className="hover:opacity-80 transition-opacity">
              <img src="/images/lxdao-logo.svg" alt="LXDAO" className="h-8 md:h-10 w-auto" />
            </a>
            <span className="text-white/30 text-2xl">×</span>
            <a href="https://spoonai.io/" target="_blank" rel="noopener noreferrer" className="hover:opacity-80 transition-opacity">
              {/* <img src="/images/spoonos_logo.jpg" alt="SpoonOS" className="h-8 md:h-10 w-auto" /> */}
              <p className="font-pixel">SpoonOS</p>
            </a>
          </div>
        </div>

        <div className="flex flex-col items-center md:items-end gap-2 text-xs font-mono text-white/50">
          <p>© 2026 EIP Playground. All rights reserved.</p>
          <div className="flex gap-4">
            <a href="#" className="hover:text-primary transition-colors">Privacy Policy</a>
            <a href="#" className="hover:text-primary transition-colors">Terms of Service</a>
          </div>
        </div>

      </div>
    </footer>
  );
}
