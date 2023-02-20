// TODO how should this file be named?

export class ResponseError {
  message: string
  code: number
  constructor(message: string, code: number) {
    this.message = message
    this.code = code
  }
}
