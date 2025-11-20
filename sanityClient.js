const path = require('path');
const dotenv = require('dotenv');

// Explicitly load .env from the project root
const envPath = path.join(__dirname, '.env');
dotenv.config({ path: envPath });

const { createClient } = require('@sanity/client');

// --- Sanity Configuration ---
// Ensure these variables are set in your .env file
const projectId = process.env.SANITY_PROJECT_ID;
const dataset = process.env.SANITY_DATASET || 'production';
// Support both variable names (User has SANITY_API_KEY in .env)
const token = process.env.SANITY_API_TOKEN || process.env.SANITY_API_KEY; 

if (!projectId || !token) {
  console.error("❌ Sanity Config Error: Missing SANITY_PROJECT_ID or SANITY_API_KEY in .env");
  // Return a mock client or null to prevent crash on startup
  module.exports = { 
    sanityClient: {
      create: async () => { throw new Error("Sanity not configured. Check .env"); }
    }
  };
} else {
  console.log(`Using Sanity Project: ${projectId} / Dataset: ${dataset}`);

  const client = createClient({
    projectId: projectId,
    dataset: dataset,
    useCdn: false, // We want real-time consistency for writes
    apiVersion: '2023-05-03',
    token: token, // Required for write operations
  });

  module.exports = { sanityClient: client };
}

