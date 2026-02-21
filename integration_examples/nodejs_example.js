// Guardrail Integration Example - Node.js
const axios = require('axios');

const GUARDRAIL_URL = 'http://localhost:8000/intent';

async function checkInput(userText, role = 'general') {
  const response = await axios.post(GUARDRAIL_URL, {
    text: userText,
    role: role
  });
  return response.data;
}

// Example usage
(async () => {
  const result = await checkInput('Tell me about Node.js');
  
  if (result.decision === 'block') {
    console.log(`🔴 Blocked: ${result.reason}`);
  } else {
    console.log(`🟢 Safe: ${result.intent}`);
  }
})();
