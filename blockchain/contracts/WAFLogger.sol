// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/// @title WAFLogger
/// @notice Stores tamper-evident Merkle roots of batched WAF traffic logs.
/// Individual requests are NOT written on-chain (too slow/expensive) — the
/// backend batches N logs, hashes each, computes a Merkle root, and calls
/// logBatch() once per batch. Anyone holding a log entry + Merkle proof can
/// verify it belongs to a recorded batch without trusting the backend.
contract WAFLogger {
    struct Batch {
        bytes32 merkleRoot;
        uint256 logCount;
        uint256 timestamp;
        address submitter;
    }

    Batch[] public batches;

    event BatchLogged(
        uint256 indexed batchIndex,
        bytes32 merkleRoot,
        uint256 logCount,
        uint256 timestamp,
        address submitter
    );

    /// @notice Record a new batch's Merkle root.
    /// @param merkleRootHex hex string of the sha256 Merkle root (as bytes32)
    /// @param logCount number of individual log entries in this batch
    function logBatch(string calldata merkleRootHex, uint256 logCount) external {
        bytes32 root = _hexStringToBytes32(merkleRootHex);
        batches.push(
            Batch({
                merkleRoot: root,
                logCount: logCount,
                timestamp: block.timestamp,
                submitter: msg.sender
            })
        );
        emit BatchLogged(batches.length - 1, root, logCount, block.timestamp, msg.sender);
    }

    function batchCount() external view returns (uint256) {
        return batches.length;
    }

    function getBatch(uint256 index)
        external
        view
        returns (bytes32 merkleRoot, uint256 logCount, uint256 timestamp, address submitter)
    {
        Batch storage b = batches[index];
        return (b.merkleRoot, b.logCount, b.timestamp, b.submitter);
    }

    function _hexStringToBytes32(string memory source) internal pure returns (bytes32 result) {
        bytes memory tempEmptyStringTest = bytes(source);
        if (tempEmptyStringTest.length == 0) {
            return 0x0;
        }
        assembly {
            result := mload(add(source, 32))
        }
    }
}
