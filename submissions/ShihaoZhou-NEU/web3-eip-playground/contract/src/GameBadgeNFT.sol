// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {ERC721} from "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import {Ownable} from "@openzeppelin/contracts/access/Ownable.sol";
import {Strings} from "@openzeppelin/contracts/utils/Strings.sol";

/// @title GameBadgeNFT
/// @notice Project-minted, transferable ERC-721 with weak-randomized style index (1..9) fixed per token.
contract GameBadgeNFT is ERC721, Ownable {
    using Strings for uint256;

    // -------------------------
    // Constants / Config
    // -------------------------

    uint8 public constant POOL_SIZE = 9;

    // -------------------------
    // State
    // -------------------------

    /// @notice Next token id to mint.
    uint256 public nextTokenId;

    /// @notice Base URI prefix, e.g. "ipfs://<METADATA_FOLDER_CID>/" (recommended to include trailing slash).
    string public baseURI;

    /// @notice The only address allowed to mint (project backend hot wallet).
    address public minter;

    /// @notice Emergency pause for minting.
    bool public paused;

    /// @notice tokenId => style index (1..9).
    mapping(uint256 tokenId => uint8 index) public tokenToIndex;

    /// @notice Optional replay protection: claimId => used.
    mapping(bytes32 claimId => bool used) public claimUsed;

    // -------------------------
    // Events
    // -------------------------

    event Minted(
        address indexed to,
        uint256 indexed tokenId,
        uint8 index,
        uint256 indexed gameId,
        bytes32 claimId
    );

    // -------------------------
    // Errors
    // -------------------------

    error NotMinter();
    error Paused();
    error ZeroAddress();
    error ClaimAlreadyUsed();

    // -------------------------
    // Modifiers
    // -------------------------

    modifier onlyMinter() {
        if (msg.sender != minter) revert NotMinter();
        _;
    }

    // -------------------------
    // Constructor
    // -------------------------

    constructor(
        string memory name_,
        string memory symbol_,
        string memory baseURI_,
        address owner_,
        address minter_,
        uint256 startTokenId_
    ) ERC721(name_, symbol_) Ownable(owner_) {
        if (minter_ == address(0) || owner_ == address(0)) revert ZeroAddress();
        baseURI = baseURI_;
        minter = minter_;
        nextTokenId = startTokenId_;
    }

    // -------------------------
    // Mint
    // -------------------------

    /// @notice Mint a badge NFT to a user after game clear (project pays gas).
    /// @param to Recipient address (user wallet).
    /// @param gameId Business identifier for the game/campaign/level.
    /// @param claimId Backend-generated idempotency id (recommended unique).
    function mintTo(address to, uint256 gameId, bytes32 claimId) external onlyMinter {
        if (paused) revert Paused();
        if (to == address(0)) revert ZeroAddress();

        // On-chain replay protection (recommended; backend should also enforce idempotency).
        if (claimUsed[claimId]) revert ClaimAlreadyUsed();

        uint256 tokenId = nextTokenId;
        unchecked {
            nextTokenId = tokenId + 1;
        }

        uint8 index = _randomIndex(to, tokenId, gameId, claimId);
        tokenToIndex[tokenId] = index;
        claimUsed[claimId] = true;

        _safeMint(to, tokenId);

        emit Minted(to, tokenId, index, gameId, claimId);
    }

    // -------------------------
    // Metadata
    // -------------------------

    function tokenURI(uint256 tokenId) public view override returns (string memory) {
        // OZ v5: check existence via _ownerOf
        if (_ownerOf(tokenId) == address(0)) revert ERC721NonexistentToken(tokenId);

        uint256 index = uint256(tokenToIndex[tokenId]);
        return string.concat(baseURI, index.toString(), ".json");
    }

    // -------------------------
    // Admin
    // -------------------------

    function setBaseURI(string calldata newBaseURI) external onlyOwner {
        baseURI = newBaseURI;
    }

    function setMinter(address newMinter) external onlyOwner {
        if (newMinter == address(0)) revert ZeroAddress();
        minter = newMinter;
    }

    function setPaused(bool paused_) external onlyOwner {
        paused = paused_;
    }

    // -------------------------
    // Internal
    // -------------------------

    function _randomIndex(
        address to,
        uint256 tokenId,
        uint256 gameId,
        bytes32 claimId
    ) internal view returns (uint8) {
        bytes32 seed = keccak256(
            abi.encodePacked(block.prevrandao, block.timestamp, to, tokenId, gameId, claimId)
        );
        return uint8(uint256(seed) % POOL_SIZE) + 1;
    }
}

