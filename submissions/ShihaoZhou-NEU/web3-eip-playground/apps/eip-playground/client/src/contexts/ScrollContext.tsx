import { createContext, useContext, useState, ReactNode } from 'react';

interface ScrollContextType {
  homeScrollPosition: number;
  setHomeScrollPosition: (position: number) => void;
}

const ScrollContext = createContext<ScrollContextType | undefined>(undefined);

export function ScrollProvider({ children }: { children: ReactNode }) {
  const [homeScrollPosition, setHomeScrollPosition] = useState(0);

  return (
    <ScrollContext.Provider value={{ homeScrollPosition, setHomeScrollPosition }}>
      {children}
    </ScrollContext.Provider>
  );
}

export function useScrollPosition() {
  const context = useContext(ScrollContext);
  if (!context) {
    throw new Error('useScrollPosition must be used within ScrollProvider');
  }
  return context;
}
