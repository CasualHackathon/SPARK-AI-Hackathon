import { Toaster } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import NotFound from "@/pages/NotFound";
import { Route, Switch } from "wouter";
import ErrorBoundary from "./components/ErrorBoundary";
import { ThemeProvider } from "./contexts/ThemeContext";
import { ScrollProvider } from "./contexts/ScrollContext";
import Home from "./pages/Home";
import EIPDetail from "./pages/EIPDetail";

// Wagmi & RainbowKit Imports
import '@rainbow-me/rainbowkit/styles.css';
import { RainbowKitProvider, darkTheme } from '@rainbow-me/rainbowkit';
import { WagmiProvider } from 'wagmi';
import { QueryClientProvider, QueryClient } from "@tanstack/react-query";
import { config } from "./lib/wagmi";

const queryClient = new QueryClient();

function Router() {
  return (
    <Switch>
      <Route path={"/"} component={Home} />
      <Route path={"/eip/:id"} component={EIPDetail} />
      <Route path={"/404"} component={NotFound} />
      {/* Final fallback route */}
      <Route component={NotFound} />
    </Switch>
  );
}

function App() {
  return (
    <ErrorBoundary>
      <WagmiProvider config={config}>
        <QueryClientProvider client={queryClient}>
          <RainbowKitProvider 
            theme={darkTheme({
              accentColor: '#ffd700', // Gold
              accentColorForeground: 'black',
              borderRadius: 'medium', // Pixel style
              fontStack: 'system',
              overlayBlur: 'small'
            })}
          >
            <ThemeProvider defaultTheme="dark">
              <ScrollProvider>
                <TooltipProvider>
                  <Toaster />
                  <Router />
                </TooltipProvider>
              </ScrollProvider>
            </ThemeProvider>
          </RainbowKitProvider>
        </QueryClientProvider>
      </WagmiProvider>
    </ErrorBoundary>
  );
}

export default App;
