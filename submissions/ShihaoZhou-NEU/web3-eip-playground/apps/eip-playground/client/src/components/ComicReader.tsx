import React, { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, BookOpen, Loader2, Maximize2, X } from 'lucide-react';
import { Button } from "@/components/ui/button";

interface ComicReaderProps {
  eipId: string;
  pageCount: number;
  title?: string;
}

const ComicReader: React.FC<ComicReaderProps> = ({ eipId, pageCount, title = "LEARN WITH COMICS" }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [loadedImages, setLoadedImages] = useState<Set<number>>(new Set([1]));
  const [isLoading, setIsLoading] = useState(false);
  const [isFullscreen, setIsFullscreen] = useState(false);

  // Optimize preloading logic to preload all images at the start
  useEffect(() => {
    const preloadAllImages = () => {
      for (let i = 1; i <= pageCount; i++) {
        if (!loadedImages.has(i)) {
          const img = new Image();
          img.src = `/comics/${eipId}/${i}.jpg`;
          img.onload = () => {
            setLoadedImages(prev => new Set(prev).add(i));
          };
        }
      }
    };

    preloadAllImages();
  }, [eipId, pageCount, loadedImages]);

  // Handle page change loading state
  useEffect(() => {
    if (!loadedImages.has(currentPage)) {
      setIsLoading(true);
      const img = new Image();
      img.src = `/comics/${eipId}/${currentPage}.jpg`;
      img.onload = () => {
        setLoadedImages(prev => new Set(prev).add(currentPage));
        setIsLoading(false);
      };
    } else {
      setIsLoading(false);
    }
  }, [currentPage, eipId, loadedImages]);

  // Handle ESC key to exit fullscreen
  useEffect(() => {
    const handleEsc = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setIsFullscreen(false);
    };
    window.addEventListener('keydown', handleEsc);
    return () => window.removeEventListener('keydown', handleEsc);
  }, []);

  const nextPage = () => {
    if (currentPage < pageCount) setCurrentPage(prev => prev + 1);
  };

  const prevPage = () => {
    if (currentPage > 1) setCurrentPage(prev => prev - 1);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowRight') nextPage();
    if (e.key === 'ArrowLeft') prevPage();
  };

  const toggleFullscreen = () => {
    setIsFullscreen(!isFullscreen);
  };

  const ReaderContent = ({ isFullscreenMode = false }) => (
    <div 
      className={`relative flex flex-col items-center justify-center bg-black/90 w-full ${isFullscreenMode ? 'h-screen' : ''}`}
      onKeyDown={handleKeyDown}
      tabIndex={0}
    >
      {/* Comic Image Container */}
      <div className={`relative w-full flex items-center justify-center p-4 md:p-8 overflow-hidden ${isFullscreenMode ? 'h-full' : 'aspect-video'}`}>
        {isLoading ? (
          <div className="flex flex-col items-center gap-4 text-primary animate-pulse">
            <Loader2 className="w-12 h-12 animate-spin" />
            <span className="font-pixel text-sm">LOADING...</span>
          </div>
        ) : (
          <img 
            src={`/comics/${eipId}/${currentPage}.jpg`} 
            alt={`Page ${currentPage}`} 
            className={`object-contain border-4 border-white shadow-[0_0_20px_rgba(255,255,255,0.2)] ${
              loadedImages.has(currentPage) ? '' : 'animate-in fade-in duration-300'
            } ${isFullscreenMode ? 'max-h-[90vh] max-w-[90vw]' : 'w-full h-full'}`}
          />
        )}
        
        {/* Navigation Overlays */}
        <button 
          onClick={(e) => { e.stopPropagation(); prevPage(); }}
          disabled={currentPage === 1}
          className="absolute left-4 top-1/2 -translate-y-1/2 p-2 bg-white/50 hover:bg-primary text-black rounded-full disabled:opacity-0 transition-all hidden md:block z-20"
        >
          <ChevronLeft size={32} />
        </button>
        
        <button 
          onClick={(e) => { e.stopPropagation(); nextPage(); }}
          disabled={currentPage === pageCount}
          className="absolute right-4 top-1/2 -translate-y-1/2 p-2  bg-white/50 hover:bg-primary text-black rounded-full disabled:opacity-0 transition-all hidden md:block z-20"
        >
          <ChevronRight size={32} />
        </button>

        {/* Close Fullscreen Button */}
        {isFullscreenMode && (
          <button
            onClick={toggleFullscreen}
            className="absolute top-4 right-4 p-2 bg-black/50 hover:bg-red-500 text-white rounded-full transition-all z-30"
          >
            <X size={24} />
          </button>
        )}
      </div>

      {/* Controls Bar (Only show in non-fullscreen or at bottom of fullscreen) */}
      <div className={`w-full bg-card border-t-4 border-border p-4 flex items-center justify-between ${isFullscreenMode ? 'absolute bottom-0 left-0 z-20 opacity-0 hover:opacity-100 transition-opacity' : ''}`}>
        <div className="flex items-center gap-4">
          <span className="font-pixel text-xs md:text-sm text-primary">
            PAGE {currentPage} / {pageCount}
          </span>
          {/* Mobile Nav Buttons */}
          <div className="flex gap-2 md:hidden">
            <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); prevPage(); }} disabled={currentPage === 1}>
              <ChevronLeft size={16} />
            </Button>
            <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); nextPage(); }} disabled={currentPage === pageCount}>
              <ChevronRight size={16} />
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className="hidden md:flex gap-1">
            {Array.from({ length: pageCount }).map((_, i) => (
              <div 
                key={i}
                onClick={(e) => { e.stopPropagation(); setCurrentPage(i + 1); }}
                className={`w-3 h-3 cursor-pointer transition-all ${
                  currentPage === i + 1 ? 'bg-primary scale-125' : 
                  loadedImages.has(i + 1) ? 'bg-primary/20 hover:bg-primary' : 'bg-muted/30'
                }`}
                title={loadedImages.has(i + 1) ? `Page ${i + 1} ` : `Page ${i + 1}`}
              />
            ))}
          </div>
        </div>
      </div>
    </div>
  );

  return (
    <>
      <div className="w-full">
        <div className="bg-card border-4 border-border shadow-pixel overflow-hidden rounded-xl">
          {/* Header */}
          <div className="bg-primary/10 border-b-4 border-border p-4 flex justify-between items-center">
            <h3 className="font-pixel text-lg md:text-xl text-primary flex items-center gap-2">
              <BookOpen className="w-6 h-6" />
              {title}
            </h3>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={toggleFullscreen}
              className="font-pixel text-xs hover:bg-primary hover:text-primary-foreground"
            >
              <Maximize2 className="w-4 h-4 mr-2" />
              FULLSCREEN
            </Button>
          </div>

          {/* Reader Body */}
          <ReaderContent />
        </div>
      </div>

      {/* Fullscreen Overlay */}
      {isFullscreen && (
        <div className="fixed inset-0 z-50 bg-black flex items-center justify-center">
          <ReaderContent isFullscreenMode={true} />
        </div>
      )}
    </>
  );
};

export default ComicReader;
