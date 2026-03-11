import request from '@/utils/request'

export interface TestCase {
  id: number
  name: string
  description?: string
  yaml_content: string
  created_at: string
  updated_at?: string
}

export const getCases = (skip = 0, limit = 100) => {
  return request.get<any, TestCase[]>('/cases', { params: { skip, limit } })
}

export const createCase = (data: Partial<TestCase>) => {
  return request.post<any, TestCase>('/cases', data)
}

export const updateCase = (id: number, data: Partial<TestCase>) => {
  return request.put<any, TestCase>(`/cases/${id}`, data)
}

export const deleteCase = (id: number) => {
  return request.delete(`/cases/${id}`)
}

export const generateFromOpenAPI = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<{message: string}>('/generate/openapi', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}

export const generateFromHAR = (file: File) => {
  const formData = new FormData()
  formData.append('file', file)
  return request.post<{message: string}>('/generate/har', formData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  })
}
