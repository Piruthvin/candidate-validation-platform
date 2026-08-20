export interface UploadedResume {
  file: File
  rawText: string
  candidateId: string
  fileName: string
  fileSize: number
}

export interface ResumeExtractResult {
  rawText: string
  candidateId: string
}
