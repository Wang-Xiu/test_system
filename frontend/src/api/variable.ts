import request from '@/utils/request'

export interface Variable {
  id: number
  project_id?: number
  environment_id?: number
  key: string
  value: string
  var_type: string
  description?: string
  created_at: string
  updated_at?: string
}

export const getVariables = (params?: { project_id?: number; env_id?: number }) => {
  return request.get<any, Variable[]>('/variables', { params })
}

export const createVariable = (data: Partial<Variable>) => {
  return request.post<any, Variable>('/variables', data)
}

export const updateVariable = (id: number, data: Partial<Variable>) => {
  return request.put<any, Variable>(`/variables/${id}`, data)
}

export const deleteVariable = (id: number) => {
  return request.delete(`/variables/${id}`)
}

export const getResolvedVariables = (projectId: number, envId?: number) => {
  return request.get<any, Record<string, { value: string; var_type: string; source: string }>>(
    `/variables/resolved/${projectId}`,
    { params: envId ? { env_id: envId } : {} }
  )
}
