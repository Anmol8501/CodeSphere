import type { ApiResponse } from '../types/api'
import type { Draft, DraftSavePayload, DraftSaveResult, SupportedLanguage } from '../types/workspace'
import { api, unwrap } from './api'

/** The signed-in student's drafts. The backend scopes every call to the JWT user. */
export const draftService = {
  /** Resolves to null when nothing has been saved yet. */
  get(problemId: number, language: SupportedLanguage): Promise<Draft | null> {
    return unwrap(api.get<ApiResponse<Draft | null>>(`/problems/${problemId}/draft`, { params: { language } }))
  },

  save(problemId: number, payload: DraftSavePayload): Promise<DraftSaveResult> {
    return unwrap(api.put<ApiResponse<DraftSaveResult>>(`/problems/${problemId}/draft`, payload))
  },
}
