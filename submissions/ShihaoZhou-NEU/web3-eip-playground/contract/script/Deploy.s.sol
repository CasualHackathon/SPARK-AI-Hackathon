// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Script} from "forge-std/Script.sol";
import {GameBadgeNFT} from "../src/GameBadgeNFT.sol";

/// @notice Deploy script for GameBadgeNFT.
/// Env vars (recommended):
/// - BASE_URI: e.g. ipfs://<METADATA_FOLDER_CID>/
/// - OWNER:    owner address (config admin)
/// - MINTER:   minter address (backend hot wallet)
/// - START_TOKEN_ID (optional): defaults to 1
contract Deploy is Script {
    function run() external returns (GameBadgeNFT deployed) {
        string memory baseURI = vm.envOr("BASE_URI", string("ipfs://<METADATA_FOLDER_CID>/"));
        address owner = vm.envAddress("OWNER");
        address minter = vm.envAddress("MINTER");

        uint256 startTokenId = 1;
        // Optional env var; if not set, vm.envOr will return default.
        startTokenId = vm.envOr("START_TOKEN_ID", startTokenId);

        vm.startBroadcast();
        deployed = new GameBadgeNFT("GameBadge", "GBADGE", baseURI, owner, minter, startTokenId);
        vm.stopBroadcast();
    }
}
