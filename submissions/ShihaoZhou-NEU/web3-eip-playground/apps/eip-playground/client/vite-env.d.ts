/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_NFT_API_BASE: string;
  readonly VITE_GAMEBADGE_CONTRACT_ADDRESS: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}