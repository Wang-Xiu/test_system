import request from '@/utils/request'

export interface TestTask {
  id: number
  case_ids: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'error'
  celery_task_id?: string
  report_path?: string
  error_msg?: string
  created_at: string
  started_at?: string
  finished_at?: string
}

export const runTasks = (case_ids: number[]) => {
  return request.post<any, TestTask>('/tasks/run', { case_ids })
}

export const getTasks = (skip = 0, limit = 100) => {
  return request.get<any, TestTask[]>('/tasks', { params: { skip, limit } })
}
