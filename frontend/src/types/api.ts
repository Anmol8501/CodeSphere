/** Standard success envelope returned by every CodeArena API endpoint. */
export interface ApiResponse<T> {
  success: true
  message: string
  data: T
}

export interface ApiFieldError {
  field: string
  message: string
}

/** Standard error envelope. `errors` is present for validation (422) failures. */
export interface ApiErrorBody {
  success: false
  message: string
  errors?: ApiFieldError[]
}
