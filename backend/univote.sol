// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;
 
contract UniversityEVoting {
    struct Voter {
        bool isRegistered;
        bool hasVoted;
        address voterAddress;
    }
 
    struct Candidate {
        uint id;
        string name;
        uint voteCount;
    }
 
    address public admin;
    mapping(address => Voter) public voters;
    mapping(uint => Candidate) public candidates;
    uint public candidatesCount;
    bool public electionStarted;
    bool public electionEnded;
 
    event VoterRegistered(address indexed voter);
    event VoteCasted(address indexed voter, uint candidateId);
    event ElectionStarted();
    event ElectionEnded();
    event CandidateAdded(uint candidateId, string name);
 
    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }
 
    modifier onlyDuringElection() {
        require(electionStarted && !electionEnded, "Election is not active");
        _;
    }
 
    constructor() {
        admin = msg.sender;
    }
 
    function addCandidate(string memory _name) public onlyAdmin {
        candidatesCount++;
        candidates[candidatesCount] = Candidate(candidatesCount, _name, 0);
        emit CandidateAdded(candidatesCount, _name);
    }
 
    function registerVoter(address _voter) public onlyAdmin {
        require(!voters[_voter].isRegistered, "Voter is already registered");
        voters[_voter] = Voter(true, false, _voter);
        emit VoterRegistered(_voter);
    }
 
    function startElection() public onlyAdmin {
        require(!electionStarted, "Election already started");
        electionStarted = true;
        emit ElectionStarted();
    }
 
    function endElection() public onlyAdmin {
        require(electionStarted, "Election has not started");
        require(!electionEnded, "Election already ended");
        electionEnded = true;
        emit ElectionEnded();
    }
 
    function vote(uint _candidateId) public onlyDuringElection {
        require(voters[msg.sender].isRegistered, "You are not a registered voter");
        require(!voters[msg.sender].hasVoted, "You have already voted");
        require(candidates[_candidateId].id != 0, "Invalid candidate");
 
        voters[msg.sender].hasVoted = true;
        candidates[_candidateId].voteCount++;
 
        emit VoteCasted(msg.sender, _candidateId);
    }
 
    function getResults(uint _candidateId) public view returns (string memory, uint) {
    require(electionEnded, "Election must be ended to view results");
    require(_candidateId > 0 && _candidateId <= candidatesCount, "Invalid candidate ID");
    return (candidates[_candidateId].name, candidates[_candidateId].voteCount);
}
}