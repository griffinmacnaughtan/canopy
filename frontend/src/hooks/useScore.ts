import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { usePortfolioContext } from "@/contexts/PortfolioContext";

export function useScore() {
  const { selectedPortfolioId } = usePortfolioContext();

  return useQuery({
    queryKey: ["score", selectedPortfolioId],
    queryFn: () => api.getScore(selectedPortfolioId),
    staleTime: 60 * 1000, // 1 minute
  });
}
