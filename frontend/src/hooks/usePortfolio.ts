import { useQuery } from "@tanstack/react-query";
import { api } from "@/api/client";
import { usePortfolioContext } from "@/contexts/PortfolioContext";

export function usePortfolio() {
  const { selectedPortfolioId } = usePortfolioContext();

  return useQuery({
    queryKey: ["portfolio", selectedPortfolioId],
    queryFn: () => api.getPortfolio(selectedPortfolioId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}

export function useAssets() {
  const { selectedPortfolioId } = usePortfolioContext();

  return useQuery({
    queryKey: ["assets", selectedPortfolioId],
    queryFn: () => api.getAssets(selectedPortfolioId),
    staleTime: 5 * 60 * 1000,
  });
}
