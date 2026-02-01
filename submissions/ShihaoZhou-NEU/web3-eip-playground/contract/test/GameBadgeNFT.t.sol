// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test, Vm} from "forge-std/Test.sol";
import {GameBadgeNFT} from "../src/GameBadgeNFT.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";

contract GameBadgeNFTTest is Test {
    using Strings for uint256;

    GameBadgeNFT internal nft;

    address internal owner = address(0xA11CE);
    address internal minter = address(0xB0B);
    address internal user = address(0xCAFE);

    string internal baseURI = "ipfs://bafybeigdyr-exampleCID/";

    function setUp() public {
        nft = new GameBadgeNFT("GameBadge", "GBADGE", baseURI, owner, minter, 1);
    }

    function test_onlyMinter_canMint() public {
        vm.expectRevert(GameBadgeNFT.NotMinter.selector);
        nft.mintTo(user, 123, keccak256("claim-1"));
    }

    function test_paused_revertsMint() public {
        vm.prank(owner);
        nft.setPaused(true);

        vm.prank(minter);
        vm.expectRevert(GameBadgeNFT.Paused.selector);
        nft.mintTo(user, 123, keccak256("claim-1"));
    }

    function test_owner_adminFunctions() public {
        vm.prank(owner);
        nft.setMinter(address(0xD00D));
        assertEq(nft.minter(), address(0xD00D));

        vm.prank(owner);
        nft.setBaseURI("ipfs://newCID/");
        assertEq(nft.baseURI(), "ipfs://newCID/");

        vm.prank(owner);
        nft.setPaused(true);
        assertTrue(nft.paused());
    }

    function test_nonOwner_cannotAdmin() public {
        vm.expectRevert();
        nft.setMinter(address(0xD00D));

        vm.expectRevert();
        nft.setBaseURI("ipfs://newCID/");

        vm.expectRevert();
        nft.setPaused(true);
    }

    function test_mint_success_setsOwnerIndexUri_andEmitsEvent() public {
        bytes32 claimId = keccak256("claim-1");
        uint256 gameId = 999;

        // index is weak-random; we record logs and decode the Minted event to assert fields.
        vm.recordLogs();

        vm.prank(minter);
        nft.mintTo(user, gameId, claimId);

        Vm.Log[] memory entries = vm.getRecordedLogs();
        // Find Minted event among logs and decode.
        bytes32 sig = keccak256("Minted(address,uint256,uint8,uint256,bytes32)");
        bool found;
        uint256 tokenId;
        uint8 index;
        uint256 loggedGameId;
        bytes32 loggedClaimId;
        address to;

        for (uint256 i = 0; i < entries.length; i++) {
            if (entries[i].topics.length > 0 && entries[i].topics[0] == sig) {
                found = true;
                // indexed: to, tokenId, gameId
                to = address(uint160(uint256(entries[i].topics[1])));
                tokenId = uint256(entries[i].topics[2]);
                loggedGameId = uint256(entries[i].topics[3]);
                // data: index (uint8) + claimId (bytes32)
                (index, loggedClaimId) = abi.decode(entries[i].data, (uint8, bytes32));
                break;
            }
        }

        assertTrue(found);
        assertEq(to, user);
        assertEq(tokenId, 1);
        assertEq(loggedGameId, gameId);
        assertEq(loggedClaimId, claimId);

        assertEq(nft.ownerOf(1), user);

        uint256 storedIndex = uint256(nft.tokenToIndex(1));
        assertTrue(storedIndex >= 1 && storedIndex <= 9);
        assertEq(storedIndex, uint256(index));

        string memory expectedUri = string.concat(baseURI, storedIndex.toString(), ".json");
        assertEq(nft.tokenURI(1), expectedUri);
    }

    function test_claimId_replayProtection_reverts() public {
        bytes32 claimId = keccak256("claim-1");
        uint256 gameId = 1;

        vm.prank(minter);
        nft.mintTo(user, gameId, claimId);

        vm.prank(minter);
        vm.expectRevert(GameBadgeNFT.ClaimAlreadyUsed.selector);
        nft.mintTo(user, gameId, claimId);
    }

    function test_transferable_transferFrom_works() public {
        bytes32 claimId = keccak256("claim-1");

        vm.prank(minter);
        nft.mintTo(user, 1, claimId);

        address to = address(0xBEEF);

        vm.prank(user);
        nft.transferFrom(user, to, 1);

        assertEq(nft.ownerOf(1), to);
    }
}

