const { sanityClient } = require('./sanityClient');

async function verify() {
  try {
    console.log("Testing Sanity connection...");
    // Try to fetch a single document, or just check project info if possible.
    // fetching 0 documents is a safe read operation.
    const result = await sanityClient.fetch('*[_type == "analysisCard"][0]');
    console.log("✅ Sanity connection successful!");
    console.log("Connection Details:", sanityClient.config());
  } catch (error) {
    console.error("❌ Sanity connection failed:", error.message);
    process.exit(1);
  }
}

verify();

