import request from '@/utils/request'

export interface TestTask {
  id: number
  case_ids?: string
  status: 'pending' | 'running' | 'success' | 'failed' | 'error'
  celery_task_id?: string
  report_path?: string
  error_msg?: string
  project_id?: number
  environment_id?: number
  suite_id?: number
  created_at: string
  started_at?: string
  finished_at?: string
}

export const runTasks = (case_ids: number[], project_id?: number, environment_id?: number, suite_id?: number) => {
  return request.post<any, TestTask>('/tasks/run', { case_ids, project_id, environment_id, suite_id })
}

export const getTasks = (skip = 0, limit = 100, project_id?: number) => {
  const params: any = { skip, limit }
  if (project_id !== undefined) params.project_id = project_id
  return request.get<any, TestTask[]>('/tasks', { params })
}
