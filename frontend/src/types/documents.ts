export interface DocumentInfo {
  filename: string;
  char_count: number;
}

export interface UploadResponse {
  success: boolean;
  document: DocumentInfo;
  message: string;
}

export interface DocumentListResponse {
  documents: DocumentInfo[];
  total_chars: number;
}

export interface DeleteDocumentsResponse {
  success: boolean;
  cleared: number;
}
