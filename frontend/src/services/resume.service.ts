import type { ResumeExtractResult } from '@/types/resume'

export class ResumeService {
  private static pdfjs: typeof import('pdfjs-dist') | null = null

  private static async getPdfjs(): Promise<typeof import('pdfjs-dist')> {
    if (!this.pdfjs) {
      this.pdfjs = await import('pdfjs-dist')
      const workerSrc = new URL(
        'pdfjs-dist/build/pdf.worker.min.mjs',
        import.meta.url
      ).toString()
      this.pdfjs.GlobalWorkerOptions.workerSrc = workerSrc
    }
    return this.pdfjs
  }

  async extractFromPdf(file: File): Promise<ResumeExtractResult> {
    const arrayBuffer = await file.arrayBuffer()
    const pdfjs = await ResumeService.getPdfjs()
    const pdf = await pdfjs.getDocument({ data: arrayBuffer }).promise

    const textParts: string[] = []
    for (let i = 1; i <= pdf.numPages; i++) {
      const page = await pdf.getPage(i)
      const content = await page.getTextContent()
      const pageText = content.items
        .map((item) => ('str' in item ? (item as { str: string }).str : ''))
        .join(' ')
      textParts.push(pageText)
    }

    const rawText = textParts.join('\n\n').trim()
    const candidateId = this.extractCandidateId(rawText, file.name)

    return { rawText, candidateId }
  }

  private extractCandidateId(text: string, fileName: string): string {
    const idMatch = text.match(
      /(?:Candidate\s*ID|ID|CandidateId)\s*[:\-]?\s*(\S+)/i
    )
    if (idMatch) return idMatch[1]!.trim()

    const emailMatch = text.match(/[\w.-]+@[\w.-]+\.\w+/)
    if (emailMatch) return emailMatch[0]

    const cleanName = fileName
      .replace(/\.pdf$/i, '')
      .replace(/[^a-zA-Z0-9_-]/g, '_')
    return `candidate_${cleanName}`
  }

  validateFile(file: File): string | null {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
      return 'Only PDF files are accepted'
    }
    if (file.size > 10 * 1024 * 1024) {
      return 'File size must be under 10MB'
    }
    return null
  }
}
