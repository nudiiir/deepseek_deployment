<template>
  <div class="app">
    <h1>LLM Query Interface</h1>
    <textarea v-model="prompt" placeholder="Enter your prompt here..."></textarea>
    <button @click="sendQuery">Submit</button>
    <div v-if="response">
      <h2>Response:</h2>
      <p>{{ response }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';

const prompt = ref('');
const response = ref('');

async function sendQuery() {
  response.value = '';  // Clear previous responses
  try {
    const res = await fetch('http://localhost:8000/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt: prompt.value })
    });
  

    // Check if the response body is readable (streaming)
    if (!res.body) {
      throw new Error("ReadableStream not supported in this browser.");
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let text = '';

    // Read streamed data chunk by chunk and update the response live.
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      // Decode the incoming chunk and split into words
      text += decoder.decode(value, { stream: true });

      // Clean the text to remove unwanted tags and newlines
      text = text.replace(/<think>/g, '').replace(/<\/think>/g, '').replace(/\n+/g, ' ').trim();

      // Update the response dynamically
      response.value = text;
    }
  } catch (error) {
    console.error('Error:', error);
    response.value = 'Failed to get a response from the backend.';
  }
}
</script>

<style>
.app {
  max-width: 600px;
  margin: auto;
  padding: 20px;
  font-family: Arial, sans-serif;
  text-align: center;
}
textarea {
  width: 100%;
  height: 100px;
  margin: 10px 0;
  padding: 10px;
 font-size: 16px;
}
button {
  padding: 10px 20px;
  font-size: 16px;
  cursor: pointer;
}
h2 {
  margin-top: 20px;
  color: #333;
}
</style>
