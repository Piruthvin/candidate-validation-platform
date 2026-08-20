/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_EXECUTOR_URL: string
  readonly VITE_API_BASE_URL: string
  readonly VITE_APP_ID: string
  readonly VITE_API_KEY: string
  readonly VITE_BEARER_TOKEN: string
  readonly VITE_USERNAME: string
  readonly VITE_STREAMING: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
