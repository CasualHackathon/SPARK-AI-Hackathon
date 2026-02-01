export interface EIPData {
  id: string;
  title: string;
  subtitle: string;
  description: string;
  content: string;
  image: string;
  gradient: string;
  icon: string;
  comic?: {
    pageCount: number;
    title?: string;
  };
}

export const eips: Record<string, EIPData> = {
  "eip-1559": {
    id: "eip-1559",
    title: "EIP-1559",
    subtitle: "Gas Fee Market",
    description: "A transaction pricing mechanism that includes fixed-per-block network fee that is burned and dynamically expands/contracts block sizes.",
    content: `
# EIP-1559: Fee Market Change for ETH 1.0 Chain

## Abstract
A transaction pricing mechanism that includes fixed-per-block network fee that is burned and dynamically expands/contracts block sizes to deal with transient congestion.

## Motivation
Ethereum historically used a simple auction mechanism to price transaction fees. This worked well enough but had several inefficiencies:
1. **Volatility**: Transaction fees could spike unpredictably.
2. **User Experience**: Users had to guess the right gas price to get included.
3. **Efficiency**: Miners could manipulate fee markets.

## How it Works
EIP-1559 introduced a "Base Fee" that is burned (destroyed) for every transaction. This base fee adjusts automatically based on network demand. Users can also add a "Priority Fee" (tip) to incentivize miners.

## Impact
Since its activation in the London Hard Fork (August 2021), EIP-1559 has burned millions of ETH, making ETH deflationary during periods of high activity.
    `,
    image: "/images/eip-1559-gas.png",
    gradient: "bg-gradient-to-br from-red-900 to-yellow-700",
    icon: "🔥",
    comic: {
      pageCount: 12,
      title: "THE GAS WARS: A VISUAL GUIDE"
    }
  },
  "eip-7702": {
    id: "eip-7702",
    title: "EIP-7702",
    subtitle: "Account Abstraction",
    description: "Adds a new transaction type that sets the code for an EOA for one transaction, enabling batching and sponsorship.",
    content: `
# EIP-7702: Set EOA Account Code for One Transaction

## Abstract
This proposal adds a new transaction type that sets the code for an Externally Owned Account (EOA) for the duration of one transaction.

## Motivation
Account Abstraction (ERC-4337) is great but requires users to migrate to smart contract wallets. EIP-7702 allows existing EOAs (like your MetaMask wallet) to temporarily act as smart contracts.

## Key Features
- **Batching**: Execute multiple operations in one transaction.
- **Sponsorship**: Allow dApps to pay gas fees for users.
- **Security**: Users retain full control of their keys; the code assignment is ephemeral.

## Status
This EIP is currently a strong candidate for the next major Ethereum upgrade (Pectra).
    `,
    image: "/images/eip-7702-robot.png",
    gradient: "bg-gradient-to-br from-orange-800 to-amber-600",
    icon: "🤖",
    comic: {
      pageCount: 13,
      title: "SET CODE: THE TEMPORARY SUPERPOWER"
    }
  },
  "erc-8004": {
    id: "erc-8004",
    title: "ERC-8004",
    subtitle: "Trustless Agents",
    description: "A standard for discovering, choosing, and interacting with AI agents across organizational boundaries using on-chain registries.",
    content: `
# Abstract
ERC-8004 proposes a standard for "Trustless Agents" by introducing three lightweight on-chain registries: Identity, Reputation, and Validation. This allows AI agents to be discoverable and verifiable on Ethereum.

# Motivation
As AI agents become more autonomous, we need a way to trust them without relying on centralized platforms. How do you know an agent will do what it says? How do you know its history?

# The Three Pillars
1.  **Identity Registry**: Verifies "Who is this agent?" using NFTs.
2.  **Reputation Registry**: Tracks "How reliable is this agent?" based on past performance.
3.  **Validation Registry**: Confirms "Did the agent do the job correctly?" using cryptographic proofs.

# Use Cases
- **DeFi Agents**: Autonomous traders that can be audited.
- **Data Oracles**: AI that fetches real-world data with reputation stakes.
- **Service Marketplaces**: A decentralized Upwork for AI bots.
    `,
    image: "/images/erc-8004-agent.png",
    gradient: "bg-gradient-to-br from-green-600 to-emerald-900",
    icon: "🕵️",
    comic: {
      pageCount: 14,
      title: "THE TRUSTLESS AGENT"
    }
  }
};
