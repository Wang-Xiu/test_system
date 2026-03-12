import request from '@/utils/request'

export interface Project {
  id: number
  name: string
  description?: string
  base_url?: string
  webhook_secret?: string
  notification_config?: Record<string, any>
  created_at: string
  updated_at?: string
}

export const getProjects = (skip = 0, limit = 100) => {
  return request.get<any, Project[]>('/projects', { params: { skip, limit } })
}

export const getProject = (id: number) => {
  return request.get<any, Project>(`/projects/${id}`)
}

export const createProject = (data: Partial<Project>) => {
  return request.post<any, Project>('/projects', data)
}

export const updateProject = (id: number, data: Partial<Project>) => {
  return request.put<any, Project>(`/projects/${id}`, data)
}

export const deleteProject = (id: number) => {
  return request.delete(`/projects/${id}`)
}
