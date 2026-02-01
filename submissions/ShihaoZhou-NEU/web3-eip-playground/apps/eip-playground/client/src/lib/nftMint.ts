// FastAPI NFT Minting Client

// const NFT_API_BASE = "http://127.0.0.1:8009";
const NFT_API_BASE = import.meta.env.VITE_API_URL;

export interface ClaimBadgeRequest {
  userAddress: string;
}

export interface ClaimBadgeSuccessResponse {
  success: true;
  tokenId: number;
  contractAddress: string;
  txHash: string;
}

export interface ClaimBadgeErrorResponse {
  Detail: string;
}

export type ClaimBadgeResponse =
  | ClaimBadgeSuccessResponse
  | ClaimBadgeErrorResponse;

export async function claimERC8004Badge(
  userAddress: string
): Promise<ClaimBadgeSuccessResponse> {
  const response = await fetch(`${NFT_API_BASE}/claim-badge/8004`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ userAddress }),
  });

  const data = await response.json();

  if (!response.ok) {
    // Handle error response
    throw new Error(
      (data as ClaimBadgeErrorResponse).Detail ||
        `Failed to claim badge: ${response.statusText}`
    );
  }

  return data as ClaimBadgeSuccessResponse;
}