const { sanityClient } = require('./sanityClient');

async function testSanity() {
    console.log("Testing Sanity Connection...");
    try {
        const query = '*[_type == "student"]{name, _id} | order(name asc)';
        const students = await sanityClient.fetch(query);
        console.log("✅ Success! Found students:", students.length);
        if (students.length > 0) {
            console.log("Sample:", students[0]);
        }
    } catch (error) {
        console.error("❌ Sanity Failed:", error.message);
    }
}

testSanity();