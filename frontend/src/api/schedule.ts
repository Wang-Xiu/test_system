import request from '@/utils/request'

export interface Schedule {
  id: number
  project_id: number
  environment_id: number
  suite_id: number
  name: string
  cron_expression: string
  is_active: boolean
  last_run_at?: string
  created_at: string
  updated_at?: string
}

export const getSchedules = (project_id?: number) => {
  const params: any = {}
  if (project_id !== undefined) params.project_id = project_id
  return request.get<any, Schedule[]>('/schedules', { params })
}

export const createSchedule = (data: Partial<Schedule>) => {
  return request.post<any, Schedule>('/schedules', data)
}

export const updateSchedule = (id: number, data: Partial<Schedule>) => {
  return request.put<any, Schedule>(`/schedules/${id}`, data)
}

export const toggleSchedule = (id: number) => {
  return request.put<any, Schedule>(`/schedules/${id}/toggle`)
}

export const deleteSchedule = (id: number) => {
  return request.delete(`/schedules/${id}`)
}
