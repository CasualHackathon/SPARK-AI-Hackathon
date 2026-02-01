import Header from "@/components/Header";
import Hero from "@/components/Hero";
import FeatureGrid from "@/components/FeatureGrid";
import Footer from "@/components/Footer";
import { useScrollPosition } from "@/contexts/ScrollContext";
import { useEffect } from "react";

export default function Home() {
  const { homeScrollPosition, setHomeScrollPosition } = useScrollPosition();

  // Restore scroll position when component mounts
  useEffect(() => {
    window.scrollTo(0, homeScrollPosition);
  }, [homeScrollPosition]);

  // Save scroll position when user scrolls
  useEffect(() => {
    const handleScroll = () => {
      setHomeScrollPosition(window.scrollY);
    };

    window.addEventListener("scroll", handleScroll);
    return () => window.removeEventListener("scroll", handleScroll);
  }, [setHomeScrollPosition]);

  return (
    <div className="min-h-screen flex flex-col relative">
      {/* Background Overlay for better text contrast */}
      <div className="fixed inset-0 bg-black/30 pointer-events-none z-0" />
      
      <Header />
      
      <main className="flex-1 flex flex-col relative z-10">
        <Hero />
        <FeatureGrid />
      </main>

      {/* Footer Cityscape */}
      <div className="relative w-full h-48 md:h-64 mt-auto z-0 pointer-events-none">
        <img 
          src="/images/pixel-city-footer.png" 
          alt="City Footer" 
          className="w-full h-full object-cover object-top opacity-80"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-background via-transparent to-transparent" />
      </div>

      {/* Team Footer */}
      <Footer />
    </div>
  );
}
