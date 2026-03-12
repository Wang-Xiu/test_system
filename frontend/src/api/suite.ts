import request from '@/utils/request'

export interface TestSuite {
  id: number
  project_id: number
  name: string
  description?: string
  created_at: string
  updated_at?: string
}

export interface SuiteDetail extends TestSuite {
  cases: { id: number; name: string; order: number }[]
}

export const getSuites = (project_id?: number) => {
  const params: any = {}
  if (project_id !== undefined) params.project_id = project_id
  return request.get<any, TestSuite[]>('/suites', { params })
}

export const getSuite = (id: number) => {
  return request.get<any, SuiteDetail>(`/suites/${id}`)
}

export const createSuite = (data: { project_id: number; name: string; description?: string; case_ids: number[] }) => {
  return request.post<any, TestSuite>('/suites', data)
}

export const updateSuite = (id: number, data: { name?: string; description?: string; case_ids?: number[] }) => {
  return request.put<any, TestSuite>(`/suites/${id}`, data)
}

export const deleteSuite = (id: number) => {
  return request.delete(`/suites/${id}`)
}

export const runSuite = (id: number, env_id?: number) => {
  const params: any = {}
  if (env_id !== undefined) params.env_id = env_id
  return request.post<any, { task_id: number; message: string }>(`/suites/${id}/run`, null, { params })
}
