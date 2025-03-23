import { openDB } from "idb";

// Initialize the IndexedDB database
export async function initDB() {
  return openDB("ElectionDB", 1, {
    upgrade(db) {
      if (!db.objectStoreNames.contains("Voters")) {
        db.createObjectStore("Voters", { keyPath: "universityID" });
      }
      if (!db.objectStoreNames.contains("Candidates")) {
        db.createObjectStore("Candidates", { keyPath: "universityID" });
      }
    },
  });
}

// Add a new voter
export async function addVoter(voter: any) {
  const db = await initDB();
  return db.put("Voters", voter);
}

// Get a voter by university ID
export async function getVoter(universityID: string) {
  const db = await initDB();
  return db.get("Voters", universityID);
}

// Update voter record (e.g., mark as voted)
export async function updateVoter(universityID: string, updates: Partial<{ hasVoted: boolean }>) {
  const db = await initDB();
  const voter = await db.get("Voters", universityID);
  
  if (!voter) {
    throw new Error("Voter not found");
  }

  const updatedVoter = { ...voter, ...updates }; // Merge updates
  await db.put("Voters", updatedVoter);
}
// Add a new candidate
export async function addCandidate(candidate: any) {
  const db = await initDB();
  return db.put("Candidates", candidate);
}

export async function getCandidate(universityID: string) {
  try {
    const response = await fetch("http://127.0.0.1:8000/api/candidate/get_candidate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ universityID }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || "Failed to fetch candidate");
    }

    return await response.json(); // ✅ Ensure response is correctly parsed
  } catch (error) {
    console.error("API Error:", error);
    return { status: "error", message: (error as Error).message }; // ✅ Ensure 'message' is properly referenced
  }
}

// Get all candidates
export async function getAllCandidates() {
  try {
    const response = await fetch("http://127.0.0.1:8000/api/candidate/get_all_candidates");
    const data = await response.json();

    if (!response.ok || data.status !== "success") {
      throw new Error(data.message || "Failed to fetch candidates");
    }

    return data.candidates;  // ✅ Return candidates array directly
  } catch (error) {
    console.error("❌ Error fetching candidates:", error);
    return [];
  }
}


// Get all voters
export async function getAllVoters() {
  const db = await initDB();
  return db.getAll("Voters");
}
