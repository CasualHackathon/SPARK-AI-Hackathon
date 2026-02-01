// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test, Vm, console} from "forge-std/Test.sol";
import {GameBadgeNFT} from "../src/GameBadgeNFT.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";

/// @title Integration Test - Full Minting Flow
/// @notice Simulates the complete flow: deploy, mint multiple NFTs, verify metadata
contract IntegrationTest is Test {
    using Strings for uint256;

    GameBadgeNFT internal nft;

    address internal owner = address(0xA11CE);
    address internal minter = address(0xB0B);

    // Simulated user addresses
    address internal user1 = address(0xCAFE);
    address internal user2 = address(0xBEEF);
    address internal user3 = address(0xDEAD);

    string internal baseURI = "ipfs://bafybeiadgwost5sefktvwsohhjtybut4n7ni3xeta2bwvifuxuumqtx3t4/";

    function setUp() public {
        // Deploy contract
        nft = new GameBadgeNFT("GameBadge", "GBADGE", baseURI, owner, minter, 1);
        console.log("Contract deployed at:", address(nft));
        console.log("Owner:", owner);
        console.log("Minter:", minter);
        console.log("Base URI:", baseURI);
    }

    /// @notice Test full minting flow with multiple users
    function test_fullMintingFlow() public {
        console.log("\n=== Full Minting Flow Test ===\n");

        // Mint NFT for user1 (game ID 100)
        bytes32 claim1 = keccak256("user1-game100-claim");
        vm.prank(minter);
        nft.mintTo(user1, 100, claim1);

        uint256 token1 = 1;
        assertEq(nft.ownerOf(token1), user1);
        console.log("Token 1 minted to user1");
        console.log("  Token ID:", token1);
        console.log("  Index:", nft.tokenToIndex(token1));
        console.log("  URI:", nft.tokenURI(token1));

        // Mint NFT for user2 (game ID 200)
        bytes32 claim2 = keccak256("user2-game200-claim");
        vm.prank(minter);
        nft.mintTo(user2, 200, claim2);

        uint256 token2 = 2;
        assertEq(nft.ownerOf(token2), user2);
        console.log("\nToken 2 minted to user2");
        console.log("  Token ID:", token2);
        console.log("  Index:", nft.tokenToIndex(token2));
        console.log("  URI:", nft.tokenURI(token2));

        // Mint another NFT for user1 (different game ID 300)
        bytes32 claim3 = keccak256("user1-game300-claim");
        vm.prank(minter);
        nft.mintTo(user1, 300, claim3);

        uint256 token3 = 3;
        assertEq(nft.ownerOf(token3), user1);
        console.log("\nToken 3 minted to user1 (second badge)");
        console.log("  Token ID:", token3);
        console.log("  Index:", nft.tokenToIndex(token3));
        console.log("  URI:", nft.tokenURI(token3));

        // Verify nextTokenId
        assertEq(nft.nextTokenId(), 4);
        console.log("\nNext Token ID:", nft.nextTokenId());

        // Verify all indices are in range [1, 9]
        assertTrue(nft.tokenToIndex(token1) >= 1 && nft.tokenToIndex(token1) <= 9);
        assertTrue(nft.tokenToIndex(token2) >= 1 && nft.tokenToIndex(token2) <= 9);
        assertTrue(nft.tokenToIndex(token3) >= 1 && nft.tokenToIndex(token3) <= 9);
        console.log("\nAll indices verified in range [1, 9]");
    }

    /// @notice Test replay protection
    function test_replayProtection() public {
        console.log("\n=== Replay Protection Test ===\n");

        bytes32 claimId = keccak256("unique-claim-id");

        // First mint should succeed
        vm.prank(minter);
        nft.mintTo(user1, 100, claimId);
        console.log("First mint with claimId succeeded");

        // Second mint with same claimId should fail
        vm.prank(minter);
        vm.expectRevert(GameBadgeNFT.ClaimAlreadyUsed.selector);
        nft.mintTo(user2, 200, claimId);
        console.log("Second mint with same claimId correctly reverted");
    }

    /// @notice Test pause functionality
    function test_pauseFunctionality() public {
        console.log("\n=== Pause Functionality Test ===\n");

        // Owner pauses minting
        vm.prank(owner);
        nft.setPaused(true);
        assertTrue(nft.paused());
        console.log("Contract paused by owner");

        // Minting should fail when paused
        vm.prank(minter);
        vm.expectRevert(GameBadgeNFT.Paused.selector);
        nft.mintTo(user1, 100, keccak256("claim"));
        console.log("Minting correctly blocked when paused");

        // Owner unpauses
        vm.prank(owner);
        nft.setPaused(false);
        assertFalse(nft.paused());
        console.log("Contract unpaused by owner");

        // Minting should work again
        vm.prank(minter);
        nft.mintTo(user1, 100, keccak256("claim"));
        assertEq(nft.ownerOf(1), user1);
        console.log("Minting works after unpause");
    }

    /// @notice Test token transfer
    function test_tokenTransfer() public {
        console.log("\n=== Token Transfer Test ===\n");

        // Mint to user1
        vm.prank(minter);
        nft.mintTo(user1, 100, keccak256("claim"));
        assertEq(nft.ownerOf(1), user1);
        console.log("Token minted to user1");

        // User1 transfers to user2
        vm.prank(user1);
        nft.transferFrom(user1, user2, 1);
        assertEq(nft.ownerOf(1), user2);
        console.log("Token transferred from user1 to user2");

        // User2 transfers to user3
        vm.prank(user2);
        nft.transferFrom(user2, user3, 1);
        assertEq(nft.ownerOf(1), user3);
        console.log("Token transferred from user2 to user3");
    }

    /// @notice Test admin functions
    function test_adminFunctions() public {
        console.log("\n=== Admin Functions Test ===\n");

        // Change minter
        address newMinter = address(0x1234);
        vm.prank(owner);
        nft.setMinter(newMinter);
        assertEq(nft.minter(), newMinter);
        console.log("Minter changed to:", newMinter);

        // Old minter cannot mint
        vm.prank(minter);
        vm.expectRevert(GameBadgeNFT.NotMinter.selector);
        nft.mintTo(user1, 100, keccak256("claim"));
        console.log("Old minter correctly blocked");

        // New minter can mint
        vm.prank(newMinter);
        nft.mintTo(user1, 100, keccak256("claim"));
        assertEq(nft.ownerOf(1), user1);
        console.log("New minter can mint");

        // Change base URI
        string memory newURI = "ipfs://newCID/";
        vm.prank(owner);
        nft.setBaseURI(newURI);
        assertEq(nft.baseURI(), newURI);
        console.log("Base URI changed to:", newURI);

        // Verify tokenURI reflects new base
        string memory expectedURI = string.concat(newURI, uint256(nft.tokenToIndex(1)).toString(), ".json");
        assertEq(nft.tokenURI(1), expectedURI);
        console.log("Token URI updated:", nft.tokenURI(1));
    }

    /// @notice Test URI format
    function test_uriFormat() public {
        console.log("\n=== URI Format Test ===\n");

        // Mint token
        vm.prank(minter);
        nft.mintTo(user1, 100, keccak256("claim"));

        uint8 index = nft.tokenToIndex(1);
        string memory uri = nft.tokenURI(1);

        console.log("Token 1 Index:", index);
        console.log("Token 1 URI:", uri);

        // Expected format: baseURI + index + ".json"
        string memory expected = string.concat(baseURI, uint256(index).toString(), ".json");
        assertEq(uri, expected);
        console.log("URI format verified correctly");
    }
}
