import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/api/client";

export function useDocuments() {
  const queryClient = useQueryClient();

  const documentsQuery = useQuery({
    queryKey: ["documents"],
    queryFn: api.getDocuments,
    staleTime: 30 * 1000, // 30 seconds
  });

  const uploadMutation = useMutation({
    mutationFn: api.uploadPDF,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  const clearMutation = useMutation({
    mutationFn: api.clearDocuments,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["documents"] });
    },
  });

  return {
    documents: documentsQuery.data?.documents ?? [],
    totalChars: documentsQuery.data?.total_chars ?? 0,
    isLoading: documentsQuery.isLoading,
    error: documentsQuery.error,
    uploadFile: uploadMutation.mutateAsync,
    isUploading: uploadMutation.isPending,
    uploadError: uploadMutation.error,
    clearDocuments: clearMutation.mutateAsync,
    isClearing: clearMutation.isPending,
  };
}
