import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  envPrefix: ["VITE_", "PUBLIC_"],
  plugins: [sveltekit()],
  server: { port: 5173, host: true, allowedHosts: ["agentstalk.neoned71.com","agenttalk.neoned71.com",".neoned71.com"] },
  preview: { port: 5173, host: true, allowedHosts: ["agentstalk.neoned71.com","agenttalk.neoned71.com",".neoned71.com"] }
});
