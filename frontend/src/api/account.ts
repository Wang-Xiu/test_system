import request from '@/utils/request'

export interface TestAccount {
  id: number
  project_id: number
  name: string
  username: string
  password?: string
  description?: string
  status: number
  created_at: string
  updated_at?: string
}

export const getAccounts = (skip = 0, limit = 100, project_id?: number) => {
  const params: any = { skip, limit }
  if (project_id !== undefined) params.project_id = project_id
  return request.get<any, TestAccount[]>('/accounts', { params })
}

export const createAccount = (data: Partial<TestAccount>) => {
  return request.post<any, TestAccount>('/accounts', data)
}

export const updateAccount = (id: number, data: Partial<TestAccount>) => {
  return request.put<any, TestAccount>(`/accounts/${id}`, data)
}

export const deleteAccount = (id: number) => {
  return request.delete(`/accounts/${id}`)
}
