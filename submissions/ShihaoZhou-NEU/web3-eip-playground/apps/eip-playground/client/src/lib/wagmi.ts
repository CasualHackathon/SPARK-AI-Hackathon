import { getDefaultConfig } from '@rainbow-me/rainbowkit';
import { mainnet, optimism, arbitrum, base, sepolia } from 'wagmi/chains';

export const config = getDefaultConfig({
  appName: 'EIP Playground',
  projectId: 'da16948f1ea1e86dd96eb4cfeb85ec49', // Replace with actual project ID
  chains: [mainnet, optimism, arbitrum, base, sepolia],
  ssr: false, // Client-side only for this static template
});
