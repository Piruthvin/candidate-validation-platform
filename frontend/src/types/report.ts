export interface Report {
  id: string
  candidateName: string
  candidateId: string
  createdDate: string
  validationScore: number
  overallScore: number
  recommendation: string
  summary: string
}

export interface ReportFilters {
  search: string
  sortOrder: 'newest' | 'oldest'
  page: number
  pageSize: number
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  totalPages: number
}
