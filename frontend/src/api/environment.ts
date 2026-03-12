import request from '@/utils/request'

export interface Environment {
  id: number
  project_id: number
  name: string
  base_url?: string
  headers?: Record<string, string>
  auth_config?: Record<string, any>
  is_default: boolean
  created_at: string
  updated_at?: string
}

export const getEnvironments = (projectId: number) => {
  return request.get<any, Environment[]>(`/projects/${projectId}/envs`)
}

export const createEnvironment = (projectId: number, data: Partial<Environment>) => {
  return request.post<any, Environment>(`/projects/${projectId}/envs`, data)
}

export const updateEnvironment = (id: number, data: Partial<Environment>) => {
  return request.put<any, Environment>(`/envs/${id}`, data)
}

export const deleteEnvironment = (id: number) => {
  return request.delete(`/envs/${id}`)
}
